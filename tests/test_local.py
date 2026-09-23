"""Tests for the cache root and local dataset helpers."""

from pathlib import Path

import pytest
from helpers import make_task
from inspect_harbor._harbor.cache import cache_root, stable_key
from inspect_harbor._harbor.local import (
    filter_entries,
    filter_task_names,
    list_local_dataset_tasks,
)

NAMES = ["alpha-1", "alpha-2", "beta-1", "gamma"]


def test_cache_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The cache defaults under the user's cache dir; the env override is expanded."""
    monkeypatch.delenv("INSPECT_HARBOR_CACHE_DIR", raising=False)
    assert cache_root() == Path.home() / ".cache" / "inspect_harbor" / "tasks"
    monkeypatch.setenv("INSPECT_HARBOR_CACHE_DIR", str(tmp_path / "c"))
    assert cache_root() == tmp_path / "c"
    monkeypatch.setenv("INSPECT_HARBOR_CACHE_DIR", "~/x")
    assert cache_root() == Path.home() / "x"


def test_stable_key_deterministic_and_order_sensitive() -> None:
    """Keys are 16 hex chars, stable, and depend on part order and boundaries."""
    key = stable_key("https://example.com/repo.git", "abc", "tasks/t1")
    assert key == stable_key("https://example.com/repo.git", "abc", "tasks/t1")
    assert len(key) == 16 and int(key, 16) >= 0
    assert key != stable_key("abc", "https://example.com/repo.git", "tasks/t1")
    assert stable_key("ab", "c") != stable_key("a", "bc")


@pytest.mark.parametrize(
    "include,exclude,n_tasks,expected",
    [
        (None, None, None, NAMES),
        (["alpha-*"], None, None, ["alpha-1", "alpha-2"]),
        (None, ["*-1"], None, ["alpha-2", "gamma"]),
        (["alpha-*", "gamma"], ["alpha-2"], None, ["alpha-1", "gamma"]),
        (None, None, 2, ["alpha-1", "alpha-2"]),
        (["*-*"], None, 1, ["alpha-1"]),
        (None, ["*"], None, []),
    ],
)
def test_filter_task_names(
    include: list[str] | None,
    exclude: list[str] | None,
    n_tasks: int | None,
    expected: list[str],
) -> None:
    """Globs filter in order; ``n_tasks`` truncates after filtering."""
    assert filter_task_names(NAMES, include, exclude, n_tasks) == expected


def test_filter_task_names_no_match_raises() -> None:
    """An include filter matching nothing is an error that lists examples."""
    with pytest.raises(ValueError, match=r"No tasks matched.*Example task names"):
        filter_task_names(["a", "b"], ["zzz"], None, None)


def test_filter_entries_keeps_duplicates_apart() -> None:
    """Entries sharing a name are filtered one by one, so ``n_tasks`` holds."""
    entries = [("hello", 1), ("hello", 2), ("other", 3)]
    assert filter_entries(entries, lambda e: e[0], None, None, 1) == [("hello", 1)]
    assert filter_entries(entries, lambda e: e[0], ["hello"], None, None) == [
        ("hello", 1),
        ("hello", 2),
    ]


def test_list_local_dataset_tasks(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Valid task dirs are listed sorted; task-like invalid ones are reported."""
    make_task(tmp_path, dirname="t-b")
    make_task(tmp_path, dirname="t-a")
    (tmp_path / "not-a-task").mkdir()
    (tmp_path / "loose-file").write_text("x")
    broken = make_task(tmp_path, dirname="broken", with_test=False)

    with caplog.at_level("WARNING", logger="inspect_harbor._harbor.local"):
        listed = list_local_dataset_tasks(tmp_path, None, None, None, False)
    assert listed == [tmp_path / "t-a", tmp_path / "t-b"]
    assert "Skipping" in caplog.text and "broken" in caplog.text
    assert "not-a-task" not in caplog.text
    # With verification disabled the task lacking tests is included too.
    assert broken in list_local_dataset_tasks(tmp_path, None, None, None, True)
