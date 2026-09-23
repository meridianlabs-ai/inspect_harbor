"""A thin client for the Harbor hub (``org/name@ref`` datasets and tasks).

The hub has no dedicated HTTP API: Harbor's own client talks to a Supabase
project through PostgREST table queries, one RPC, and a storage bucket, all
readable anonymously with the publishable key. This module does the same
with ``httpx`` so inspect_harbor does not depend on the ``harbor`` package.

Verified against the live backend on 2026-09-21. Table and column names are
Harbor internals and may change without notice. The nightly registry update
resolves every hub dataset through this client, so a change to the dataset
or task-listing queries fails that job; the task-version RPC and archive
download are only exercised by evals and the opt-in parity test in
``tests/manual``.
"""

import asyncio
import json
import logging
import os
import re
import shutil
import tarfile
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from inspect_harbor._harbor.cache import cache_root
from inspect_harbor._harbor.models import ORG_NAME_PATTERN

logger = logging.getLogger(__name__)

HUB_URL_ENV = "HARBOR_SUPABASE_URL"
HUB_KEY_ENV = "HARBOR_SUPABASE_PUBLISHABLE_KEY"
TELEMETRY_OPT_OUT_ENV = "INSPECT_HARBOR_NO_TELEMETRY"
DEFAULT_HUB_URL = "https://ofhuhcpkvzjlejydnvyd.supabase.co"
DEFAULT_HUB_KEY = "sb_publishable_Z-vuQbpvpG-PStjbh4yE0Q_e-d3MTIH"
STORAGE_BUCKET = "packages"

_DATASET_VERSION_FIELDS = "id,revision,content_hash,description,yanked_at,yanked_reason"
_PACKAGE_EMBED = "package:package_id!inner(name,type,org:org_id!inner(name))"
_TASK_ROWS_SELECT = "task_version:task_version_id(content_hash,package:package_id(name,org:org_id(name)))"


class RefType(str, Enum):
    """How a ``@ref`` suffix is interpreted."""

    TAG = "tag"
    REVISION = "revision"
    DIGEST = "digest"


@dataclass(frozen=True)
class PackageRef:
    """A hub package reference ``org/name@ref``."""

    org: str
    name: str
    ref: str = "latest"

    @property
    def slug(self) -> str:
        """``org/name`` without the ref."""
        return f"{self.org}/{self.name}"

    def __str__(self) -> str:
        """``org/name@ref``."""
        return f"{self.slug}@{self.ref}"


@dataclass(frozen=True)
class HubTaskRef:
    """A pinned task version inside a hub dataset."""

    org: str
    name: str
    content_hash: str

    @property
    def slug(self) -> str:
        """``org/name``, the display name used for dataset filtering."""
        return f"{self.org}/{self.name}"

    def __str__(self) -> str:
        """``org/name@sha256:<digest>``."""
        return f"{self.slug}@sha256:{self.content_hash}"


@dataclass
class HubDatasetMetadata:
    """A resolved hub dataset version and its tasks."""

    name: str
    version: str
    description: str
    task_refs: list[HubTaskRef]
    dataset_version_id: str
    revision: int | None
    yanked_at: str | None = None
    yanked_reason: str | None = None


@dataclass
class ResolvedTaskVersion:
    """A task version resolved to its archive on the hub."""

    id: str
    archive_path: str
    content_hash: str
    revision: int | None = None
    yanked_at: str | None = None
    yanked_reason: str | None = None


class HubClient:
    """Anonymous, read-mostly client for the Harbor hub backend.

    Args:
        base_url: Supabase project URL. Defaults to ``HARBOR_SUPABASE_URL``
            or Harbor's public project.
        api_key: Publishable key. Defaults to
            ``HARBOR_SUPABASE_PUBLISHABLE_KEY`` or Harbor's public key.
        transport: Optional ``httpx`` transport (tests inject a mock).
        timeout: Per-request timeout in seconds.
    """

    page_size = 1000
    retry_attempts = 3
    retry_wait_seconds = 0.5

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = 120.0,
    ) -> None:
        """Configure the client; no connection is made until first use."""
        self.base_url = (
            base_url or os.environ.get(HUB_URL_ENV) or DEFAULT_HUB_URL
        ).rstrip("/")
        self.api_key = api_key or os.environ.get(HUB_KEY_ENV) or DEFAULT_HUB_KEY
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "apikey": self.api_key,
                "Authorization": f"Bearer {self.api_key}",
            },
            transport=transport,
            timeout=timeout,
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def resolve_dataset(self, ref: PackageRef) -> HubDatasetMetadata:
        """Resolve a dataset ref to its version and pinned task list.

        Raises:
            ValueError: When the dataset or ref does not exist, or some of its
                tasks are not readable anonymously.
        """
        ref_type, value = classify_ref(ref.ref)
        common = {
            "package.name": f"eq.{ref.name}",
            "package.type": "eq.dataset",
            "package.org.name": f"eq.{ref.org}",
            "limit": "1",
        }
        if ref_type is RefType.TAG:
            rows = await self._select(
                "dataset_version_tag",
                {
                    "select": (
                        f"dataset_version:dataset_version_id({_DATASET_VERSION_FIELDS}),"
                        f"{_PACKAGE_EMBED}"
                    ),
                    "tag": f"eq.{value}",
                    **common,
                },
            )
            version_row = rows[0]["dataset_version"] if rows else None
        else:
            column = "revision" if ref_type is RefType.REVISION else "content_hash"
            rows = await self._select(
                "dataset_version",
                {
                    "select": f"{_DATASET_VERSION_FIELDS},{_PACKAGE_EMBED}",
                    column: f"eq.{value}",
                    **common,
                },
            )
            version_row = rows[0] if rows else None
        if not version_row:
            raise ValueError(f"Dataset not found on the Harbor hub: {ref}")

        if version_row.get("yanked_at"):
            reason = version_row.get("yanked_reason")
            logger.warning(
                "Dataset version %s is yanked%s. Consider pinning a different revision.",
                ref,
                f": {reason}" if reason else "",
            )

        task_refs = await self.list_dataset_tasks(version_row["id"], label=str(ref))
        return HubDatasetMetadata(
            name=ref.slug,
            version=f"sha256:{version_row['content_hash']}",
            description=version_row.get("description") or "",
            task_refs=task_refs,
            dataset_version_id=version_row["id"],
            revision=version_row.get("revision"),
            yanked_at=version_row.get("yanked_at"),
            yanked_reason=version_row.get("yanked_reason"),
        )

    async def list_dataset_tasks(
        self, dataset_version_id: str, label: str = ""
    ) -> list[HubTaskRef]:
        """All task versions in a dataset version, in hub order.

        Raises:
            ValueError: When some task versions are hidden from anonymous
                readers (the hub returns them as null rows), naming the count.
        """
        refs: list[HubTaskRef] = []
        hidden = 0
        offset = 0
        while True:
            rows = await self._select(
                "dataset_version_task",
                {
                    "select": _TASK_ROWS_SELECT,
                    "dataset_version_id": f"eq.{dataset_version_id}",
                    "order": "task_version_id",
                    "limit": str(self.page_size),
                    "offset": str(offset),
                },
            )
            for row in rows:
                tv = row.get("task_version")
                if not tv:
                    hidden += 1
                    continue
                refs.append(
                    HubTaskRef(
                        org=tv["package"]["org"]["name"],
                        name=tv["package"]["name"],
                        content_hash=tv["content_hash"],
                    )
                )
            if len(rows) < self.page_size:
                break
            offset += self.page_size
        if hidden:
            raise ValueError(
                f"Dataset {label or dataset_version_id} references {hidden} task "
                "version(s) that are not available anonymously (private or hidden)."
            )
        return refs

    async def resolve_task_version(
        self, org: str, name: str, ref: str | None
    ) -> ResolvedTaskVersion:
        """Resolve a task ref (tag, revision, or digest) to its archive.

        Raises:
            ValueError: When the task version does not exist.
        """
        ref = ref or "latest"
        response = await self._request(
            "POST",
            "/rest/v1/rpc/resolve_task_version",
            json={"p_org": org, "p_name": name, "p_ref": ref},
        )
        row = response.json()
        if not row:
            raise ValueError(
                f"Task version not found on the Harbor hub: {org}/{name}@{ref}"
            )
        if row.get("yanked_at"):
            reason = row.get("yanked_reason")
            logger.warning(
                "Task version %s/%s@%s is yanked%s",
                org,
                name,
                ref,
                f": {reason}" if reason else "",
            )
        return ResolvedTaskVersion(
            id=row["id"],
            archive_path=row["archive_path"],
            content_hash=row["content_hash"],
            revision=row.get("revision"),
            yanked_at=row.get("yanked_at"),
            yanked_reason=row.get("yanked_reason"),
        )

    async def download_archive(self, archive_path: str, dest: Path) -> None:
        """Download a task archive from the hub's storage bucket to ``dest``."""
        response = await self._request(
            "GET", f"/storage/v1/object/authenticated/{STORAGE_BUCKET}/{archive_path}"
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(response.content)

    async def record_task_download(self, task_version_id: str) -> None:
        """Increment the hub's download counter for a task version.

        Mirrors what Harbor does after a cache miss so dataset authors see
        inspect_harbor usage. Never raises; failures are logged at debug.
        """
        await self._record_download(
            "task_version_download", task_version_id=task_version_id
        )

    async def record_dataset_download(self, dataset_version_id: str) -> None:
        """Increment the hub's download counter for a dataset version (see above)."""
        await self._record_download(
            "dataset_version_download", dataset_version_id=dataset_version_id
        )

    async def _record_download(self, table: str, **row: str) -> None:
        if not _telemetry_enabled():
            return
        try:
            response = await self._http.post(
                f"/rest/v1/{table}", json=row, headers={"Prefer": "return=minimal"}
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.debug("Failed to record download in %s: %s", table, exc)

    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        async for attempt in AsyncRetrying(
            retry=retry_if_exception(_is_retryable),
            stop=stop_after_attempt(self.retry_attempts),
            wait=wait_exponential(
                multiplier=self.retry_wait_seconds,
                min=self.retry_wait_seconds,
                max=8 * self.retry_wait_seconds,
            ),
            reraise=True,
        ):
            with attempt:
                response = await self._http.request(method, url, **kwargs)
                response.raise_for_status()
                return response
        raise AssertionError("unreachable")  # pragma: no cover

    async def _select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        response = await self._request("GET", f"/rest/v1/{table}", params=params)
        return response.json()


def classify_ref(ref: str | None) -> tuple[RefType, str]:
    """Split a ref into its type and bare value.

    ``None``, ``""`` and ``"latest"`` are the ``latest`` tag; digits are a
    revision number; ``sha256:<hex>`` is a digest (returned lower-cased and
    without the prefix); anything else is a tag.
    """
    if not ref or ref == "latest":
        return RefType.TAG, "latest"
    if ref.isdigit():
        return RefType.REVISION, ref
    if ref.startswith("sha256:"):
        return RefType.DIGEST, ref.removeprefix("sha256:").lower()
    return RefType.TAG, ref


def parse_package_ref(slug: str) -> PackageRef:
    """Parse ``org/name`` or ``org/name@ref`` (ref defaults to ``latest``).

    Raises:
        ValueError: When the name is not in ``org/name`` form.
    """
    name, _, ref = slug.partition("@")
    if not re.match(ORG_NAME_PATTERN, name) or ".." in name:
        raise ValueError(
            f"Package name must be in 'org/name' format (got {slug!r}); allowed "
            "characters are letters, digits, '.', '_' and '-'."
        )
    org, short = name.split("/", 1)
    return PackageRef(org=org, name=short, ref=ref or "latest")


async def resolve_hub_dataset(
    slug: str, client: HubClient | None = None
) -> HubDatasetMetadata:
    """Resolve ``org/name[@ref]`` to its dataset version and task list."""
    ref = parse_package_ref(slug)
    if client is not None:
        return await client.resolve_dataset(ref)
    client = HubClient()
    try:
        return await client.resolve_dataset(ref)
    finally:
        await client.aclose()


def hub_task_dir(ref: HubTaskRef) -> Path:
    """Cache location of a pinned hub task: content-addressed by digest."""
    return cache_root() / "hub" / ref.org / ref.name / ref.content_hash


def is_cached(target: Path) -> bool:
    """Whether a cache directory holds a complete task (a ``task.toml``)."""
    return (target / "task.toml").is_file()


async def download_hub_tasks(
    task_refs: list[HubTaskRef],
    overwrite: bool = False,
    client: HubClient | None = None,
    max_concurrency: int = 100,
) -> list[Path]:
    """Download pinned hub tasks into the cache; returns paths in input order.

    Tasks are content-addressed, so a complete cached directory is reused
    unless ``overwrite`` is set. Concurrent downloads of the same task, from
    this or another process, are safe: each extracts into its own staging
    directory and the first to finish wins.

    ``max_concurrency`` defaults to 100, which is httpx's connection-pool
    ceiling and what Harbor uses against the same backend. Measured on 100
    aider tasks: 8 in flight took 11.5 s, 32 took 3.7 s, 100 took 2.2 s with
    no throttling, so higher values could not help and lower ones cost time
    on large datasets.
    """
    targets = {ref: hub_task_dir(ref) for ref in task_refs}
    missing = [
        ref for ref, target in targets.items() if overwrite or not is_cached(target)
    ]
    if missing:
        own_client = client is None
        client = client or HubClient()
        semaphore = asyncio.Semaphore(max_concurrency)
        try:
            async with asyncio.TaskGroup() as tg:
                for ref in missing:
                    tg.create_task(
                        _download_one(client, ref, targets[ref], overwrite, semaphore)
                    )
        except* Exception as group:
            first, *others = group.exceptions
            for other in others:
                logger.warning("Additional hub download failure: %r", other)
            raise first from None
        finally:
            if own_client:
                await client.aclose()
    return [targets[ref] for ref in task_refs]


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == 429 or exc.response.status_code >= 500
    return False


def _telemetry_enabled() -> bool:
    return not os.environ.get(TELEMETRY_OPT_OUT_ENV)


def _sidecar_path(target: Path) -> Path:
    return target.parent / f"{target.name}.json"


def _extract_archive(archive: Path, target: Path, overwrite: bool) -> bool:
    """Extract into a private staging dir, then swap it into place.

    Returns ``False`` when another writer completed ``target`` first and this
    extraction was discarded (only when not overwriting).

    Raises:
        ValueError: When the archive does not contain a ``task.toml`` at its
            root, so a bad archive never becomes a cached "task".
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(dir=target.parent, prefix=f".{target.name}."))
    staged = staging / "task"
    try:
        staged.mkdir()
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(path=staged, filter="data")
        if not (staged / "task.toml").is_file():
            raise ValueError(
                f"Hub archive for {target.name} has no task.toml at its root"
            )
        if target.exists():
            if not overwrite and is_cached(target):
                return False
            old = staging / "old"
            target.rename(old)
        try:
            staged.rename(target)
        except OSError:
            # Lost a race: someone else renamed a complete task into place.
            if is_cached(target):
                return False
            raise
        return True
    finally:
        shutil.rmtree(staging, ignore_errors=True)


async def _download_one(
    client: HubClient,
    ref: HubTaskRef,
    target: Path,
    overwrite: bool,
    semaphore: asyncio.Semaphore,
) -> None:
    async with semaphore:
        try:
            resolved = await client.resolve_task_version(
                ref.org, ref.name, f"sha256:{ref.content_hash}"
            )
            with tempfile.TemporaryDirectory() as tmp:
                archive = Path(tmp) / "dist.tar.gz"
                await client.download_archive(resolved.archive_path, archive)
                written = _extract_archive(archive, target, overwrite)
        except Exception as exc:
            exc.add_note(f"while downloading hub task {ref}")
            raise
        if not written:
            return
        sidecar = {
            **asdict(ref),
            "task_version_id": resolved.id,
            "revision": resolved.revision,
            "downloaded_at": datetime.now(UTC).isoformat(),
        }
        _sidecar_path(target).write_text(json.dumps(sidecar))
        await client.record_task_download(resolved.id)
