"""Shared utilities for sandbox operations."""

from pathlib import Path

from inspect_ai.util import sandbox


async def copy_directory_to_sandbox(
    local_dir: str | Path, container_path: str
) -> None:
    """Recursively copy a local directory to the sandbox.

    Args:
        local_dir: Local directory path to copy from (string or Path).
        container_path: Container path to copy to (e.g., "/tests", "/solution").

    Raises:
        Exception: If copying fails.
    """
    local_dir_path = Path(local_dir)

    for file_path in local_dir_path.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(local_dir_path)
            target_path = f"{container_path}/{rel_path}".replace("\\", "/")

            content = file_path.read_text()
            await sandbox().write_file(target_path, content)
