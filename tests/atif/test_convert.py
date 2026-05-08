"""Tests for ATIF Trajectory → Scout Transcript conversion.

Combines two strategies:

* Programmatic fixtures via `harbor.models.trajectories.*` Pydantic models
  for targeted assertions on specific spec features (compaction,
  is_copied_context, reasoning, tool-call correlation).
* JSON fixtures pulled from harbor's golden tests for full end-to-end
  validation that real Harbor output round-trips through our converter.
"""

from pathlib import Path

import pytest
from harbor.models.trajectories import (
    Agent,
    ContentPart,
    Metrics,
    Observation,
    ObservationResult,
    Step,
    ToolCall,
    Trajectory,
)
from inspect_ai._util.content import ContentImage, ContentReasoning, ContentText
from inspect_ai.event import CompactionEvent, ModelEvent
from inspect_ai.model import (
    ChatMessageAssistant,
    ChatMessageSystem,
    ChatMessageTool,
    ChatMessageUser,
)
from inspect_harbor._atif.convert import (
    ATIF_SOURCE_TYPE,
    trajectory_to_transcript,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _agent(model_name: str | None = None) -> Agent:
    return Agent(name="test-agent", version="0.1.0", model_name=model_name)


def _mk_trajectory(steps: list[Step], **kwargs: object) -> Trajectory:
    return Trajectory(
        session_id="test-session",
        agent=_agent(),
        steps=steps,
        **kwargs,  # type: ignore[arg-type]
    )


# ---------- Programmatic fixtures: targeted assertions ----------


def test_user_step_yields_chat_message_user() -> None:
    """A `user`-source step becomes a `ChatMessageUser`."""
    traj = _mk_trajectory([Step(step_id=1, source="user", message="hello")])

    transcript = trajectory_to_transcript(traj)

    assert len(transcript.messages) == 1
    msg = transcript.messages[0]
    assert isinstance(msg, ChatMessageUser)
    assert msg.content == "hello"


def test_system_step_yields_chat_message_system() -> None:
    """A `system`-source step becomes a `ChatMessageSystem`."""
    traj = _mk_trajectory([Step(step_id=1, source="system", message="you are a bot")])

    transcript = trajectory_to_transcript(traj)

    assert isinstance(transcript.messages[0], ChatMessageSystem)
    assert transcript.messages[0].content == "you are a bot"


def test_agent_step_yields_chat_message_assistant() -> None:
    """An `agent`-source step becomes a `ChatMessageAssistant` with `model`."""
    traj = _mk_trajectory(
        [Step(step_id=1, source="agent", message="ok!", model_name="gpt-4")]
    )

    msg = trajectory_to_transcript(traj).messages[0]

    assert isinstance(msg, ChatMessageAssistant)
    assert msg.content == "ok!"
    assert msg.model == "gpt-4"


def test_reasoning_content_becomes_content_reasoning_part() -> None:
    """`reasoning_content` is prepended as a `ContentReasoning` part."""
    traj = _mk_trajectory(
        [
            Step(
                step_id=1,
                source="agent",
                message="final answer: 42",
                reasoning_content="thinking step by step...",
            )
        ]
    )

    msg = trajectory_to_transcript(traj).messages[0]

    assert isinstance(msg, ChatMessageAssistant)
    assert isinstance(msg.content, list)
    assert isinstance(msg.content[0], ContentReasoning)
    assert msg.content[0].reasoning == "thinking step by step..."
    assert isinstance(msg.content[1], ContentText)
    assert msg.content[1].text == "final answer: 42"


def test_tool_call_and_observation_correlate_via_source_call_id() -> None:
    """`ChatMessageTool.tool_call_id` matches the ATIF `source_call_id`."""
    traj = _mk_trajectory(
        [
            Step(
                step_id=1,
                source="agent",
                message="running it",
                tool_calls=[
                    ToolCall(
                        tool_call_id="call_42",
                        function_name="run_code",
                        arguments={"code": "1 + 1"},
                    )
                ],
                observation=Observation(
                    results=[ObservationResult(source_call_id="call_42", content="2")]
                ),
            )
        ]
    )

    transcript = trajectory_to_transcript(traj)
    assistant, tool = transcript.messages

    assert isinstance(assistant, ChatMessageAssistant)
    assert assistant.tool_calls is not None
    assert assistant.tool_calls[0].id == "call_42"
    assert assistant.tool_calls[0].function == "run_code"

    assert isinstance(tool, ChatMessageTool)
    assert tool.tool_call_id == "call_42"
    assert tool.function == "run_code"
    assert tool.content == "2"


def test_metrics_synthesize_model_event() -> None:
    """A `ModelEvent` is synthesized from `Step.metrics` with sentinel fields."""
    traj = _mk_trajectory(
        [
            Step(
                step_id=1,
                source="agent",
                message="done",
                model_name="gpt-4",
                metrics=Metrics(
                    prompt_tokens=100, completion_tokens=20, cost_usd=0.001
                ),
            )
        ]
    )

    events = trajectory_to_transcript(traj).events

    assert len(events) == 1
    ev = events[0]
    assert isinstance(ev, ModelEvent)
    assert ev.model == "gpt-4"
    assert ev.tools == []
    assert ev.tool_choice == "auto"
    assert ev.output.usage is not None
    assert ev.output.usage.input_tokens == 100
    assert ev.output.usage.output_tokens == 20
    assert ev.output.usage.total_tokens == 120
    assert ev.output.metadata == {"atif_synthesized": True}


def test_no_metrics_means_no_model_event() -> None:
    """No `Step.metrics` → no `ModelEvent` is emitted."""
    traj = _mk_trajectory([Step(step_id=1, source="agent", message="hi")])
    assert trajectory_to_transcript(traj).events == []


def test_context_management_step_emits_compaction_event() -> None:
    """A system step with `extra.context_management` becomes `CompactionEvent`."""
    traj = _mk_trajectory(
        [
            Step(
                step_id=1,
                source="system",
                message="(compacted)",
                extra={
                    "context_management": {
                        "type": "summary",
                        "tokens_before": 5000,
                        "tokens_after": 1000,
                    }
                },
            )
        ]
    )

    transcript = trajectory_to_transcript(traj)

    # The system message is replaced by a CompactionEvent.
    assert transcript.messages == []
    assert len(transcript.events) == 1
    ev = transcript.events[0]
    assert isinstance(ev, CompactionEvent)
    assert ev.source == "atif"
    assert ev.tokens_before == 5000
    assert ev.tokens_after == 1000


def test_is_copied_context_sets_transcript_metadata_flag() -> None:
    """Any `Step.is_copied_context=True` sets transcript-level `has_copied_context`."""
    traj = _mk_trajectory(
        [
            Step(step_id=1, source="user", message="hi"),
            Step(
                step_id=2,
                source="agent",
                message="from another run",
                is_copied_context=True,
            ),
        ]
    )

    transcript = trajectory_to_transcript(traj)

    assert transcript.metadata["has_copied_context"] is True


def test_continued_trajectory_ref_preserved_in_metadata() -> None:
    """`Trajectory.continued_trajectory_ref` is preserved in transcript metadata."""
    traj = _mk_trajectory(
        [Step(step_id=1, source="user", message="hi")],
        continued_trajectory_ref="next.json",
    )
    transcript = trajectory_to_transcript(traj)
    assert transcript.metadata["continued_trajectory_ref"] == "next.json"


def test_image_content_part_becomes_content_image() -> None:
    """ATIF `ContentPart` with `type='image'` becomes inspect_ai `ContentImage`."""
    from harbor.models.trajectories.content import ImageSource

    traj = _mk_trajectory(
        [
            Step(
                step_id=1,
                source="user",
                message=[
                    ContentPart(type="text", text="see this:"),
                    ContentPart(
                        type="image",
                        source=ImageSource(
                            media_type="image/png", path="images/cat.png"
                        ),
                    ),
                ],
            )
        ]
    )

    msg = trajectory_to_transcript(traj).messages[0]
    assert isinstance(msg.content, list)
    assert isinstance(msg.content[0], ContentText)
    assert isinstance(msg.content[1], ContentImage)
    assert msg.content[1].image == "images/cat.png"


def test_transcript_top_level_fields() -> None:
    """Identifying fields (id, source_type, agent, source_uri) are populated."""
    traj = _mk_trajectory(
        [Step(step_id=1, source="user", message="hi")],
    )
    transcript = trajectory_to_transcript(traj, source_uri="/path/to/t.json")

    assert transcript.transcript_id == "test-session"
    assert transcript.source_type == ATIF_SOURCE_TYPE
    assert transcript.source_id == "test-session"
    assert transcript.source_uri == "/path/to/t.json"
    assert transcript.agent == "test-agent"
    assert transcript.message_count == 1
    assert transcript.metadata["schema_version"].startswith("ATIF-")


# ---------- Real fixtures from harbor's golden tests ----------


@pytest.mark.parametrize(
    "fixture_name,expected_messages,expected_model_events",
    [
        ("openhands_hello-world.trajectory.json", 7, 2),
        ("openhands_hello-world.trajectory.no_function_calling.json", 5, 2),
    ],
)
def test_golden_fixture_round_trips(
    fixture_name: str,
    expected_messages: int,
    expected_model_events: int,
) -> None:
    """Real Harbor golden fixtures convert without error and yield expected counts."""
    raw = (FIXTURES / fixture_name).read_text()
    traj = Trajectory.model_validate_json(raw)

    transcript = trajectory_to_transcript(traj, source_uri=fixture_name)

    assert transcript.source_type == ATIF_SOURCE_TYPE
    assert len(transcript.messages) == expected_messages
    assert (
        sum(1 for e in transcript.events if isinstance(e, ModelEvent))
        == expected_model_events
    )
