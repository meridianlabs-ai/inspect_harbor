"""Download tasks that live in git repositories.

Follows the approach Harbor uses: one shallow, blob-less clone per
repository with a sparse checkout of just the requested task paths, then a
copy of each task directory into the local cache.
"""

import asyncio
import logging
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from inspect_harbor._harbor.cache import cache_root, stable_key

logger = logging.getLogger(__name__)

_GIT_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$|^[0-9a-fA-F]{64}$")
_lfs_warning_logged = False


@dataclass(frozen=True)
class GitTaskSpec:
    """A task directory inside a git repository."""

    git_url: str
    path: PurePosixPath
    git_commit_id: str | None = None

    @property
    def name(self) -> str:
        """Display name used for dataset filtering: the last path component."""
        return self.path.name


def is_resolved_commit(commit: str | None) -> bool:
    """Whether ``commit`` is a full sha (so a cached copy can be trusted)."""
    return commit is not None and _GIT_COMMIT_RE.match(commit) is not None


def clone_args(git_url: str, dest: Path) -> list[str]:
    """Arguments for the initial shallow, no-checkout clone.

    ``--filter=blob:none`` defers blob fetches to git's partial-clone
    protocol. Hugging Face's git server does not implement it, and a later
    ``git checkout`` on such a clone fails, so the filter is skipped there.
    """
    args = ["git", "clone"]
    if "huggingface.co" not in git_url:
        args.append("--filter=blob:none")
    args += ["--depth", "1", "--no-checkout", git_url, str(dest)]
    return args


def target_dir(spec: GitTaskSpec) -> Path:
    """Where ``spec`` is cached: keyed by URL, commit, and path."""
    key = stable_key(spec.git_url, spec.git_commit_id or "", spec.path.as_posix())
    return cache_root() / "git" / key / spec.path.name


async def download_git_tasks(
    specs: list[GitTaskSpec], overwrite: bool = False
) -> list[Path]:
    """Download the given tasks and return their cached paths in input order.

    A cached copy is reused only when the spec pins a full commit sha and
    the directory is non-empty; unpinned (HEAD) specs are always refreshed.

    Raises:
        RuntimeError: When a git command fails.
    """
    targets = {spec: target_dir(spec) for spec in specs}
    to_fetch = {
        spec: target
        for spec, target in targets.items()
        if overwrite
        or not is_resolved_commit(spec.git_commit_id)
        or not target.is_dir()
        or not any(target.iterdir())
    }

    by_url: dict[str, list[tuple[GitTaskSpec, Path]]] = {}
    for spec, target in to_fetch.items():
        by_url.setdefault(spec.git_url, []).append((spec, target))
    for git_url, group in by_url.items():
        await _download_from_repo(git_url, group)

    return [targets[spec] for spec in specs]


async def _run_git(
    *args: str, cwd: Path | None = None, input: bytes | None = None
) -> str:
    process = await asyncio.create_subprocess_exec(
        *args,
        cwd=cwd,
        stdin=asyncio.subprocess.PIPE if input is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate(input)
    if process.returncode != 0:
        raise RuntimeError(
            f"{' '.join(args)} failed with exit code {process.returncode}:\n"
            f"{stderr.decode(errors='replace').strip()}"
        )
    return stdout.decode(errors="replace").strip()


def _repo_uses_lfs(repo_dir: Path) -> bool:
    gitattributes = repo_dir / ".gitattributes"
    try:
        return gitattributes.exists() and "filter=lfs" in gitattributes.read_text()
    except OSError:
        return False


async def _pull_lfs_files(repo_dir: Path, paths: list[PurePosixPath]) -> None:
    global _lfs_warning_logged
    if not _repo_uses_lfs(repo_dir):
        return
    if not shutil.which("git-lfs"):
        if not _lfs_warning_logged:
            logger.warning(
                "git-lfs is not installed; LFS-tracked task files will not be "
                "downloaded."
            )
            _lfs_warning_logged = True
        return
    include = ",".join(f"{p.as_posix()}/**" for p in paths)
    await _run_git("git", "lfs", "pull", f"--include={include}", cwd=repo_dir)


def _copy_task(source: Path, target: Path) -> None:
    if not source.is_dir():
        raise FileNotFoundError(f"Task path {source.name!r} not found in repository")
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


async def _download_from_repo(
    git_url: str, specs: list[tuple[GitTaskSpec, Path]]
) -> None:
    """Clone ``git_url`` once and copy every requested task into place."""
    with tempfile.TemporaryDirectory() as tmp:
        repo_dir = Path(tmp) / "repo"
        await _run_git(*clone_args(git_url, repo_dir))
        sparse_paths = "\n".join(sorted({s.path.as_posix() for s, _ in specs}))
        await _run_git(
            "git",
            "sparse-checkout",
            "set",
            "--no-cone",
            "--stdin",
            cwd=repo_dir,
            input=sparse_paths.encode("utf-8"),
        )

        by_commit: dict[str | None, list[tuple[GitTaskSpec, Path]]] = {}
        for spec, target in specs:
            by_commit.setdefault(spec.git_commit_id, []).append((spec, target))

        for commit, group in by_commit.items():
            if commit is None:
                await _run_git("git", "checkout", cwd=repo_dir)
            else:
                await _run_git(
                    "git", "fetch", "--depth", "1", "origin", commit, cwd=repo_dir
                )
                await _run_git("git", "checkout", commit, cwd=repo_dir)
            await _pull_lfs_files(repo_dir, [s.path for s, _ in group])
            for spec, target in group:
                _copy_task(repo_dir / spec.path, target)
