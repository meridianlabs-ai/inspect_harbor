"""Shared helpers for building task directories in tests."""

from pathlib import Path


def make_task(
    root: Path,
    toml: str = "",
    instruction: str | None = "Do the thing.",
    with_test: bool = True,
    test_name: str = "test.sh",
    dirname: str = "my-task",
) -> Path:
    """Write a minimal task directory under ``root`` and return it."""
    task_dir = root / dirname
    (task_dir / "environment").mkdir(parents=True)
    (task_dir / "environment" / "Dockerfile").write_text("FROM scratch\n")
    (task_dir / "task.toml").write_text(toml)
    if instruction is not None:
        (task_dir / "instruction.md").write_text(instruction)
    if with_test:
        (task_dir / "tests").mkdir()
        (task_dir / "tests" / test_name).write_text("#!/bin/bash\n")
    return task_dir
