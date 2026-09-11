"""Scorer for Harbor tasks in Inspect AI."""

import json
import logging
from pathlib import Path
from typing import Any

from harbor.constants import MAIN_SERVICE_NAME
from harbor.models.task.config import TaskConfig, VerifierEnvironmentMode
from harbor.models.task.verifier_mode import resolve_task_verifier_mode
from harbor.models.trial.paths import EnvironmentPaths
from inspect_ai.scorer import Score, Scorer, Target, accuracy, scorer, stderr
from inspect_ai.solver import TaskState
from inspect_ai.util import sandbox

from inspect_harbor._harbor.converters import _user_to_str
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

        # Create Harbor's standard log directories. Harbor bind-mounts and
        # pre-creates /logs/artifacts, so create it here too since collect
        # hooks may assume it exists.
        await sandbox().exec(["mkdir", "-p", "/logs/agent"])
        await sandbox().exec(["mkdir", "-p", "/logs/verifier"])
        await sandbox().exec(["mkdir", "-p", "/logs/artifacts"])

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

        result = await sandbox().exec(
            ["bash", "-l", container_test_path],
            timeout=int(verifier_timeout_sec),
            env=verifier_env,
            user=verifier_user,
        )

        reward_value, reward_dict = await _parse_reward_file(result.returncode)
        passed = reward_value > 0

        score_result = Score(
            value=reward_value,
            answer="PASS" if passed else "FAIL",
            explanation=f"Test exit code: {result.returncode}\n\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
            metadata={"reward_dict": reward_dict} if reward_dict else None,
        )

        await cleanup_sandbox_directories("/tests", "/logs/verifier")
        await cleanup_sandbox_env_vars(list(verifier_env.keys()))

        return score_result

    return score


async def _run_verifier_collect(harbor_config: dict[str, Any]) -> None:
    """Run ``[[verifier.collect]]`` hooks and, in separate mode, reset the repo.

    Harbor runs collect hooks in their target compose service after the agent
    phase ends and before verification, then, when the verifier runs in
    ``separate`` mode, builds the verifier in a fresh container at the base
    commit. We share a single container, so we run the hooks here and
    approximate the fresh verifier container by resetting the repo to the base
    commit. The reset is only an approximation: Harbor's separate verifier may
    use a different image than the agent container.
    """
    task_cfg = TaskConfig.model_validate(harbor_config)
    collect_steps = task_cfg.verifier.collect
    if not collect_steps:
        return

    workdir = task_cfg.environment.workdir or "/app"

    for step in collect_steps:
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
        result = await sandbox().exec(
            ["bash", "-c", step.command],
            timeout=int(step.timeout_sec),
            user=_user_to_str(step.user),
        )
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
    if resolve_task_verifier_mode(task_cfg) != VerifierEnvironmentMode.SEPARATE:
        return

    base_commit = task_cfg.metadata.get("base_commit_hash")
    if not base_commit:
        return

    # The agent may have committed as a non-root user, so mark the repo safe to
    # avoid git's "dubious ownership" error when resetting as the default user.
    reset_cmd = (
        f"cd {workdir} && "
        "git config --global --add safe.directory '*' && "
        f"git checkout -f {base_commit} && git clean -fd"
    )
    result = await sandbox().exec(["bash", "-c", reset_cmd], timeout=60)
    if result.returncode != 0:
        logger.warning(
            "repo reset to base commit %r exited %d\nstdout:\n%s\nstderr:\n%s",
            base_commit,
            result.returncode,
            result.stdout,
            result.stderr,
        )


async def _parse_reward_file(exit_code: int) -> tuple[float, dict[str, Any] | None]:
    """Parse reward from either reward.txt or reward.json.

    Args:
        exit_code: Test script exit code.

    Returns:
        Tuple of (reward value as float, reward dict if from JSON else None).

    Raises:
        RewardFileEmptyError: When reward file exists but is empty.
        VerifierOutputParseError: When reward file content cannot be parsed.
        RewardFileNotFoundError: When no reward file exists at expected locations.
    """
    reward_text_path = "/logs/verifier/reward.txt"
    reward_json_path = "/logs/verifier/reward.json"

    try:
        reward_content = await sandbox().read_file(reward_text_path)
        if not reward_content.strip():
            raise RewardFileEmptyError(f"Reward file is empty: {reward_text_path}")

        try:
            return float(reward_content.strip()), None
        except (ValueError, TypeError) as e:
            raise VerifierOutputParseError(
                f"Failed to parse reward.txt as float: {reward_content[:100]}"
            ) from e

    except FileNotFoundError:
        try:
            reward_json_content = await sandbox().read_file(reward_json_path)
            if not reward_json_content.strip():
                raise RewardFileEmptyError(f"Reward file is empty: {reward_json_path}")

            try:
                reward_dict = json.loads(reward_json_content)
                # If dict has "reward" key, use it; otherwise use first value
                if isinstance(reward_dict, dict):
                    if "reward" in reward_dict:
                        return float(reward_dict["reward"]), reward_dict
                    # Use first value from dict
                    elif reward_dict:
                        return float(next(iter(reward_dict.values()))), reward_dict
                raise VerifierOutputParseError(
                    f"Reward JSON is not a valid dict or is empty: {reward_json_content[:100]}"
                )
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                raise VerifierOutputParseError(
                    f"Failed to parse reward.json: {reward_json_content[:100]}"
                ) from e

        except FileNotFoundError as e:
            raise RewardFileNotFoundError(
                f"No reward file found at {reward_text_path} or {reward_json_path}. "
                f"Test script exit code was {exit_code}."
            ) from e
