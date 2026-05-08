"""ATIF Trajectory → Scout Transcript conversion.

Maps Harbor's `Trajectory` (Pydantic model from `harbor.models.trajectories`)
to Scout's `Transcript` (a `TranscriptInfo` plus `messages` and `events`).

The mapping follows precedent from inspect_scout's other source converters:

* Steps with `source="user"` / `"system"` / `"agent"` map to
  `ChatMessageUser`, `ChatMessageSystem`, and `ChatMessageAssistant`.
* `Step.tool_calls[]` populate `ChatMessageAssistant.tool_calls`.
* `Step.observation.results[]` become `ChatMessageTool` rows correlated to
  the calling tool via `source_call_id` ↔ `tool_call_id`.
* `Step.reasoning_content` becomes a `ContentReasoning` part on the
  assistant message (matches `inspect_ai/_util/content.py`).
* `Step.metrics` synthesize a `ModelEvent` with sentinel `tools=[]`,
  `tool_choice="auto"`, and `config=GenerateConfig()` — matching the
  pattern used by Scout's logfire / langsmith / weave / phoenix sources.
  Synthesized events are marked via `output.metadata["atif_synthesized"]`.
* ATIF system steps with `extra.context_management` are emitted as
  `CompactionEvent` (the native inspect_ai construct) rather than
  `ChatMessageSystem`.
* `Step.is_copied_context=True` is preserved as a transcript-level
  `metadata["has_copied_context"]` flag.
"""

from datetime import datetime, timezone
from logging import getLogger
from typing import Any

from harbor.models.trajectories import (
    ContentPart,
    Step,
    Trajectory,
)
from inspect_ai._util.content import (
    Content,
    ContentImage,
    ContentReasoning,
    ContentText,
)
from inspect_ai.event import CompactionEvent, Event, ModelEvent
from inspect_ai.model import (
    ChatMessage,
    ChatMessageAssistant,
    ChatMessageSystem,
    ChatMessageTool,
    ChatMessageUser,
    GenerateConfig,
    ModelOutput,
    ModelUsage,
)
from inspect_ai.model._model_output import ChatCompletionChoice
from inspect_ai.tool import ToolCall
from inspect_scout import Transcript

logger = getLogger(__name__)

ATIF_SOURCE_TYPE = "atif"
"""Value populated into `Transcript.source_type` for ATIF-derived rows."""


def trajectory_to_transcript(
    trajectory: Trajectory,
    source_uri: str | None = None,
) -> Transcript:
    """Convert a Harbor `Trajectory` to a Scout `Transcript`.

    Args:
        trajectory: A validated ATIF Trajectory.
        source_uri: Optional URI pointing to the trajectory's on-disk
            location (e.g. file path), preserved on `Transcript.source_uri`.

    Returns:
        Scout Transcript suitable for inserting into a transcript database.
    """
    # Pre-scan tool_calls so observations can resolve `function` from
    # `source_call_id` regardless of whether the calling step came earlier
    # in the same trajectory or in a continuation.
    tool_call_funcs: dict[str, str] = {}
    for step in trajectory.steps:
        if step.tool_calls:
            for tc in step.tool_calls:
                tool_call_funcs[tc.tool_call_id] = tc.function_name

    messages: list[ChatMessage] = []
    events: list[Event] = []
    has_copied_context = False

    for step in trajectory.steps:
        if step.is_copied_context:
            has_copied_context = True

        # Compaction step → emit CompactionEvent in lieu of a system message.
        if (
            step.source == "system"
            and step.extra
            and "context_management" in step.extra
        ):
            events.append(_compaction_event_for_step(step))
            continue

        new_msgs = _step_to_messages(step, tool_call_funcs)

        # Synthesize a ModelEvent BEFORE adding the assistant message to
        # the running history, so `event.input` reflects what the model
        # actually saw.
        if step.source == "agent" and step.metrics is not None:
            ev = _synthesize_model_event(
                step,
                prior_messages=messages,
                new_messages=new_msgs,
            )
            if ev is not None:
                events.append(ev)

        messages.extend(new_msgs)

    metadata: dict[str, Any] = {
        "schema_version": trajectory.schema_version,
    }
    if trajectory.continued_trajectory_ref:
        metadata["continued_trajectory_ref"] = trajectory.continued_trajectory_ref
    if has_copied_context:
        metadata["has_copied_context"] = True
    if trajectory.notes:
        metadata["notes"] = trajectory.notes

    total_tokens: int | None = None
    if trajectory.final_metrics is not None:
        prompt = trajectory.final_metrics.total_prompt_tokens or 0
        completion = trajectory.final_metrics.total_completion_tokens or 0
        total = prompt + completion
        total_tokens = total if total > 0 else None

    return Transcript(
        transcript_id=trajectory.session_id,
        source_type=ATIF_SOURCE_TYPE,
        source_id=trajectory.session_id,
        source_uri=source_uri,
        agent=trajectory.agent.name,
        model=trajectory.agent.model_name,
        message_count=len(messages),
        total_tokens=total_tokens,
        messages=messages,
        events=events,
        metadata=metadata,
    )


def _step_to_messages(
    step: Step,
    tool_call_funcs: dict[str, str],
) -> list[ChatMessage]:
    """Convert one ATIF step to a list of ChatMessages.

    A single step can yield multiple messages: the step's own message
    (system/user/assistant) plus one `ChatMessageTool` per
    `observation.results[]` entry.
    """
    msgs: list[ChatMessage] = []
    content = _atif_to_inspect_content(step.message, step.reasoning_content)

    if step.source == "system":
        msgs.append(ChatMessageSystem(content=content))
    elif step.source == "user":
        msgs.append(ChatMessageUser(content=content))
    elif step.source == "agent":
        tool_calls: list[ToolCall] | None = None
        if step.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.tool_call_id,
                    function=tc.function_name,
                    arguments=tc.arguments,
                )
                for tc in step.tool_calls
            ]
        msgs.append(
            ChatMessageAssistant(
                content=content,
                tool_calls=tool_calls,
                model=step.model_name,
            )
        )

    if step.observation is not None:
        for result in step.observation.results:
            tool_call_id = result.source_call_id or ""
            function = tool_call_funcs.get(tool_call_id, "unknown")
            msgs.append(
                ChatMessageTool(
                    tool_call_id=tool_call_id,
                    function=function,
                    content=_atif_to_inspect_content(result.content),
                )
            )

    return msgs


def _atif_to_inspect_content(
    message: str | list[ContentPart] | None,
    reasoning: str | None = None,
) -> str | list[Content]:
    """Convert ATIF message content to inspect_ai content.

    `reasoning` is optional and, when present, prepended as a
    `ContentReasoning` part — forces a multipart return.
    """
    parts: list[Content] = []

    if reasoning:
        parts.append(ContentReasoning(reasoning=reasoning))

    if isinstance(message, str):
        if not parts:
            return message
        parts.append(ContentText(text=message))
    elif isinstance(message, list):
        for cp in message:
            if cp.type == "text" and cp.text is not None:
                parts.append(ContentText(text=cp.text))
            elif cp.type == "image" and cp.source is not None:
                # Phase 3 ships path-as-string. Resolving relative paths to
                # data URIs is a follow-up — Scout's `ContentImage.image`
                # accepts either a URL or base64 data URI.
                parts.append(ContentImage(image=cp.source.path))
            else:
                logger.warning("Unrecognized ATIF ContentPart: type=%r", cp.type)
    elif message is None:
        # No content (e.g., observation result with only subagent_trajectory_ref)
        pass

    return parts if parts else ""


def _synthesize_model_event(
    step: Step,
    prior_messages: list[ChatMessage],
    new_messages: list[ChatMessage],
) -> ModelEvent | None:
    """Build a `ModelEvent` from ATIF step metrics.

    Sentinel values fill in fields ATIF doesn't carry (`tools=[]`,
    `tool_choice="auto"`, `config=GenerateConfig()`). Returns None when the
    step has `llm_call_count == 0` (deterministic dispatch — no real LLM
    call to model).
    """
    if step.metrics is None:
        return None

    # ATIF v1.6+ has llm_call_count to mark deterministic-dispatch steps.
    # When present and zero, skip event synthesis entirely.
    llm_call_count = getattr(step, "llm_call_count", None)
    if llm_call_count == 0:
        return None

    assistant_msg = next(
        (m for m in new_messages if isinstance(m, ChatMessageAssistant)),
        None,
    )
    if assistant_msg is None:
        return None

    prompt_tokens = step.metrics.prompt_tokens or 0
    completion_tokens = step.metrics.completion_tokens or 0
    usage = ModelUsage(
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        input_tokens_cache_read=step.metrics.cached_tokens,
        total_cost=step.metrics.cost_usd,
    )

    model_name = step.model_name or "unknown"
    timestamp = _parse_timestamp(step.timestamp) or _utcnow()

    output = ModelOutput(
        model=model_name,
        choices=[ChatCompletionChoice(message=assistant_msg)],
        usage=usage,
        metadata={"atif_synthesized": True},
    )

    return ModelEvent(
        model=model_name,
        input=list(prior_messages),
        tools=[],
        tool_choice="auto",
        config=GenerateConfig(),
        output=output,
        timestamp=timestamp,
    )


def _compaction_event_for_step(step: Step) -> CompactionEvent:
    """Build a `CompactionEvent` for a context-management ATIF step.

    Triggered when an ATIF system step carries `extra.context_management`.
    Token-before/after counts and the compaction `type` are pulled from
    that extra dict when present (ATIF system steps cannot carry top-level
    `metrics`).
    """
    cm: dict[str, Any] = (
        (step.extra or {}).get("context_management") or {} if step.extra else {}
    )
    if not isinstance(cm, dict):
        cm = {}

    cm_type = cm.get("type")
    compaction_type = cm_type if cm_type in ("summary", "edit", "trim") else "summary"

    tokens_before = cm.get("tokens_before")
    tokens_after = cm.get("tokens_after")

    timestamp = _parse_timestamp(step.timestamp) or _utcnow()
    return CompactionEvent(
        type=compaction_type,
        tokens_before=tokens_before if isinstance(tokens_before, int) else None,
        tokens_after=tokens_after if isinstance(tokens_after, int) else None,
        source="atif",
        timestamp=timestamp,
    )


def _parse_timestamp(value: str | None) -> datetime | None:
    """Parse an ISO 8601 timestamp string to a tz-aware UTC datetime."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        logger.warning("Invalid ATIF timestamp: %r", value)
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
