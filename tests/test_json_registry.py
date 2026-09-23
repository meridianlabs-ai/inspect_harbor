"""Tests for JSON registry files (``name@version`` datasets)."""

import json
import time
from pathlib import Path, PurePosixPath

import httpx
import pytest
from inspect_harbor._harbor.git_tasks import GitTaskSpec
from inspect_harbor._harbor.registry import (
    DEFAULT_REGISTRY_URL,
    load_registry,
    resolve_registry_dataset,
    resolve_version,
)

REGISTRY = [
    {
        "name": "aime",
        "version": "1.0",
        "description": "AIME problems",
        "tasks": [
            {
                "name": "aime_i-9",
                "git_url": "https://github.com/org/repo",
                "git_commit_id": "a" * 40,
                "path": "tasks/aime_i-9",
            },
            {
                "name": "aime_ii-3",
                "git_url": "https://github.com/org/repo",
                "git_commit_id": None,
                "path": "tasks/aime_ii-3",
            },
        ],
        "metrics": [{"type": "mean", "kwargs": {}}],
    },
    {
        "name": "aime",
        "version": "2.0",
        "description": "newer",
        "tasks": [{"name": "only", "path": "/abs/local/only"}],
    },
    {"name": "other", "version": "head", "description": "", "tasks": []},
]


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Temp cache dir for the URL cache."""
    cache = tmp_path / "cache"
    monkeypatch.setenv("INSPECT_HARBOR_CACHE_DIR", str(cache))
    return cache


@pytest.fixture
def registry_file(tmp_path: Path) -> Path:
    """The sample registry written to disk."""
    p = tmp_path / "registry.json"
    p.write_text(json.dumps(REGISTRY))
    return p


@pytest.mark.parametrize(
    "versions,expected",
    [
        (["1.0", "head", "2.0"], "head"),
        (["1.0", "1.10", "1.9"], "1.10"),
        (["0.1", "0.2.1", "0.2"], "0.2.1"),
        (["b", "a", "c"], "c"),
        (["1.0", "zzz"], "1.0"),
        (["v1", "0.5"], "v1"),
        (["1.0rc1", "1.0"], "1.0"),
        (["1.0", "1.0.0"], "1.0"),
    ],
)
def test_resolve_version(versions: list[str], expected: str) -> None:
    """``head`` wins, then the highest numeric version, then lexical order."""
    assert resolve_version(versions) == expected


def test_resolve_version_empty_raises() -> None:
    """No versions is an error."""
    with pytest.raises(ValueError, match="No versions"):
        resolve_version([])


async def test_load_registry_from_path(registry_file: Path) -> None:
    """A local registry file parses into datasets."""
    datasets = await load_registry(path=registry_file)
    assert [(d.name, d.version) for d in datasets] == [
        ("aime", "1.0"),
        ("aime", "2.0"),
        ("other", "head"),
    ]
    assert datasets[0].tasks[0].git_commit_id == "a" * 40
    assert datasets[0].tasks[0].path == PurePosixPath("tasks/aime_i-9")


async def test_load_registry_from_url_is_cached(isolated_cache: Path) -> None:
    """The URL body is fetched once and reused within the TTL."""
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert str(request.url) == "https://example.test/registry.json"
        return httpx.Response(200, json=REGISTRY)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    url = "https://example.test/registry.json"
    first = await load_registry(url=url, client=client)
    second = await load_registry(url=url, client=client)
    assert calls == 1
    assert [d.name for d in first] == [d.name for d in second]
    cached = list((isolated_cache / "registry").glob("*.json"))
    assert len(cached) == 1

    # An expired cache file is refetched; ``overwrite`` always refetches.
    old = time.time() - 48 * 3600
    import os

    os.utime(cached[0], (old, old))
    await load_registry(url=url, client=client)
    assert calls == 2
    await load_registry(url=url, overwrite=True, client=client)
    assert calls == 3


@pytest.mark.parametrize(
    "bad_body,match",
    [
        (b"<html>outage</html>", "not valid JSON"),
        (b'{"name": "x"}', "must be a JSON list"),
    ],
)
async def test_bad_registry_body_is_not_cached(bad_body: bytes, match: str) -> None:
    """A bad response fails loudly and the next fetch is not poisoned by cache."""
    bodies = [bad_body, json.dumps(REGISTRY).encode()]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=bodies.pop(0))

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    url = "https://example.test/registry.json"
    with pytest.raises(ValueError, match=match):
        await load_registry(url=url, client=client)
    datasets = await load_registry(url=url, client=client)
    assert [d.name for d in datasets] == ["aime", "aime", "other"]
    assert not bodies


async def test_load_registry_url_error_propagates() -> None:
    """A failing fetch is an ``HTTPStatusError``."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        await load_registry(url="https://example.test/missing.json", client=client)


async def test_load_registry_requires_one_source() -> None:
    """Both or neither of ``url`` and ``path`` is an error."""
    with pytest.raises(ValueError, match="Only one"):
        await load_registry(url="https://x", path=Path("y"))


def test_default_registry_url() -> None:
    """The default is the curated laude-institute registry file."""
    assert DEFAULT_REGISTRY_URL == (
        "https://raw.githubusercontent.com/laude-institute/harbor/main/registry.json"
    )


async def test_resolve_registry_dataset_explicit_version(registry_file: Path) -> None:
    """``name@version`` returns git specs and local paths in registry order."""
    entries = await resolve_registry_dataset("aime@1.0", path=registry_file)
    assert entries == [
        GitTaskSpec(
            git_url="https://github.com/org/repo",
            path=PurePosixPath("tasks/aime_i-9"),
            git_commit_id="a" * 40,
        ),
        GitTaskSpec(
            git_url="https://github.com/org/repo",
            path=PurePosixPath("tasks/aime_ii-3"),
            git_commit_id=None,
        ),
    ]


async def test_resolve_registry_dataset_latest_version(registry_file: Path) -> None:
    """Without a version the highest one is picked."""
    entries = await resolve_registry_dataset("aime", path=registry_file)
    assert entries == [Path("/abs/local/only")]


async def test_resolve_registry_dataset_unknown(registry_file: Path) -> None:
    """Unknown dataset names and versions are reported."""
    with pytest.raises(ValueError, match="Dataset 'nope' not found"):
        await resolve_registry_dataset("nope", path=registry_file)
    with pytest.raises(ValueError, match="Version '9.9' of dataset 'aime' not found"):
        await resolve_registry_dataset("aime@9.9", path=registry_file)


async def test_resolve_registry_dataset_uses_default_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without ``url`` or ``path`` the default registry URL is fetched."""
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json=REGISTRY)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    entries = await resolve_registry_dataset("other@head", client=client)
    assert entries == []
    assert seen == [DEFAULT_REGISTRY_URL]
