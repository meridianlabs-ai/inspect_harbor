"""Shared utilities for sandbox operations."""

import logging
from pathlib import Path

from inspect_ai.util import sandbox

logger = logging.getLogger(__name__)


async def copy_directory_to_sandbox(local_dir: str | Path, container_path: str) -> None:
    """Recursively copy a local directory to the sandbox.

    All files are read as bytes to preserve binary content integrity.
    The sandbox write_file method handles both text and binary content.

    Args:
        local_dir: Local directory path to copy from (string or Path).
        container_path: Container path to copy to (e.g., "/tests", "/solution").
    """
    local_dir_path = Path(local_dir)

    for file_path in local_dir_path.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(local_dir_path)
            target_path = f"{container_path}/{rel_path}".replace("\\", "/")

            # Always read as bytes to handle both text and binary files correctly
            content = file_path.read_bytes()

            await sandbox().write_file(target_path, content)


async def cleanup_sandbox_directories(*paths: str) -> None:
    """Clean up directories from the sandbox.

    Removes the specified directories from the sandbox. Errors are logged but
    not raised to ensure cleanup continues even if some operations fail.

    Args:
        *paths: Variable number of container paths to remove (e.g., "/tests", "/solution").
    """
    for path in paths:
        try:
            await sandbox().exec(["rm", "-rf", path])
        except (RuntimeError, OSError, TimeoutError) as e:
            logger.warning(f"Failed to cleanup sandbox directory {path}: {e}")
