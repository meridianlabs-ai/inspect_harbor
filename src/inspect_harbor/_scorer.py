"""Scorer for Harbor tasks in Inspect AI."""

import json
from pathlib import Path
from typing import Any

from inspect_ai.scorer import Score, Scorer, Target, accuracy, scorer, stderr
from inspect_ai.solver import TaskState
from inspect_ai.util import sandbox

from inspect_harbor._sandbox_utils import (
    cleanup_sandbox_directories,
    copy_directory_to_sandbox,
)


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
        tests_dir = Path(state.metadata.get("tests_dir", ""))
        test_path = Path(state.metadata.get("test_path", ""))
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
        except ValueError:
            # Fallback if relative path resolution fails
            container_test_path = "/tests/test.sh"

        result = await sandbox().exec(
            ["bash", "-l", container_test_path],
            timeout=int(verifier_timeout_sec),
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

        return score_result

    return score


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
