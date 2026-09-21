"""Tests for the hub client (Harbor's Supabase-backed package registry)."""

import io
import json
import tarfile
from pathlib import Path
from typing import Any

import httpx
import pytest
from inspect_harbor._harbor import hub
from inspect_harbor._harbor.hub import (
    HubClient,
    HubTaskRef,
    PackageRef,
    RefType,
    classify_ref,
    download_hub_tasks,
    hub_task_dir,
    parse_package_ref,
    resolve_hub_dataset,
)

ORG, NAME = "acme", "bench"
DV_ID = "dv-123"
DV_HASH = "d" * 64
TASK_HASH_A = "a" * 64
TASK_HASH_B = "b" * 64


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Temp cache, telemetry on, fast retries, default hub URL and key."""
    cache = tmp_path / "cache"
    monkeypatch.setenv("INSPECT_HARBOR_CACHE_DIR", str(cache))
    monkeypatch.delenv("INSPECT_HARBOR_NO_TELEMETRY", raising=False)
    monkeypatch.delenv("HARBOR_SUPABASE_URL", raising=False)
    monkeypatch.delenv("HARBOR_SUPABASE_PUBLISHABLE_KEY", raising=False)
    monkeypatch.setattr(HubClient, "retry_wait_seconds", 0.0)
    return cache


def _dataset_version_row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": DV_ID,
        "revision": 3,
        "content_hash": DV_HASH,
        "description": "A benchmark",
        "yanked_at": None,
        "yanked_reason": None,
    }
    row.update(overrides)
    return row


def _task_rows(*hashes: str) -> list[dict[str, Any]]:
    return [
        {
            "task_version": {
                "content_hash": h,
                "package": {"name": f"task-{h[0]}", "org": {"name": ORG}},
            }
        }
        for h in hashes
    ]


def _archive_bytes(instruction: str = "hello") -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, content in [
            ("task.toml", '[environment]\ndocker_image = "x"\n'),
            ("instruction.md", instruction),
            ("environment/Dockerfile", "FROM scratch\n"),
            ("tests/test.sh", "#!/bin/bash\n"),
        ]:
            data = content.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


class FakeHub:
    """A scripted Supabase backend behind ``httpx.MockTransport``."""

    def __init__(self, page_size: int = 1000) -> None:
        self.requests: list[httpx.Request] = []
        self.dataset_row: dict[str, Any] | None = _dataset_version_row()
        self.task_rows = _task_rows(TASK_HASH_A, TASK_HASH_B)
        self.page_size = page_size
        self.archives: dict[str, bytes] = {}
        self.fail_first_n = 0
        for h in (TASK_HASH_A, TASK_HASH_B):
            self.archives[f"packages/{ORG}/task-{h[0]}/{h}/dist.tar.gz"] = (
                _archive_bytes(f"task {h[0]}")
            )

    def handler(self, request: httpx.Request) -> httpx.Response:
        """Route a request to the scripted table, RPC, or storage response."""
        self.requests.append(request)
        if self.fail_first_n > 0:
            self.fail_first_n -= 1
            raise httpx.ConnectError("boom", request=request)
        path = request.url.path
        params = request.url.params
        if path.endswith("/rest/v1/dataset_version_tag"):
            if self.dataset_row is None:
                return httpx.Response(200, json=[])
            return httpx.Response(
                200,
                json=[
                    {
                        "dataset_version": self.dataset_row,
                        "package": {
                            "name": NAME,
                            "type": "dataset",
                            "org": {"name": ORG},
                        },
                    }
                ],
            )
        if path.endswith("/rest/v1/dataset_version"):
            if self.dataset_row is None:
                return httpx.Response(200, json=[])
            return httpx.Response(
                200,
                json=[
                    {
                        **self.dataset_row,
                        "package": {
                            "name": NAME,
                            "type": "dataset",
                            "org": {"name": ORG},
                        },
                    }
                ],
            )
        if path.endswith("/rest/v1/dataset_version_task"):
            offset = int(params.get("offset", "0"))
            limit = int(params.get("limit", str(self.page_size)))
            return httpx.Response(200, json=self.task_rows[offset : offset + limit])
        if path.endswith("/rest/v1/rpc/resolve_task_version"):
            body = json.loads(request.content)
            digest = body["p_ref"].removeprefix("sha256:")
            for row in self.task_rows:
                tv = row["task_version"]
                if (
                    tv["content_hash"] == digest
                    and tv["package"]["name"] == body["p_name"]
                ):
                    return httpx.Response(
                        200,
                        json={
                            "id": f"tv-{digest[0]}",
                            "archive_path": (
                                f"packages/{ORG}/{body['p_name']}/{digest}/dist.tar.gz"
                            ),
                            "content_hash": digest,
                            "revision": 1,
                            "yanked_at": None,
                            "yanked_reason": None,
                        },
                    )
            return httpx.Response(200, content=b"null")
        if "/storage/v1/object/authenticated/packages/" in path:
            key = path.split("/storage/v1/object/authenticated/packages/", 1)[1]
            if key in self.archives:
                return httpx.Response(200, content=self.archives[key])
            return httpx.Response(400, json={"error": "not found"})
        if path.endswith("/rest/v1/task_version_download"):
            return httpx.Response(201)
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

    def client(self) -> HubClient:
        """A ``HubClient`` wired to this fake."""
        return HubClient(transport=httpx.MockTransport(self.handler))

    def paths(self) -> list[str]:
        """Request paths seen so far."""
        return [r.url.path for r in self.requests]


# --- ref parsing ---------------------------------------------------------


@pytest.mark.parametrize(
    "slug,expected",
    [
        ("acme/bench", PackageRef("acme", "bench", "latest")),
        ("acme/bench@latest", PackageRef("acme", "bench", "latest")),
        ("acme/bench@3", PackageRef("acme", "bench", "3")),
        ("acme/bench@sha256:abc", PackageRef("acme", "bench", "sha256:abc")),
        (
            "Some-Org/some.name_1@stable",
            PackageRef("Some-Org", "some.name_1", "stable"),
        ),
    ],
)
def test_parse_package_ref(slug: str, expected: PackageRef) -> None:
    """``org/name[@ref]`` is split with ``latest`` as the default ref."""
    assert parse_package_ref(slug) == expected
    assert expected.slug == f"{expected.org}/{expected.name}"


@pytest.mark.parametrize("slug", ["bench", "a/b/c", "/bench", "a/../b", ""])
def test_parse_package_ref_rejects_bad_names(slug: str) -> None:
    """Names must be ``org/name``."""
    with pytest.raises(ValueError, match="org/name"):
        parse_package_ref(slug)


@pytest.mark.parametrize(
    "ref,expected",
    [
        (None, (RefType.TAG, "latest")),
        ("", (RefType.TAG, "latest")),
        ("latest", (RefType.TAG, "latest")),
        ("stable", (RefType.TAG, "stable")),
        ("7", (RefType.REVISION, "7")),
        ("sha256:abc", (RefType.DIGEST, "abc")),
    ],
)
def test_classify_ref(ref: str | None, expected: tuple[RefType, str]) -> None:
    """Refs are tags, integer revisions, or ``sha256:`` digests."""
    assert classify_ref(ref) == expected


# --- dataset resolution --------------------------------------------------


async def test_resolve_dataset_by_tag() -> None:
    """A tag ref queries ``dataset_version_tag`` and lists the tasks."""
    fake = FakeHub()
    meta = await fake.client().resolve_dataset(parse_package_ref(f"{ORG}/{NAME}"))
    assert meta.name == f"{ORG}/{NAME}"
    assert meta.version == f"sha256:{DV_HASH}"
    assert meta.description == "A benchmark"
    assert meta.dataset_version_id == DV_ID
    assert meta.revision == 3
    assert [t.content_hash for t in meta.task_refs] == [TASK_HASH_A, TASK_HASH_B]
    assert meta.task_refs[0] == HubTaskRef(ORG, "task-a", TASK_HASH_A)

    tag_req = fake.requests[0]
    assert tag_req.url.path == "/rest/v1/dataset_version_tag"
    assert tag_req.url.params["tag"] == "eq.latest"
    assert tag_req.url.params["package.name"] == f"eq.{NAME}"
    assert tag_req.url.params["package.org.name"] == f"eq.{ORG}"
    assert tag_req.url.params["package.type"] == "eq.dataset"
    assert tag_req.headers["apikey"] == hub.DEFAULT_HUB_KEY
    assert tag_req.headers["authorization"] == f"Bearer {hub.DEFAULT_HUB_KEY}"

    tasks_req = fake.requests[1]
    assert tasks_req.url.path == "/rest/v1/dataset_version_task"
    assert tasks_req.url.params["dataset_version_id"] == f"eq.{DV_ID}"
    assert tasks_req.url.params["order"] == "task_version_id"


@pytest.mark.parametrize(
    "ref,column,value",
    [("3", "revision", "eq.3"), (f"sha256:{DV_HASH}", "content_hash", f"eq.{DV_HASH}")],
)
async def test_resolve_dataset_by_revision_or_digest(
    ref: str, column: str, value: str
) -> None:
    """Revision and digest refs query ``dataset_version`` directly."""
    fake = FakeHub()
    meta = await fake.client().resolve_dataset(PackageRef(ORG, NAME, ref))
    assert meta.dataset_version_id == DV_ID
    req = fake.requests[0]
    assert req.url.path == "/rest/v1/dataset_version"
    assert req.url.params[column] == value
    assert req.url.params["package.name"] == f"eq.{NAME}"


async def test_resolve_dataset_pages_through_tasks() -> None:
    """Task listing follows PostgREST paging until a short page."""
    fake = FakeHub(page_size=2)
    fake.task_rows = _task_rows("1" * 64, "2" * 64, "3" * 64, "4" * 64, "5" * 64)
    client = fake.client()
    client.page_size = 2
    meta = await client.resolve_dataset(PackageRef(ORG, NAME, "latest"))
    assert len(meta.task_refs) == 5
    offsets = [
        r.url.params.get("offset")
        for r in fake.requests
        if r.url.path.endswith("dataset_version_task")
    ]
    assert offsets == ["0", "2", "4"]


async def test_resolve_dataset_not_found() -> None:
    """An unknown dataset or ref is a ``ValueError`` naming the slug."""
    fake = FakeHub()
    fake.dataset_row = None
    with pytest.raises(ValueError, match=f"{ORG}/{NAME}@latest"):
        await fake.client().resolve_dataset(PackageRef(ORG, NAME, "latest"))
    with pytest.raises(ValueError, match=f"{ORG}/{NAME}@9"):
        await fake.client().resolve_dataset(PackageRef(ORG, NAME, "9"))


async def test_resolve_dataset_yanked_warns() -> None:
    """A yanked dataset version still resolves but warns."""
    fake = FakeHub()
    fake.dataset_row = _dataset_version_row(
        yanked_at="2026-01-01T00:00:00Z", yanked_reason="broken"
    )
    with pytest.warns(UserWarning, match="yanked.*broken"):
        meta = await fake.client().resolve_dataset(PackageRef(ORG, NAME, "latest"))
    assert meta.yanked_at == "2026-01-01T00:00:00Z"


async def test_resolve_hub_dataset_convenience() -> None:
    """``resolve_hub_dataset`` parses the slug and uses the given client."""
    fake = FakeHub()
    meta = await resolve_hub_dataset(f"{ORG}/{NAME}@3", client=fake.client())
    assert meta.revision == 3
    assert fake.requests[0].url.path == "/rest/v1/dataset_version"


# --- task versions and downloads -----------------------------------------


async def test_resolve_task_version_rpc() -> None:
    """The RPC is called with ``p_org``, ``p_name``, ``p_ref``."""
    fake = FakeHub()
    resolved = await fake.client().resolve_task_version(
        ORG, "task-a", f"sha256:{TASK_HASH_A}"
    )
    assert resolved.id == "tv-a"
    assert resolved.archive_path.endswith(f"{TASK_HASH_A}/dist.tar.gz")
    req = fake.requests[0]
    assert req.method == "POST"
    assert req.url.path == "/rest/v1/rpc/resolve_task_version"
    assert json.loads(req.content) == {
        "p_org": ORG,
        "p_name": "task-a",
        "p_ref": f"sha256:{TASK_HASH_A}",
    }


async def test_resolve_task_version_not_found() -> None:
    """A ``null`` RPC result is a ``ValueError``."""
    fake = FakeHub()
    with pytest.raises(ValueError, match="acme/nope@latest"):
        await fake.client().resolve_task_version(ORG, "nope", "latest")


async def test_download_hub_tasks_end_to_end(isolated_env: Path) -> None:
    """Tasks are resolved, downloaded, extracted, recorded, and cached."""
    fake = FakeHub()
    refs = [
        HubTaskRef(ORG, "task-a", TASK_HASH_A),
        HubTaskRef(ORG, "task-b", TASK_HASH_B),
    ]
    paths = await download_hub_tasks(refs, client=fake.client())

    assert paths == [hub_task_dir(refs[0]), hub_task_dir(refs[1])]
    assert paths[0] == isolated_env / "hub" / ORG / "task-a" / TASK_HASH_A
    assert (paths[0] / "instruction.md").read_text() == "task a"
    assert (paths[1] / "tests" / "test.sh").exists()
    sidecar = json.loads((paths[0].parent / f"{TASK_HASH_A}.json").read_text())
    assert sidecar["org"] == ORG
    assert sidecar["name"] == "task-a"
    assert sidecar["content_hash"] == TASK_HASH_A
    assert sidecar["task_version_id"] == "tv-a"

    telemetry = [
        r for r in fake.requests if r.url.path.endswith("task_version_download")
    ]
    assert len(telemetry) == 2
    assert telemetry[0].headers["prefer"] == "return=minimal"
    assert json.loads(telemetry[0].content) == {"task_version_id": "tv-a"}

    # Second call is served from cache: no further requests at all.
    before = len(fake.requests)
    again = await download_hub_tasks(refs, client=fake.client())
    assert again == paths
    assert len(fake.requests) == before


async def test_download_hub_tasks_overwrite_and_telemetry_opt_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``overwrite`` refetches; the opt-out env var suppresses the counter."""
    fake = FakeHub()
    ref = HubTaskRef(ORG, "task-a", TASK_HASH_A)
    [path] = await download_hub_tasks([ref], client=fake.client())
    (path / "instruction.md").write_text("tampered")

    monkeypatch.setenv("INSPECT_HARBOR_NO_TELEMETRY", "1")
    fake.requests.clear()
    [again] = await download_hub_tasks([ref], overwrite=True, client=fake.client())
    assert again == path
    assert (path / "instruction.md").read_text() == "task a"
    assert not any(r.url.path.endswith("task_version_download") for r in fake.requests)


async def test_download_hub_tasks_telemetry_failure_is_swallowed() -> None:
    """A failing download counter never fails the download."""
    fake = FakeHub()
    original = fake.handler

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("task_version_download"):
            return httpx.Response(500)
        return original(request)

    client = HubClient(transport=httpx.MockTransport(handler))
    [path] = await download_hub_tasks(
        [HubTaskRef(ORG, "task-a", TASK_HASH_A)], client=client
    )
    assert (path / "task.toml").exists()


async def test_download_rejects_unsafe_archive(tmp_path: Path) -> None:
    """Archive members escaping the target dir are refused (data filter)."""
    fake = FakeHub()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo("../escape.txt")
        info.size = 1
        tar.addfile(info, io.BytesIO(b"x"))
    fake.archives[f"packages/{ORG}/task-a/{TASK_HASH_A}/dist.tar.gz"] = buf.getvalue()
    with pytest.raises(tarfile.FilterError):
        await download_hub_tasks(
            [HubTaskRef(ORG, "task-a", TASK_HASH_A)], client=fake.client()
        )
    assert not hub_task_dir(HubTaskRef(ORG, "task-a", TASK_HASH_A)).exists()


async def test_transient_errors_are_retried() -> None:
    """Connection errors are retried a few times before giving up."""
    fake = FakeHub()
    fake.fail_first_n = 2
    meta = await fake.client().resolve_dataset(PackageRef(ORG, NAME, "latest"))
    assert meta.dataset_version_id == DV_ID

    fake = FakeHub()
    fake.fail_first_n = 10
    with pytest.raises(httpx.ConnectError):
        await fake.client().resolve_dataset(PackageRef(ORG, NAME, "latest"))


async def test_server_error_is_retried_then_raised() -> None:
    """5xx responses are retried and surface as ``HTTPStatusError``."""
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503)

    client = HubClient(transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        await client.resolve_task_version(ORG, "task-a", "latest")
    assert calls == 3


def test_env_overrides_for_url_and_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Harbor's env vars relocate the hub for local or private deployments."""
    monkeypatch.setenv("HARBOR_SUPABASE_URL", "https://example.test")
    monkeypatch.setenv("HARBOR_SUPABASE_PUBLISHABLE_KEY", "k")
    client = HubClient()
    assert client.base_url == "https://example.test"
    assert client.api_key == "k"
    assert HubClient().base_url == "https://example.test"
    monkeypatch.delenv("HARBOR_SUPABASE_URL")
    assert HubClient().base_url == hub.DEFAULT_HUB_URL
