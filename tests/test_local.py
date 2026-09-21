"""Tests for the cache root and local dataset helpers."""

from pathlib import Path

import pytest
from helpers import make_task
from inspect_harbor._harbor.cache import cache_root, stable_key
from inspect_harbor._harbor.local import filter_task_names, list_local_dataset_tasks


def test_cache_root_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without an override the cache lives under the user's cache dir."""
    monkeypatch.delenv("INSPECT_HARBOR_CACHE_DIR", raising=False)
    assert cache_root() == Path.home() / ".cache" / "inspect_harbor" / "tasks"


def test_cache_root_env_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``INSPECT_HARBOR_CACHE_DIR`` relocates the cache and is expanded."""
    monkeypatch.setenv("INSPECT_HARBOR_CACHE_DIR", str(tmp_path / "c"))
    assert cache_root() == tmp_path / "c"
    monkeypatch.setenv("INSPECT_HARBOR_CACHE_DIR", "~/x")
    assert cache_root() == Path.home() / "x"


def test_stable_key_deterministic_and_order_sensitive() -> None:
    """Keys are 16 hex chars, stable, and depend on part order."""
    key = stable_key("https://example.com/repo.git", "abc", "tasks/t1")
    assert key == stable_key("https://example.com/repo.git", "abc", "tasks/t1")
    assert len(key) == 16
    assert int(key, 16) >= 0
    assert key != stable_key("abc", "https://example.com/repo.git", "tasks/t1")
    # Parts are delimited, so concatenation collisions are avoided.
    assert stable_key("ab", "c") != stable_key("a", "bc")


def test_filter_task_names_include_exclude_and_limit() -> None:
    """Globs filter in order; ``n_tasks`` truncates the filtered list."""
    names = ["alpha-1", "alpha-2", "beta-1", "gamma"]
    assert filter_task_names(names, None, None, None) == names
    assert filter_task_names(names, ["alpha-*"], None, None) == ["alpha-1", "alpha-2"]
    assert filter_task_names(names, None, ["*-1"], None) == ["alpha-2", "gamma"]
    assert filter_task_names(names, ["alpha-*", "gamma"], ["alpha-2"], None) == [
        "alpha-1",
        "gamma",
    ]
    assert filter_task_names(names, None, None, 2) == ["alpha-1", "alpha-2"]
    assert filter_task_names(names, ["*-*"], None, 1) == ["alpha-1"]


def test_filter_task_names_no_match_raises() -> None:
    """An include filter matching nothing is an error that lists examples."""
    with pytest.raises(ValueError, match=r"No tasks matched.*Example task names"):
        filter_task_names(["a", "b"], ["zzz"], None, None)


def test_filter_task_names_exclude_everything_is_not_an_error() -> None:
    """Excluding everything yields an empty list rather than raising."""
    assert filter_task_names(["a"], None, ["*"], None) == []


def test_list_local_dataset_tasks(tmp_path: Path) -> None:
    """Only valid task dirs are listed, sorted, and filtered by dir name."""
    make_task(tmp_path, dirname="t-b")
    make_task(tmp_path, dirname="t-a")
    make_task(tmp_path, dirname="skip-me")
    (tmp_path / "not-a-task").mkdir()
    (tmp_path / "loose-file").write_text("x")
    broken = make_task(tmp_path, dirname="broken", with_test=False)

    assert list_local_dataset_tasks(tmp_path, None, None, None, False) == [
        tmp_path / "skip-me",
        tmp_path / "t-a",
        tmp_path / "t-b",
    ]
    assert list_local_dataset_tasks(tmp_path, ["t-*"], None, None, False) == [
        tmp_path / "t-a",
        tmp_path / "t-b",
    ]
    assert list_local_dataset_tasks(tmp_path, None, ["skip-*"], 1, False) == [
        tmp_path / "t-a"
    ]
    # With verification disabled the task lacking tests is included too.
    assert broken in list_local_dataset_tasks(tmp_path, None, None, None, True)
