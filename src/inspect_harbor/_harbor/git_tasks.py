"""Download tasks that live in git repositories.

Follows the approach Harbor uses: one shallow, blob-less clone per
repository with a sparse checkout of just the requested task paths, then a
copy of each task directory into the local cache. Copies are staged and
renamed into place, and symlinks are materialised only when they stay inside
the task, so a repository cannot pull host files into the cache.
"""

import asyncio
import logging
import re
import shutil
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from inspect_harbor._harbor.cache import cache_root, stable_key

logger = logging.getLogger(__name__)

_GIT_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$|^[0-9a-fA-F]{64}$")
_URL_USERINFO_RE = re.compile(r"(?<=://)[^/@\s]+@")
_lfs_warning_logged = False


@dataclass(frozen=True)
class GitTaskSpec:
    """A task directory inside a git repository.

    Raises:
        ValueError: When ``path`` is absolute, empty, or contains ``..``.
    """

    git_url: str
    path: PurePosixPath
    git_commit_id: str | None = None

    def __post_init__(self) -> None:
        """Reject paths that could escape the repository checkout."""
        if self.path.is_absolute() or not self.path.parts or ".." in self.path.parts:
            raise ValueError(
                f"Git task path must be relative to the repository and must not "
                f"contain '..': {self.path.as_posix()!r}"
            )

    @property
    def name(self) -> str:
        """Display name used for dataset filtering: the last path component."""
        return self.path.name

    def describe(self) -> str:
        """``url@commit:path`` for error messages, with credentials redacted."""
        return f"{redact_url(self.git_url)}@{self.git_commit_id or 'HEAD'}:{self.path}"


def is_resolved_commit(commit: str | None) -> bool:
    """Whether ``commit`` is a full sha (so a cached copy can be trusted)."""
    return commit is not None and _GIT_COMMIT_RE.match(commit) is not None


def redact_url(url: str) -> str:
    """Strip any ``user:token@`` from a URL before it reaches logs or errors."""
    return _URL_USERINFO_RE.sub("***@", url)


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


def is_cached(target: Path) -> bool:
    """Whether a cache directory holds a complete task (a ``task.toml``)."""
    return (target / "task.toml").is_file()


async def download_git_tasks(
    specs: list[GitTaskSpec], overwrite: bool = False
) -> list[Path]:
    """Download the given tasks and return their cached paths in input order.

    A cached copy is reused only when the spec pins a full commit sha and
    the directory holds a complete task; unpinned (HEAD) specs are always
    refreshed.

    Raises:
        RuntimeError: When a git command fails.
        ValueError: When the task directory contains links that escape it.
    """
    targets = {spec: target_dir(spec) for spec in specs}
    to_fetch = {
        spec: target
        for spec, target in targets.items()
        if overwrite
        or not is_resolved_commit(spec.git_commit_id)
        or not is_cached(target)
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
        command = " ".join(redact_url(a) for a in args)
        raise RuntimeError(
            f"{command} failed with exit code {process.returncode}:\n"
            f"{redact_url(stderr.decode(errors='replace').strip())}"
        )
    return stdout.decode(errors="replace").strip()


def _repo_uses_lfs(repo_dir: Path) -> bool:
    gitattributes = repo_dir / ".gitattributes"
    if gitattributes.is_symlink() or not gitattributes.is_file():
        return False
    try:
        return "filter=lfs" in gitattributes.read_text()
    except OSError as exc:
        logger.warning("Could not read %s (%s); skipping LFS pull", gitattributes, exc)
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


def _materialize_tree(source_root: Path, destination: Path) -> None:
    """Copy a task tree, resolving symlinks that stay inside it.

    Ported from Harbor: links must be relative, resolve inside the task, and
    point at regular files or directories. Anything else is rejected so a
    repository cannot smuggle host files into the cache.
    """
    source_root = source_root.resolve(strict=True)

    def copy_entry(path: Path, dest: Path, active_dirs: frozenset[Path]) -> None:
        relative = path.relative_to(source_root) if path != source_root else Path(".")
        if path.is_symlink() and path.readlink().is_absolute():
            raise ValueError(f"Git task links must be relative: {relative}")
        try:
            resolved = path.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ValueError(f"Invalid git task link: {relative}") from exc
        if not resolved.is_relative_to(source_root):
            raise ValueError(f"Git task links must stay within the task: {relative}")
        mode = resolved.stat().st_mode
        if stat.S_ISDIR(mode):
            if resolved in active_dirs:
                raise ValueError(f"Cyclic git task directory: {relative}")
            dest.mkdir()
            for child in sorted(resolved.iterdir()):
                copy_entry(child, dest / child.name, active_dirs | {resolved})
            shutil.copystat(resolved, dest)
        elif stat.S_ISREG(mode):
            shutil.copy2(resolved, dest)
        else:
            raise ValueError(f"Unsupported git task entry: {relative}")

    copy_entry(source_root, destination, frozenset())


def _copy_task(repo_dir: Path, spec: GitTaskSpec, target: Path) -> None:
    """Stage a validated copy of the task and swap it into ``target``."""
    source = repo_dir / spec.path
    current = repo_dir
    for part in spec.path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(
                f"Git task paths must not contain symlinks: {spec.describe()}"
            )
    if not source.is_dir():
        raise FileNotFoundError(
            f"Task directory not found in repository: {spec.describe()}"
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(dir=target.parent, prefix=f".{target.name}."))
    staged = staging / "task"
    try:
        _materialize_tree(source, staged)
        if target.is_symlink():
            target.unlink()
        elif target.exists():
            shutil.rmtree(target)
        staged.rename(target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


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

        # Unpinned specs first: once a sha is checked out HEAD is detached, and
        # a bare ``git checkout`` afterwards would hand them that sha's files.
        for commit in sorted(by_commit, key=lambda c: c is not None):
            group = by_commit[commit]
            if commit is None:
                await _run_git("git", "checkout", cwd=repo_dir)
            else:
                await _run_git(
                    "git", "fetch", "--depth", "1", "origin", commit, cwd=repo_dir
                )
                await _run_git("git", "checkout", commit, cwd=repo_dir)
            await _pull_lfs_files(repo_dir, [s.path for s, _ in group])
            for spec, target in group:
                _copy_task(repo_dir, spec, target)
