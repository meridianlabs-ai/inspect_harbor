"""Tests for downloading git-hosted tasks (uses a real local git repository)."""

import asyncio
import subprocess
from pathlib import Path, PurePosixPath

import pytest
from helpers import make_task
from inspect_harbor._harbor import git_tasks
from inspect_harbor._harbor.git_tasks import (
    GitTaskSpec,
    clone_args,
    download_git_tasks,
    is_resolved_commit,
)


def _git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> tuple[str, str]:
    """A local repo with two tasks under ``tasks/``; returns ``(file_url, sha)``."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _git("init", "-q", "-b", "main", cwd=repo_dir)
    _git("config", "user.email", "t@example.com", cwd=repo_dir)
    _git("config", "user.name", "Test", cwd=repo_dir)
    # Let a shallow fetch by full sha work over file:// like GitHub allows.
    _git("config", "uploadpack.allowAnySHA1InWant", "true", cwd=repo_dir)
    make_task(repo_dir / "tasks", dirname="t1", instruction="first")
    make_task(repo_dir / "tasks", dirname="t2", instruction="second")
    (repo_dir / "README.md").write_text("not a task\n")
    _git("add", ".", cwd=repo_dir)
    _git("commit", "-q", "-m", "init", cwd=repo_dir)
    sha = _git("rev-parse", "HEAD", cwd=repo_dir)
    return f"file://{repo_dir}", sha


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Point the task cache at a temp dir for every test."""
    cache = tmp_path / "cache"
    monkeypatch.setenv("INSPECT_HARBOR_CACHE_DIR", str(cache))
    return cache


async def test_download_head(repo: tuple[str, str], isolated_cache: Path) -> None:
    """A HEAD spec clones the repo and copies just the task directory."""
    url, _ = repo
    spec = GitTaskSpec(git_url=url, path=PurePosixPath("tasks/t1"))
    [path] = await download_git_tasks([spec])
    assert path.is_relative_to(isolated_cache / "git")
    assert path.name == "t1"
    assert (path / "instruction.md").read_text() == "first"
    assert (path / "tests" / "test.sh").exists()
    assert not (path.parent / "README.md").exists()


async def test_download_pinned_and_cache_hit(
    repo: tuple[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A full-sha spec is downloaded once and then served from cache."""
    url, sha = repo
    spec = GitTaskSpec(git_url=url, path=PurePosixPath("tasks/t2"), git_commit_id=sha)
    [first] = await download_git_tasks([spec])
    assert (first / "instruction.md").read_text() == "second"

    async def boom(*args: object, **kwargs: object) -> str:
        raise AssertionError("git must not run on a cache hit")

    monkeypatch.setattr(git_tasks, "_run_git", boom)
    [second] = await download_git_tasks([spec])
    assert second == first


async def test_overwrite_redownloads(
    repo: tuple[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """``overwrite=True`` ignores the cache."""
    url, sha = repo
    spec = GitTaskSpec(git_url=url, path=PurePosixPath("tasks/t1"), git_commit_id=sha)
    [path] = await download_git_tasks([spec])
    (path / "instruction.md").write_text("tampered")
    [again] = await download_git_tasks([spec], overwrite=True)
    assert again == path
    assert (path / "instruction.md").read_text() == "first"


async def test_head_specs_are_never_cached(
    repo: tuple[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without a resolved commit the task is fetched again each time."""
    url, _ = repo
    spec = GitTaskSpec(git_url=url, path=PurePosixPath("tasks/t1"))
    await download_git_tasks([spec])
    calls: list[tuple[str, ...]] = []
    real = git_tasks._run_git

    async def spy(*args: str, **kwargs: object) -> str:
        calls.append(args)
        return await real(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(git_tasks, "_run_git", spy)
    await download_git_tasks([spec])
    assert any(a[:2] == ("git", "clone") for a in calls)


async def test_same_repo_cloned_once_and_order_preserved(
    repo: tuple[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Specs sharing a URL share one clone; results follow input order."""
    url, sha = repo
    specs = [
        GitTaskSpec(git_url=url, path=PurePosixPath("tasks/t2"), git_commit_id=sha),
        GitTaskSpec(git_url=url, path=PurePosixPath("tasks/t1"), git_commit_id=sha),
    ]
    calls: list[tuple[str, ...]] = []
    real = git_tasks._run_git

    async def spy(*args: str, **kwargs: object) -> str:
        calls.append(args)
        return await real(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(git_tasks, "_run_git", spy)
    paths = await download_git_tasks(specs)
    assert [p.name for p in paths] == ["t2", "t1"]
    assert sum(1 for a in calls if a[:2] == ("git", "clone")) == 1


async def test_git_failure_raises(tmp_path: Path) -> None:
    """A failing git command surfaces as ``RuntimeError`` with git's stderr."""
    spec = GitTaskSpec(
        git_url=f"file://{tmp_path / 'missing'}", path=PurePosixPath("tasks/t1")
    )
    with pytest.raises(RuntimeError, match="git clone"):
        await download_git_tasks([spec])


def test_clone_args_skip_blob_filter_for_hugging_face(tmp_path: Path) -> None:
    """Hugging Face's git server lacks promisor support, so no blob filter."""
    args = clone_args("https://github.com/org/repo", tmp_path)
    assert "--filter=blob:none" in args
    assert args[-2:] == ["https://github.com/org/repo", str(tmp_path)]
    hf = clone_args("https://huggingface.co/datasets/org/repo", tmp_path)
    assert "--filter=blob:none" not in hf
    assert "--depth" in hf and "--no-checkout" in hf


@pytest.mark.parametrize(
    "commit,expected",
    [
        (None, False),
        ("main", False),
        ("abc123", False),
        ("a" * 40, True),
        ("A" * 40, True),
        ("0" * 64, True),
        ("a" * 41, False),
    ],
)
def test_is_resolved_commit(commit: str | None, expected: bool) -> None:
    """Only full 40 or 64 hex-digit shas count as pinned."""
    assert is_resolved_commit(commit) is expected


def test_spec_name() -> None:
    """A spec's display name is the last path component."""
    spec = GitTaskSpec(git_url="u", path=PurePosixPath("a/b/task-x"))
    assert spec.name == "task-x"


@pytest.mark.parametrize("path", ["../escape", "/abs/path", ""])
def test_spec_rejects_paths_that_escape_the_repo(path: str) -> None:
    """Task paths must be relative and free of ``..``."""
    with pytest.raises(ValueError, match="relative"):
        GitTaskSpec(git_url="u", path=PurePosixPath(path))


@pytest.mark.parametrize(
    "link_target,expected",
    [
        ("/etc/hostname", "relative"),
        ("..", "within the task"),
        ("missing-file", "Invalid git task link"),
        ("instruction.md", None),
    ],
)
def test_symlinks_are_contained(
    repo: tuple[str, str], tmp_path: Path, link_target: str, expected: str | None
) -> None:
    """Links leaving the task are rejected; links inside it are materialised."""
    url, _ = repo
    repo_dir = Path(url.removeprefix("file://"))
    (repo_dir / "tasks" / "t1" / "link").symlink_to(link_target)
    _git("add", ".", cwd=repo_dir)
    _git("commit", "-q", "-m", "link", cwd=repo_dir)
    spec = GitTaskSpec(git_url=url, path=PurePosixPath("tasks/t1"))
    if expected is not None:
        with pytest.raises(ValueError, match=expected):
            asyncio.run(download_git_tasks([spec]))
        assert not git_tasks.target_dir(spec).exists()
        assert not list(git_tasks.target_dir(spec).parent.glob(".*"))
    else:
        [path] = asyncio.run(download_git_tasks([spec]))
        assert not (path / "link").is_symlink()
        assert (path / "link").read_text() == "first"


async def test_unpinned_spec_after_pinned_gets_head_content(
    repo: tuple[str, str],
) -> None:
    """A HEAD spec is not handed the files of a pinned sha from the same repo."""
    url, sha = repo
    repo_dir = Path(url.removeprefix("file://"))
    (repo_dir / "tasks" / "t2" / "instruction.md").write_text("second v2")
    _git("commit", "-q", "-am", "v2", cwd=repo_dir)
    pinned = GitTaskSpec(git_url=url, path=PurePosixPath("tasks/t1"), git_commit_id=sha)
    head = GitTaskSpec(git_url=url, path=PurePosixPath("tasks/t2"))
    _, t2 = await download_git_tasks([pinned, head])
    assert (t2 / "instruction.md").read_text() == "second v2"


async def test_incomplete_cache_dir_is_not_a_hit(repo: tuple[str, str]) -> None:
    """A pinned target without a task.toml (interrupted copy) is refetched."""
    url, sha = repo
    spec = GitTaskSpec(git_url=url, path=PurePosixPath("tasks/t1"), git_commit_id=sha)
    target = git_tasks.target_dir(spec)
    (target / "tests").mkdir(parents=True)
    [path] = await download_git_tasks([spec])
    assert path == target
    assert (target / "task.toml").exists()


async def test_git_errors_redact_credentials(tmp_path: Path) -> None:
    """A token embedded in the clone URL never reaches the error message."""
    spec = GitTaskSpec(
        git_url="https://user:s3cret@example.invalid/org/repo.git",
        path=PurePosixPath("tasks/t1"),
    )
    with pytest.raises(RuntimeError) as info:
        await download_git_tasks([spec])
    assert "s3cret" not in str(info.value)
    assert "***@example.invalid" in str(info.value)
