"""``name@version`` datasets from a Harbor ``registry.json`` file.

This is Harbor's original, pre-hub dataset index: a JSON array of datasets,
each listing tasks by git URL, commit and path (or a local path). The
curated file in ``laude-institute/harbor`` is the default source; private
registries can be given by URL or local path.
"""

import json
import os
import time
from pathlib import Path, PurePosixPath

import httpx
from packaging.version import InvalidVersion, Version
from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

from inspect_harbor._harbor.cache import cache_root, stable_key
from inspect_harbor._harbor.git_tasks import GitTaskSpec

DEFAULT_REGISTRY_URL = (
    "https://raw.githubusercontent.com/laude-institute/harbor/main/registry.json"
)
REGISTRY_CACHE_TTL_SECONDS = 24 * 60 * 60


class RegistryTask(BaseModel):
    """One task entry of a registry dataset."""

    model_config = ConfigDict(extra="allow")

    name: str
    git_url: str | None = None
    git_commit_id: str | None = None
    path: PurePosixPath


class RegistryDataset(BaseModel):
    """One ``name@version`` dataset of a registry file."""

    model_config = ConfigDict(extra="allow")

    name: str
    version: str
    description: str = ""
    tasks: list[RegistryTask]


_REGISTRY_ADAPTER = TypeAdapter(list[RegistryDataset])


def resolve_version(versions: list[str]) -> str:
    """Pick the version to use when none is given, as Harbor does.

    ``head`` wins if present, then the highest PEP 440 version (first listed
    wins a tie), then the lexically last string.

    Raises:
        ValueError: When ``versions`` is empty.
    """
    if not versions:
        raise ValueError("No versions available")
    if "head" in versions:
        return "head"
    parsed: list[tuple[Version, str]] = []
    for v in versions:
        try:
            parsed.append((Version(v), v))
        except InvalidVersion:
            pass
    if parsed:
        parsed.sort(key=lambda item: item[0], reverse=True)
        return parsed[0][1]
    return sorted(versions, reverse=True)[0]


def parse_registry(text: str, source: str) -> list[RegistryDataset]:
    """Parse registry JSON, naming ``source`` in any error.

    Raises:
        ValueError: When the body is not JSON or not a list of datasets.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Registry at {source} is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(
            f"Registry at {source} must be a JSON list of datasets, got "
            f"{type(data).__name__}"
        )
    try:
        return _REGISTRY_ADAPTER.validate_python(data)
    except ValidationError as exc:
        exc.add_note(f"while parsing registry at {source}")
        raise


async def load_registry(
    url: str | None = None,
    path: Path | None = None,
    overwrite: bool = False,
    client: httpx.AsyncClient | None = None,
) -> list[RegistryDataset]:
    """Load a registry from a local file or URL (default: the curated registry).

    URL bodies are cached for 24 hours under the task cache once they have
    parsed successfully, so a bad response is never served from cache;
    ``overwrite`` forces a refetch.

    Raises:
        ValueError: When both ``url`` and ``path`` are given, or the body is
            not a valid registry.
        httpx.HTTPStatusError: When the URL cannot be fetched.
    """
    if url is not None and path is not None:
        raise ValueError("Only one of registry url or path can be provided")
    if path is not None:
        return parse_registry(path.read_text(), str(path))
    url = url or DEFAULT_REGISTRY_URL
    cache_file = cache_root() / "registry" / f"{stable_key(url)}.json"
    if not overwrite and cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < REGISTRY_CACHE_TTL_SECONDS:
            return parse_registry(
                cache_file.read_text(), f"{url} (cached at {cache_file})"
            )
    text = await _fetch_text(url, client)
    datasets = parse_registry(text, url)
    _write_atomically(cache_file, text)
    return datasets


async def resolve_registry_dataset(
    name_version: str,
    url: str | None = None,
    path: Path | None = None,
    overwrite: bool = False,
    client: httpx.AsyncClient | None = None,
) -> list[GitTaskSpec | Path]:
    """Resolve ``name`` or ``name@version`` to its task sources, in registry order.

    Git-hosted tasks come back as ``GitTaskSpec``; tasks given by local path
    come back as ``Path``.

    Raises:
        ValueError: When the dataset or version is not in the registry.
    """
    name, _, version = name_version.partition("@")
    datasets = await load_registry(
        url=url, path=path, overwrite=overwrite, client=client
    )
    by_version = {d.version: d for d in datasets if d.name == name}
    if not by_version:
        raise ValueError(f"Dataset {name!r} not found in registry")
    if not version:
        version = resolve_version(list(by_version))
    if version not in by_version:
        raise ValueError(
            f"Version {version!r} of dataset {name!r} not found in registry"
        )

    entries: list[GitTaskSpec | Path] = []
    for task in by_version[version].tasks:
        if task.git_url is not None:
            entries.append(
                GitTaskSpec(
                    git_url=task.git_url,
                    path=task.path,
                    git_commit_id=task.git_commit_id,
                )
            )
        else:
            entries.append(Path(task.path).expanduser().resolve())
    return entries


async def _fetch_text(url: str, client: httpx.AsyncClient | None) -> str:
    async def _get(http: httpx.AsyncClient) -> str:
        response = await http.get(url, follow_redirects=True)
        response.raise_for_status()
        return response.text

    if client is not None:
        return await _get(client)
    async with httpx.AsyncClient(timeout=120.0) as http:
        return await _get(http)


def _write_atomically(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text)
    os.replace(tmp, path)
