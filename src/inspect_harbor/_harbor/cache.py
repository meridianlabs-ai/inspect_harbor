"""Location and keying of the local task cache."""

import hashlib
import os
from pathlib import Path

CACHE_DIR_ENV = "INSPECT_HARBOR_CACHE_DIR"
_DEFAULT_CACHE_DIR = Path("~/.cache/inspect_harbor/tasks")


def cache_root() -> Path:
    """Root directory for downloaded tasks.

    Defaults to ``~/.cache/inspect_harbor/tasks``; override with the
    ``INSPECT_HARBOR_CACHE_DIR`` environment variable. Callers create
    subdirectories as needed.
    """
    override = os.environ.get(CACHE_DIR_ENV)
    return Path(override if override else _DEFAULT_CACHE_DIR).expanduser()


def stable_key(*parts: str) -> str:
    """A short, deterministic cache key for a tuple of identifying strings."""
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]
