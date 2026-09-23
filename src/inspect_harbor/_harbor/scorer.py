"""Scorer for Harbor tasks in Inspect AI."""

import json
import logging
import math
import shlex
import warnings
from pathlib import Path
from typing import Any

from inspect_ai.scorer import Score, Scorer, Target, accuracy, scorer, stderr
from inspect_ai.solver import TaskState
from inspect_ai.util import sandbox

from inspect_harbor._harbor.converters import _user_to_str
from inspect_harbor._harbor.models import MAIN_SERVICE_NAME, TaskConfig
from inspect_harbor._harbor.paths import EnvironmentPaths
from inspect_harbor._harbor.sandbox_utils import (
    cleanup_sandbox_directories,
    cleanup_sandbox_env_vars,
    copy_directory_to_sandbox,
    resolve_env_vars,
)

logger = logging.getLogger(__name__)

# ``TEST_DIR`` is a Terminal-Bench convention some verifier scripts rely on.
_DEFAULT_VERIFIER_ENV: dict[str, str] = {
    "TEST_DIR": str(EnvironmentPaths().tests_dir),
}


class CopyTestsDirError(Exception):
    """Raised when failing to copy the tests directory to the sandbox."""


class VerifierOutputParseError(Exception):
    """Raised when parsing rewards from output files (text or JSON) fails."""


class RewardFileNotFoundError(FileNotFoundError):
    """Raised when neither a text nor JSON reward file exists at expected locations."""


class RewardFileEmptyError(Exception):
    """Raised when a reward file exists but contains no data."""


@scorer(metrics=[accuracy(), stderr()])
def harbor_scorer(
    default_verifier_timeout_sec: int = 600,
) -> Scorer:
    """Scorer for Harbor tasks.

    Copies test files to the sandbox at scoring time (after agent submission),
    runs the test script, reads the reward file to determine the score, and
    cleans up scoring files to ensure a clean state for subsequent attempts.

    Args:
        default_verifier_timeout_sec: Default timeout if not in metadata. Defaults to 600s.

    Returns:
        Scorer that copies tests, runs them, returns the score, and cleans up.
    """

    async def score(state: TaskState, target: Target) -> Score:  # noqa: ARG001
        tests_dir = state.metadata.get("tests_dir")
        test_path = state.metadata.get("test_path")

        if not tests_dir:
            raise CopyTestsDirError("tests_dir not found in metadata")
        if not test_path:
            raise CopyTestsDirError("test_path not found in metadata")

        tests_dir = Path(tests_dir)
        test_path = Path(test_path)
        verifier_timeout_sec = state.metadata.get(
            "verifier_timeout_sec", default_verifier_timeout_sec
        )

        if not tests_dir.exists():
            raise CopyTestsDirError(f"Tests directory not found: {tests_dir}")

        try:
            await copy_directory_to_sandbox(tests_dir, "/tests")
        except Exception as e:
            raise CopyTestsDirError(f"Failed to copy tests to sandbox: {e}") from e

        try:
            relative_test_path = test_path.relative_to(tests_dir)
            container_test_path = f"/tests/{relative_test_path}".replace("\\", "/")
        except ValueError as e:
            raise CopyTestsDirError(
                f"Test path {test_path} is not relative to tests directory {tests_dir}"
            ) from e

        # Create Harbor's standard log directories. Harbor bind-mounts
        # /logs/artifacts and chmods it world-writable so collect hooks running
        # as a non-root user can write there; mirror that here.
        await sandbox().exec(["mkdir", "-p", "/logs/agent"])
        await sandbox().exec(["mkdir", "-p", "/logs/verifier"])
        await sandbox().exec(
            ["sh", "-c", "mkdir -p /logs/artifacts && chmod 0777 /logs/artifacts"]
        )

        # Run [[verifier.collect]] hooks to gather artifacts (e.g. model.patch)
        harbor_config = state.metadata.get("harbor_config")
        if harbor_config:
            await _run_verifier_collect(harbor_config)

        verifier_env_raw = state.metadata.get("verifier_env", {})
        resolved_user_env = (
            resolve_env_vars(verifier_env_raw) if verifier_env_raw else {}
        )
        verifier_env = {**_DEFAULT_VERIFIER_ENV, **resolved_user_env}
        verifier_user = state.metadata.get("verifier_user")

        # Exec the script directly, as Harbor's verifier does, so its shebang
        # picks the interpreter. Harbor chmods as root; we only switch user when
        # the task sets [verifier].user, because on some Inspect sandbox
        # providers a user switch needs sudo or su in the image, and a task
        # without a verifier user never needed either. A script that still is
        # not executable runs under bash, as it always did here.
        script = shlex.quote(container_test_path)
        run = f"if [ -x {script} ]; then {script}; else bash {script}; fi"
        if verifier_user is None:
            command = f"chmod +x {script} 2>/dev/null; {run}"
        else:
            await sandbox().exec(["chmod", "+x", container_test_path], user="root")
            command = run
        result = await sandbox().exec(
            ["sh", "-c", command],
            timeout=int(verifier_timeout_sec),
            env=verifier_env,
            user=verifier_user,
        )

        reward_value, reward_dict = await _parse_reward_file(result.returncode)
        passed = reward_value > 0

        score_result = Score(
            value=reward_value,
            answer="PASS" if passed else "FAIL",
            explanation=(
                f"Test exit code: {result.returncode}\n\n"
                f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
            ),
            metadata={"reward_dict": reward_dict} if reward_dict else None,
        )

        await cleanup_sandbox_directories("/tests", "/logs/verifier", "/logs/artifacts")
        await cleanup_sandbox_env_vars(list(verifier_env.keys()))

        return score_result

    return score


async def _run_verifier_collect(harbor_config: dict[str, Any]) -> None:
    """Run ``[[verifier.collect]]`` hooks, then reset the repo in separate mode.

    Mirrors Harbor: hooks run in the main service after the agent phase and are
    best-effort (failures are logged, scoring continues). In ``separate``
    verifier mode Harbor then verifies in a fresh container at the base commit;
    everything here shares the agent's container, so we approximate that with
    ``git checkout -f <base_commit_hash> && git clean -fd``. Without it, graders
    such as DeepSWE's fail to apply ``model.patch`` over files the agent created.
    Limits: build-time edits to tracked files survive only if the agent committed
    them, and a multi-attempt solver sees the reset tree on its next attempt.
    """
    try:
        # The config already warned about unknown keys when the task loaded;
        # don't repeat that for every sample scored.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            task_cfg = TaskConfig.model_validate(harbor_config)
    except ValueError as exc:  # pydantic.ValidationError
        logger.warning(
            "Skipping verifier.collect hooks: harbor_config failed validation: %s",
            exc,
        )
        return

    # None -> the container's WORKDIR, matching Harbor's exec default.
    workdir = task_cfg.environment.workdir

    for step in task_cfg.verifier.collect:
        # ``sandbox()`` only addresses the default (main) compose service, so
        # hooks targeting a sidecar can't be honored here.
        if step.service != MAIN_SERVICE_NAME:
            logger.warning(
                "Skipping verifier.collect hook targeting non-main service %r: %r",
                step.service,
                step.command,
            )
            continue

        # Harbor runs collect hooks as ``hook.user`` (falling back to the
        # container's default user), not the agent user.
        try:
            result = await sandbox().exec(
                ["bash", "-c", step.command],
                timeout=int(step.timeout_sec),
                user=_user_to_str(step.user),
                cwd=workdir,
            )
        except Exception as exc:
            # e.g. TimeoutError raised by the sandbox when the hook overruns
            logger.warning(
                "verifier.collect hook failed to run (%s): %r", exc, step.command
            )
            continue
        if result.returncode != 0:
            logger.warning(
                "verifier.collect hook exited %d: %r\nstdout:\n%s\nstderr:\n%s",
                result.returncode,
                step.command,
                result.stdout,
                result.stderr,
            )

    # Only reset in separate mode; in shared mode Harbor verifies against the
    # agent's environment, so wiping its work would grade the pristine base.
    if not task_cfg.verifier_runs_separately():
        return

    base_commit = task_cfg.metadata.get("base_commit_hash")
    if not base_commit:
        return

    # The agent may have committed as a non-root user, so mark the repo safe to
    # avoid git's "dubious ownership" error when resetting as the default user.
    reset_cmd = (
        f"cd {shlex.quote(workdir or '/app')} && "
        "git config --global --add safe.directory '*' && "
        f"git checkout -f {shlex.quote(str(base_commit))} && git clean -fd"
    )
    try:
        result = await sandbox().exec(["bash", "-c", reset_cmd], timeout=60)
    except Exception as exc:
        logger.warning(
            "repo reset to base commit %r failed to run: %s", base_commit, exc
        )
        return
    if result.returncode != 0:
        logger.warning(
            "repo reset to base commit %r exited %d\nstdout:\n%s\nstderr:\n%s",
            base_commit,
            result.returncode,
            result.stdout,
            result.stderr,
        )


async def _parse_reward_file(exit_code: int) -> tuple[float, dict[str, Any] | None]:
    """Parse the reward from ``reward.json`` or, failing that, ``reward.txt``.

    Like Harbor, ``reward.json`` takes precedence when both exist.

    Args:
        exit_code: Test script exit code, for the not-found message.

    Returns:
        Tuple of (reward value as float, reward dict if from JSON else None).

    Raises:
        RewardFileEmptyError: When a reward file exists but is empty.
        VerifierOutputParseError: When a reward file cannot be parsed, or holds
            a non-numeric or non-finite value.
        RewardFileNotFoundError: When neither reward file exists.
    """
    reward_text_path = str(EnvironmentPaths().reward_text_path)
    reward_json_path = str(EnvironmentPaths().reward_json_path)

    try:
        reward_json_content = await sandbox().read_file(reward_json_path)
    except FileNotFoundError:
        reward_json_content = None
    if reward_json_content is not None:
        if not reward_json_content.strip():
            raise RewardFileEmptyError(f"Reward file is empty: {reward_json_path}")
        try:
            reward_dict = json.loads(reward_json_content)
        except json.JSONDecodeError as e:
            raise VerifierOutputParseError(
                f"Failed to parse reward.json: {reward_json_content[:100]}"
            ) from e
        if not isinstance(reward_dict, dict) or not reward_dict:
            raise VerifierOutputParseError(
                f"Reward JSON is not a valid dict or is empty: {reward_json_content[:100]}"
            )
        # Like Harbor, require real finite numbers: json.loads accepts
        # NaN/Infinity tokens and overflows like 1e309.
        for key, value in reward_dict.items():
            if not isinstance(value, (int, float)) or (
                isinstance(value, float) and not math.isfinite(value)
            ):
                raise VerifierOutputParseError(
                    f"Non-numeric or non-finite reward {value!r} for {key!r} in reward.json"
                )
        value = (
            reward_dict["reward"]
            if "reward" in reward_dict
            else next(iter(reward_dict.values()))
        )
        return float(value), reward_dict

    try:
        reward_content = await sandbox().read_file(reward_text_path)
    except FileNotFoundError as e:
        raise RewardFileNotFoundError(
            f"No reward file found at {reward_json_path} or {reward_text_path}. "
            f"Test script exit code was {exit_code}."
        ) from e
    if not reward_content.strip():
        raise RewardFileEmptyError(f"Reward file is empty: {reward_text_path}")
    try:
        value = float(reward_content.strip())
    except (ValueError, TypeError) as e:
        raise VerifierOutputParseError(
            f"Failed to parse reward.txt as float: {reward_content[:100]}"
        ) from e
    if not math.isfinite(value):
        raise VerifierOutputParseError(f"Non-finite reward in reward.txt: {value!r}")
    return value, None
