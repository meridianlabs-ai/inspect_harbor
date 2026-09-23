"""Tests for the hub client (Harbor's Supabase-backed package registry)."""

import io
import json
import tarfile
from concurrent.futures import ThreadPoolExecutor
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
HASH_A, HASH_B = "a" * 64, "b" * 64
REF_A, REF_B = HubTaskRef(ORG, "task-a", HASH_A), HubTaskRef(ORG, "task-b", HASH_B)


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Temp cache, telemetry on, no retry waits, default hub URL and key."""
    cache = tmp_path / "cache"
    monkeypatch.setenv("INSPECT_HARBOR_CACHE_DIR", str(cache))
    for var in (
        "INSPECT_HARBOR_NO_TELEMETRY",
        "HARBOR_SUPABASE_URL",
        "HARBOR_SUPABASE_PUBLISHABLE_KEY",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(HubClient, "retry_wait_seconds", 0.0)
    return cache


def archive_bytes(members: dict[str, str]) -> bytes:
    """A gzip tarball with the given ``path: content`` members."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, content in members.items():
            data = content.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def task_archive(instruction: str) -> bytes:
    """A minimal complete task archive."""
    return archive_bytes(
        {
            "task.toml": '[environment]\ndocker_image = "x"\n',
            "instruction.md": instruction,
            "environment/Dockerfile": "FROM scratch\n",
            "tests/test.sh": "#!/bin/bash\n",
        }
    )


class FakeHub:
    """A scripted Supabase backend behind ``httpx.MockTransport``.

    Attributes are the knobs tests turn: ``dataset`` (``None`` for not
    found), ``tasks`` (rows for the task listing), ``archives`` keyed by
    digest, ``fail_first_n``/``fail_with`` for transient failures, and
    ``telemetry_status``.
    """

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.dataset: dict[str, Any] | None = {
            "id": DV_ID,
            "revision": 3,
            "content_hash": DV_HASH,
            "description": "A benchmark",
            "yanked_at": None,
            "yanked_reason": None,
        }
        self.tasks: list[dict[str, Any]] = [self.task_row(REF_A), self.task_row(REF_B)]
        self.archives = {HASH_A: task_archive("task a"), HASH_B: task_archive("task b")}
        self.fail_first_n = 0
        self.fail_with: Exception | int = httpx.ConnectError("boom")
        self.telemetry_status = 201
        self.task_yanked_reason: str | None = None

    @staticmethod
    def task_row(ref: HubTaskRef) -> dict[str, Any]:
        """A ``dataset_version_task`` row for ``ref``."""
        return {
            "task_version": {
                "content_hash": ref.content_hash,
                "package": {"name": ref.name, "org": {"name": ref.org}},
            }
        }

    def client(self) -> HubClient:
        """A ``HubClient`` wired to this fake."""
        return HubClient(transport=httpx.MockTransport(self.handler))

    def handler(self, request: httpx.Request) -> httpx.Response:
        """Route a request to the scripted table, RPC, or storage response."""
        self.requests.append(request)
        if self.fail_first_n > 0:
            self.fail_first_n -= 1
            if isinstance(self.fail_with, int):
                return httpx.Response(self.fail_with)
            raise self.fail_with
        path, params = request.url.path, request.url.params
        package = {"name": NAME, "type": "dataset", "org": {"name": ORG}}
        if path.endswith("/rest/v1/dataset_version_tag"):
            rows = (
                [{"dataset_version": self.dataset, "package": package}]
                if self.dataset
                else []
            )
            return httpx.Response(200, json=rows)
        if path.endswith("/rest/v1/dataset_version"):
            rows = [{**self.dataset, "package": package}] if self.dataset else []
            return httpx.Response(200, json=rows)
        if path.endswith("/rest/v1/dataset_version_task"):
            assert params["order"] == "task_version_id"
            offset, limit = int(params["offset"]), int(params["limit"])
            return httpx.Response(200, json=self.tasks[offset : offset + limit])
        if path.endswith("/rest/v1/rpc/resolve_task_version"):
            body = json.loads(request.content)
            digest = body["p_ref"].removeprefix("sha256:")
            if digest not in self.archives:
                return httpx.Response(200, content=b"null")
            return httpx.Response(
                200,
                json={
                    "id": f"tv-{digest[0]}",
                    "archive_path": f"packages/{body['p_org']}/{body['p_name']}/{digest}/dist.tar.gz",
                    "content_hash": digest,
                    "revision": 1,
                    "yanked_at": "2026-01-01" if self.task_yanked_reason else None,
                    "yanked_reason": self.task_yanked_reason,
                },
            )
        if "/storage/v1/object/authenticated/packages/" in path:
            digest = path.rsplit("/", 2)[-2]
            if digest in self.archives:
                return httpx.Response(200, content=self.archives[digest])
            return httpx.Response(400, json={"error": "not found"})
        if path.endswith(
            ("/rest/v1/task_version_download", "/rest/v1/dataset_version_download")
        ):
            return httpx.Response(self.telemetry_status)
        raise AssertionError(f"unexpected request: {request.method} {request.url}")


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


@pytest.mark.parametrize("slug", ["bench", "a/b/c", "/bench", "a/../b"])
def test_parse_package_ref_rejects_bad_names(slug: str) -> None:
    """Names must be ``org/name``."""
    with pytest.raises(ValueError, match="org/name"):
        parse_package_ref(slug)


@pytest.mark.parametrize(
    "ref,expected",
    [
        (None, (RefType.TAG, "latest")),
        ("latest", (RefType.TAG, "latest")),
        ("stable", (RefType.TAG, "stable")),
        ("7", (RefType.REVISION, "7")),
        ("sha256:abc", (RefType.DIGEST, "abc")),
        ("sha256:ABCDEF", (RefType.DIGEST, "abcdef")),
    ],
)
def test_classify_ref(ref: str | None, expected: tuple[RefType, str]) -> None:
    """Refs are tags, integer revisions, or lower-cased ``sha256:`` digests."""
    assert classify_ref(ref) == expected


# --- dataset resolution --------------------------------------------------


async def test_resolve_dataset_by_tag() -> None:
    """A tag ref queries ``dataset_version_tag`` and lists the tasks."""
    fake = FakeHub()
    meta = await fake.client().resolve_dataset(parse_package_ref(f"{ORG}/{NAME}"))
    assert (meta.name, meta.version) == (f"{ORG}/{NAME}", f"sha256:{DV_HASH}")
    assert (meta.description, meta.dataset_version_id, meta.revision) == (
        "A benchmark",
        DV_ID,
        3,
    )
    assert meta.task_refs == [REF_A, REF_B]

    tag_req, tasks_req = fake.requests
    assert tag_req.url.path == "/rest/v1/dataset_version_tag"
    assert tag_req.url.params["tag"] == "eq.latest"
    assert tag_req.url.params["package.name"] == f"eq.{NAME}"
    assert tag_req.url.params["package.org.name"] == f"eq.{ORG}"
    assert tag_req.url.params["package.type"] == "eq.dataset"
    assert tag_req.headers["apikey"] == hub.DEFAULT_HUB_KEY
    assert tag_req.headers["authorization"] == f"Bearer {hub.DEFAULT_HUB_KEY}"
    assert tasks_req.url.path == "/rest/v1/dataset_version_task"
    assert tasks_req.url.params["dataset_version_id"] == f"eq.{DV_ID}"


@pytest.mark.parametrize(
    "ref,column,value",
    [("3", "revision", "eq.3"), (f"sha256:{DV_HASH}", "content_hash", f"eq.{DV_HASH}")],
)
async def test_resolve_dataset_by_revision_or_digest(
    ref: str, column: str, value: str
) -> None:
    """Revision and digest refs query ``dataset_version`` directly (via the slug helper)."""
    fake = FakeHub()
    meta = await resolve_hub_dataset(f"{ORG}/{NAME}@{ref}", client=fake.client())
    assert meta.dataset_version_id == DV_ID
    req = fake.requests[0]
    assert req.url.path == "/rest/v1/dataset_version"
    assert req.url.params[column] == value
    assert req.url.params["package.name"] == f"eq.{NAME}"


async def test_resolve_dataset_pages_through_tasks() -> None:
    """Task listing follows PostgREST paging until a short page."""
    fake = FakeHub()
    fake.tasks = [
        FakeHub.task_row(HubTaskRef(ORG, f"t{i}", str(i) * 64)) for i in range(5)
    ]
    client = fake.client()
    client.page_size = 2
    meta = await client.resolve_dataset(PackageRef(ORG, NAME, "latest"))
    assert len(meta.task_refs) == 5
    offsets = [r.url.params["offset"] for r in fake.requests if "task" in r.url.path]
    assert offsets == ["0", "2", "4"]


async def test_not_found_names_the_ref() -> None:
    """Unknown datasets and task versions raise a ``ValueError`` naming the ref."""
    fake = FakeHub()
    fake.dataset = None
    with pytest.raises(ValueError, match=f"{ORG}/{NAME}@9"):
        await fake.client().resolve_dataset(PackageRef(ORG, NAME, "9"))
    with pytest.raises(ValueError, match="acme/nope@latest"):
        await fake.client().resolve_task_version(ORG, "nope", "latest")


async def test_resolve_dataset_yanked_warns(caplog: pytest.LogCaptureFixture) -> None:
    """A yanked dataset version still resolves but is logged as a warning."""
    fake = FakeHub()
    assert fake.dataset is not None
    fake.dataset.update(yanked_at="2026-01-01T00:00:00Z", yanked_reason="broken")
    with caplog.at_level("WARNING", logger="inspect_harbor._harbor.hub"):
        meta = await fake.client().resolve_dataset(PackageRef(ORG, NAME, "latest"))
    assert meta.yanked_at == "2026-01-01T00:00:00Z"
    assert "yanked: broken" in caplog.text


async def test_hidden_task_rows_raise_a_clear_error() -> None:
    """Task versions hidden from anonymous readers come back as null rows."""
    fake = FakeHub()
    fake.tasks = [FakeHub.task_row(REF_A), {"task_version": None}]
    with pytest.raises(ValueError, match=f"{ORG}/{NAME}@latest.*1 task version"):
        await fake.client().resolve_dataset(PackageRef(ORG, NAME, "latest"))


# --- task versions and downloads -----------------------------------------


async def test_resolve_task_version_rpc() -> None:
    """The RPC is called with ``p_org``, ``p_name``, ``p_ref``."""
    fake = FakeHub()
    resolved = await fake.client().resolve_task_version(
        ORG, "task-a", f"sha256:{HASH_A}"
    )
    assert resolved.id == "tv-a"
    assert resolved.archive_path.endswith(f"{HASH_A}/dist.tar.gz")
    req = fake.requests[0]
    assert (req.method, req.url.path) == ("POST", "/rest/v1/rpc/resolve_task_version")
    assert json.loads(req.content) == {
        "p_org": ORG,
        "p_name": "task-a",
        "p_ref": f"sha256:{HASH_A}",
    }


async def test_download_hub_tasks_end_to_end(isolated_env: Path) -> None:
    """Tasks are resolved, downloaded, extracted, recorded, and then cached."""
    fake = FakeHub()
    paths = await download_hub_tasks([REF_A, REF_B], client=fake.client())
    assert paths == [hub_task_dir(REF_A), hub_task_dir(REF_B)]
    assert paths[0] == isolated_env / "hub" / ORG / "task-a" / HASH_A
    assert (paths[0] / "instruction.md").read_text() == "task a"
    assert (paths[1] / "tests" / "test.sh").exists()
    sidecar = json.loads((paths[0].parent / f"{HASH_A}.json").read_text())
    assert (sidecar["org"], sidecar["name"], sidecar["task_version_id"]) == (
        ORG,
        "task-a",
        "tv-a",
    )

    telemetry = [
        r for r in fake.requests if r.url.path.endswith("task_version_download")
    ]
    assert len(telemetry) == 2
    assert telemetry[0].headers["prefer"] == "return=minimal"
    assert json.loads(telemetry[0].content) == {"task_version_id": "tv-a"}

    # Second call is served from cache: no further requests at all.
    before = len(fake.requests)
    assert await download_hub_tasks([REF_A, REF_B], client=fake.client()) == paths
    assert len(fake.requests) == before


async def test_overwrite_refetches_and_telemetry_opt_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``overwrite`` refetches; the opt-out env var suppresses the counter."""
    fake = FakeHub()
    [path] = await download_hub_tasks([REF_A], client=fake.client())
    (path / "instruction.md").write_text("tampered")

    monkeypatch.setenv("INSPECT_HARBOR_NO_TELEMETRY", "1")
    fake.requests.clear()
    [again] = await download_hub_tasks([REF_A], overwrite=True, client=fake.client())
    assert again == path
    assert (path / "instruction.md").read_text() == "task a"
    assert not any(r.url.path.endswith("task_version_download") for r in fake.requests)


async def test_telemetry_failure_is_swallowed(caplog: pytest.LogCaptureFixture) -> None:
    """Failing download counters, for tasks or datasets, never fail the caller."""
    fake = FakeHub()
    fake.telemetry_status = 500
    client = fake.client()
    with caplog.at_level("DEBUG", logger="inspect_harbor._harbor.hub"):
        [path] = await download_hub_tasks([REF_A], client=client)
        await client.record_dataset_download(DV_ID)
    assert (path / "task.toml").exists()
    assert "Failed to record download in task_version_download" in caplog.text
    assert "Failed to record download in dataset_version_download" in caplog.text
    posts = [
        r for r in fake.requests if r.url.path.endswith("dataset_version_download")
    ]
    assert json.loads(posts[0].content) == {"dataset_version_id": DV_ID}


@pytest.mark.parametrize("junk", [None, "tests"])
async def test_incomplete_cache_dir_is_not_a_hit(junk: str | None) -> None:
    """An empty or partial cache directory (no task.toml) is re-downloaded."""
    fake = FakeHub()
    target = hub_task_dir(REF_A)
    (target / junk if junk else target).mkdir(parents=True)
    [path] = await download_hub_tasks([REF_A], client=fake.client())
    assert path == target and (target / "task.toml").exists()
    assert any(r.url.path.endswith("resolve_task_version") for r in fake.requests)


@pytest.mark.parametrize(
    "members,exc,match",
    [
        ({"README.md": "x"}, ValueError, "no task.toml"),
        ({"../escape.txt": "x"}, tarfile.FilterError, None),
    ],
)
async def test_bad_archives_are_rejected_and_not_cached(
    members: dict[str, str], exc: type[Exception], match: str | None
) -> None:
    """Incomplete or path-escaping archives fail, name the task, and leave nothing."""
    fake = FakeHub()
    fake.archives[HASH_A] = archive_bytes(members)
    with pytest.raises(exc, match=match) as info:
        await download_hub_tasks([REF_A], client=fake.client())
    assert any(str(REF_A) in note for note in info.value.__notes__)
    assert not hub_task_dir(REF_A).exists()
    assert not list(hub_task_dir(REF_A).parent.glob(".*"))


async def test_concurrent_extractions_of_one_task_are_safe(tmp_path: Path) -> None:
    """Several writers racing on one target all succeed; the result is complete."""
    archive = tmp_path / "dist.tar.gz"
    archive.write_bytes(task_archive("racy"))
    target = hub_task_dir(REF_A)
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(
            pool.map(lambda _: hub._extract_archive(archive, target, False), range(6))
        )
    assert results.count(True) >= 1
    assert (target / "instruction.md").read_text() == "racy"
    assert not list(target.parent.glob(".*"))


@pytest.mark.parametrize(
    "fail_first_n,fail_with,raises",
    [
        (2, httpx.ConnectError("boom"), None),
        (10, httpx.ConnectError("boom"), httpx.ConnectError),
        (3, 503, httpx.HTTPStatusError),
    ],
)
async def test_transient_errors_are_retried(
    fail_first_n: int, fail_with: Exception | int, raises: type[Exception] | None
) -> None:
    """Connection errors and 5xx are retried three times, then raised."""
    fake = FakeHub()
    fake.fail_first_n, fake.fail_with = fail_first_n, fail_with
    if raises is None:
        meta = await fake.client().resolve_dataset(PackageRef(ORG, NAME, "latest"))
        assert meta.dataset_version_id == DV_ID
    else:
        with pytest.raises(raises):
            await fake.client().resolve_dataset(PackageRef(ORG, NAME, "latest"))


def test_env_overrides_for_url_and_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Harbor's env vars relocate the hub for local or private deployments."""
    monkeypatch.setenv("HARBOR_SUPABASE_URL", "https://example.test/")
    monkeypatch.setenv("HARBOR_SUPABASE_PUBLISHABLE_KEY", "k")
    client = HubClient()
    assert (client.base_url, client.api_key) == ("https://example.test", "k")
    monkeypatch.delenv("HARBOR_SUPABASE_URL")
    assert HubClient().base_url == hub.DEFAULT_HUB_URL
