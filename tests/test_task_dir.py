"""Tests for loading a Harbor task directory."""

from pathlib import Path
from typing import Any

import pytest
from helpers import make_task
from inspect_harbor._harbor.task_dir import HarborTask, strip_canary

FIXTURE = Path(__file__).parent / "fixtures" / "simple_task"
WINDOWS = '[environment]\nos = "windows"\n'


def test_loads_paths_config_name_and_instruction(tmp_path: Path) -> None:
    """The loaded task exposes its dir, paths, parsed config, name, and text."""
    task_dir = make_task(
        tmp_path, "[verifier]\ntimeout_sec = 7\n", instruction="# canary\n\nReal."
    )
    task = HarborTask(task_dir)
    assert task.task_dir == task_dir.resolve()
    assert task.paths.tests_dir == task_dir.resolve() / "tests"
    assert task.config.verifier.timeout_sec == 7
    assert task.name == "my-task"  # directory name when [task] is absent
    assert task.instruction == "Real."  # canary stripped by the loader
    assert task.has_steps is False


def test_fixture_loads() -> None:
    """The integration fixture loads end to end, named by ``[task].name``."""
    task = HarborTask(FIXTURE)
    assert task.name == "harbor-test/simple-task"
    assert "2 + 2" in task.instruction
    assert HarborTask.is_valid_dir(FIXTURE)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("plain", "plain"),
        ("# canary\nbody", "body"),
        ("body\n# canary at end", "body\n# canary at end"),
        ("<!-- Canary -->\n\nbody", "body"),
        (
            "<!-- BENCHMARK DATA CANARY abc -->\n# canary: xyz\n\n\nReal.\nMore.",
            "Real.\nMore.",
        ),
    ],
)
def test_strip_canary(text: str, expected: str) -> None:
    """Only leading canary lines, and the blanks after them, are stripped."""
    assert strip_canary(text) == expected


@pytest.mark.parametrize(
    "kwargs,match",
    [
        (dict(instruction=None), "instruction.md"),
        (dict(with_test=False), r"tests/test\.sh"),
        (dict(toml=WINDOWS), r"test\.bat"),
    ],
)
def test_missing_required_file_raises(
    tmp_path: Path, kwargs: dict[str, Any], match: str
) -> None:
    """Verification needs the instruction and the OS-appropriate test script."""
    task_dir = make_task(tmp_path, **kwargs)
    with pytest.raises(FileNotFoundError, match=match):
        HarborTask(task_dir)
    assert HarborTask.is_valid_dir(task_dir) is False


@pytest.mark.parametrize(
    "kwargs,disable_verification",
    [
        (dict(with_test=False), True),
        (
            dict(toml='[verifier]\nenvironment_mode = "separate"\n', with_test=False),
            False,
        ),
        (dict(toml=WINDOWS, test_name="test.bat"), False),
    ],
)
def test_loads_without_default_test_script(
    tmp_path: Path, kwargs: dict[str, Any], disable_verification: bool
) -> None:
    """Disabled verification, a separate verifier, or a Windows script all load."""
    task_dir = make_task(tmp_path, **kwargs)
    assert HarborTask(task_dir, disable_verification=disable_verification).name
    assert HarborTask.is_valid_dir(task_dir, disable_verification=disable_verification)


def test_steps_task(tmp_path: Path) -> None:
    """Multi-step tasks validate per-step files like Harbor, then load empty."""
    toml = '[[steps]]\nname = "one"\n'
    task_dir = make_task(tmp_path, toml, instruction=None, with_test=False)
    with pytest.raises(FileNotFoundError, match="Step directory"):
        HarborTask(task_dir)
    assert HarborTask.is_valid_dir(task_dir, disable_verification=True) is False
    (task_dir / "steps" / "one").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="Step instruction"):
        HarborTask(task_dir)
    (task_dir / "steps" / "one" / "instruction.md").write_text("step one")
    task = HarborTask(task_dir)
    assert task.has_steps is True
    assert task.instruction == ""
    assert HarborTask.is_valid_dir(task_dir) is True


def test_parse_errors_name_the_file(tmp_path: Path) -> None:
    """A broken ``task.toml`` is reported with its path."""
    bad_syntax = make_task(tmp_path, "[environment\n", dirname="syntax")
    with pytest.raises(ValueError, match=r"Invalid TOML in .*syntax/task\.toml"):
        HarborTask(bad_syntax)
    bad_value = make_task(tmp_path, '[environment]\ncpus = "two"\n', dirname="value")
    with pytest.raises(ValueError) as info:
        HarborTask(bad_value)
    assert any("value/task.toml" in note for note in info.value.__notes__)


def test_is_valid_dir(tmp_path: Path) -> None:
    """``is_valid_dir`` mirrors the constructor's checks without raising."""
    assert HarborTask.is_valid_dir(make_task(tmp_path, dirname="good")) is True

    no_toml = make_task(tmp_path, dirname="no-toml")
    (no_toml / "task.toml").unlink()
    assert HarborTask.is_valid_dir(no_toml) is False

    no_env = make_task(tmp_path, dirname="no-env")
    (no_env / "environment" / "Dockerfile").unlink()
    (no_env / "environment").rmdir()
    assert HarborTask.is_valid_dir(no_env) is False

    assert (
        HarborTask.is_valid_dir(make_task(tmp_path, "[environment\n", dirname="bad"))
        is False
    )

    no_instr = make_task(tmp_path, instruction=None, dirname="no-instr")
    assert HarborTask.is_valid_dir(no_instr, disable_verification=True) is False

    assert HarborTask.is_valid_dir(tmp_path / "does-not-exist") is False


@pytest.mark.parametrize(
    "link_target,ok",
    [("/etc/hostname", False), ("../../outside", False), ("../instruction.md", True)],
)
def test_inputs_must_stay_within_task(
    tmp_path: Path, link_target: str, ok: bool
) -> None:
    """``tests/`` and ``solution/`` may not link outside the task, even unverified."""
    (tmp_path / "outside").write_text("host file")
    task_dir = make_task(tmp_path)
    (task_dir / "tests" / "link").symlink_to(link_target)
    if ok:
        assert HarborTask(task_dir, disable_verification=True).name == "my-task"
        assert HarborTask.is_valid_dir(task_dir)
    else:
        with pytest.raises(ValueError, match="within the task"):
            HarborTask(task_dir, disable_verification=True)
        assert HarborTask.is_valid_dir(task_dir) is False
