"""Tests for task directory layout and Docker image names."""

from pathlib import Path

import pytest
from inspect_harbor._harbor.paths import TaskPaths, sanitize_docker_image_name


def test_task_paths_layout(tmp_path: Path) -> None:
    """Every conventional file and directory hangs off the resolved task dir."""
    root = tmp_path.resolve()
    paths = TaskPaths(str(tmp_path))  # str is accepted and resolved
    assert paths.task_dir == root
    assert paths.instruction_path == root / "instruction.md"
    assert paths.config_path == root / "task.toml"
    assert paths.environment_dir == root / "environment"
    assert paths.test_path == root / "tests" / "test.sh"
    assert paths.solve_path == root / "solution" / "solve.sh"
    assert (
        paths.step_instruction_path("one") == root / "steps" / "one" / "instruction.md"
    )


# Reference outputs captured from harbor 0.21.0's ``_sanitize_docker_image_name``.
@pytest.mark.parametrize(
    "name,expected",
    [
        ("hb__harbor-test/simple-task", "hb__harbor-test-simple-task"),
        (
            "hb__Enterprise-Bench/l1-l2-bench__main",
            "hb__enterprise-bench-l1-l2-bench__main",
        ),
        (
            "hb__aider/polyglot_java_affine-cipher",
            "hb__aider-polyglot_java_affine-cipher",
        ),
        ("hb___leading", "hb___leading"),
        ("hb__UPPER.case", "hb__upper.case"),
        ("hb__with space", "hb__with-space"),
        ("-starts-dash", "0-starts-dash"),
        ("ünïcode", "0-n-code"),
    ],
)
def test_sanitize_docker_image_name_matches_harbor(name: str, expected: str) -> None:
    """Image names are sanitised exactly like Harbor does it."""
    assert sanitize_docker_image_name(name) == expected
