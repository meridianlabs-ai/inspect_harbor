"""Shared utilities for sandbox operations."""

import logging
import os
import re
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


def resolve_env_vars(env_dict: dict[str, str]) -> dict[str, str]:
    """
    Resolve environment variable templates in a dictionary.

    Templates like "${VAR_NAME}" are replaced with values from os.environ.
    Literal values are passed through unchanged.

    Args:
        env_dict: Dictionary with potentially templated values

    Returns:
        Dictionary with resolved values

    Raises:
        ValueError: If a required environment variable is not found
    """
    resolved = {}
    pattern = re.compile(r"\$\{([^}]+)\}")

    for key, value in env_dict.items():
        match = pattern.fullmatch(value)
        if match:
            var_name = match.group(1)
            if var_name not in os.environ:
                raise ValueError(
                    f"Environment variable '{var_name}' not found in host environment"
                )
            resolved[key] = os.environ[var_name]
        else:
            resolved[key] = value

    return resolved


async def cleanup_sandbox_directories(*paths: str) -> None:
    """Removes the specified directories from the sandbox.

    Errors are logged but not raised to ensure cleanup continues even if some operations fail.

    Args:
        *paths: Variable number of container paths to remove (e.g., "/tests", "/solution").
    """
    for path in paths:
        try:
            await sandbox().exec(["rm", "-rf", path])
        except (RuntimeError, OSError, TimeoutError) as e:
            logger.warning(f"Failed to cleanup sandbox directory {path}: {e}")


async def cleanup_sandbox_env_vars(env_var_keys: list[str]) -> None:
    """Unsets the specified environment variables from the sandbox.

    Errors are logged but not raised to ensure cleanup continues even if some operations fail.

    Args:
        env_var_keys: List of environment variable names to unset (e.g., ["API_KEY", "SECRET"]).
    """
    for var_key in env_var_keys:
        try:
            await sandbox().exec(["unset", var_key])
        except (RuntimeError, OSError, TimeoutError) as e:
            logger.warning(
                f"Failed to cleanup sandbox environment variable {var_key}: {e}"
            )
