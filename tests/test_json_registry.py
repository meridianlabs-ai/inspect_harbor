"""Tests for JSON registry files (``name@version`` datasets)."""

import json
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
AIME_1_0 = [
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


@pytest.fixture
def registry_file(tmp_path: Path) -> Path:
    """The sample registry written to disk."""
    p = tmp_path / "registry.json"
    p.write_text(json.dumps(REGISTRY))
    return p


def _client(*bodies: bytes, status: int = 200) -> tuple[httpx.AsyncClient, list[str]]:
    """A client whose responses are served from ``bodies`` in order; returns seen URLs."""
    queue = list(bodies)
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(status, content=queue.pop(0) if queue else b"[]")

    return httpx.AsyncClient(transport=httpx.MockTransport(handler)), seen


@pytest.mark.parametrize(
    "versions,expected",
    [
        (["1.0", "head", "2.0"], "head"),
        (["1.0", "1.10", "1.9"], "1.10"),
        (["1.0rc1", "1.0"], "1.0"),
        (["1.0", "1.0.0"], "1.0"),
        (["b", "a", "c"], "c"),
        (["1.0", "zzz"], "1.0"),
    ],
)
def test_resolve_version(versions: list[str], expected: str) -> None:
    """``head`` wins, then the highest PEP 440 version (first wins ties), then lexical."""
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


async def test_load_registry_from_url_fetches_every_time() -> None:
    """Like Harbor, the registry URL is fetched on each load; nothing is cached."""
    body = json.dumps(REGISTRY).encode()
    client, seen = _client(body, body)
    url = "https://example.test/registry.json"
    await load_registry(url=url, client=client)
    await load_registry(url=url, client=client)
    assert seen == [url, url]


@pytest.mark.parametrize(
    "bad_body,match",
    [
        (b"<html>outage</html>", "not valid JSON"),
        (b'{"name": "x"}', "must be a JSON list"),
    ],
)
async def test_bad_registry_body_raises(bad_body: bytes, match: str) -> None:
    """A non-JSON or non-list body fails with an error naming the source."""
    client, _ = _client(bad_body)
    with pytest.raises(ValueError, match=match):
        await load_registry(url="https://example.test/registry.json", client=client)


async def test_load_registry_errors() -> None:
    """HTTP failures propagate; url and path together are rejected."""
    client, _ = _client(status=404)
    with pytest.raises(httpx.HTTPStatusError):
        await load_registry(url="https://example.test/missing.json", client=client)
    with pytest.raises(ValueError, match="Only one"):
        await load_registry(url="https://x", path=Path("y"))


@pytest.mark.parametrize(
    "name_version,expected",
    [("aime@1.0", AIME_1_0), ("aime", [Path("/abs/local/only")])],
)
async def test_resolve_registry_dataset(
    registry_file: Path, name_version: str, expected: list[GitTaskSpec | Path]
) -> None:
    """An explicit version returns its sources in order; no version picks the highest."""
    assert await resolve_registry_dataset(name_version, path=registry_file) == expected


async def test_resolve_registry_dataset_unknown(registry_file: Path) -> None:
    """Unknown dataset names and versions are reported."""
    with pytest.raises(ValueError, match="Dataset 'nope' not found"):
        await resolve_registry_dataset("nope", path=registry_file)
    with pytest.raises(ValueError, match="Version '9.9' of dataset 'aime' not found"):
        await resolve_registry_dataset("aime@9.9", path=registry_file)


async def test_resolve_registry_dataset_uses_default_url() -> None:
    """Without ``url`` or ``path`` the curated registry URL is fetched."""
    client, seen = _client(json.dumps(REGISTRY).encode())
    assert await resolve_registry_dataset("other@head", client=client) == []
    assert seen == [DEFAULT_REGISTRY_URL]
