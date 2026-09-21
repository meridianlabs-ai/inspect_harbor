"""Tests for loading a Harbor task directory."""

from pathlib import Path

import pytest
from helpers import make_task
from inspect_harbor._harbor.task_dir import HarborTask, strip_canary

FIXTURE = Path(__file__).parent / "fixtures" / "simple_task"


def test_name_from_task_section(tmp_path: Path) -> None:
    """``[task].name`` wins over the directory name."""
    task = HarborTask(make_task(tmp_path, '[task]\nname = "org/thing"\n'))
    assert task.name == "org/thing"


def test_name_from_directory(tmp_path: Path) -> None:
    """Without ``[task]`` the directory name is the task name."""
    task = HarborTask(make_task(tmp_path, dirname="dir-name"))
    assert task.name == "dir-name"


def test_paths_and_config_exposed(tmp_path: Path) -> None:
    """The loaded task exposes its dir, paths, and parsed config."""
    task_dir = make_task(tmp_path, "[verifier]\ntimeout_sec = 7\n")
    task = HarborTask(task_dir)
    assert task.task_dir == task_dir.resolve()
    assert task.paths.tests_dir == task_dir.resolve() / "tests"
    assert task.config.verifier.timeout_sec == 7
    assert task.has_steps is False


def test_instruction_read_and_canary_stripped(tmp_path: Path) -> None:
    """Leading canary comment lines and following blanks are removed."""
    text = "<!-- BENCHMARK DATA CANARY abc -->\n# canary: xyz\n\n\nReal text.\nMore."
    task = HarborTask(make_task(tmp_path, instruction=text))
    assert task.instruction == "Real text.\nMore."


@pytest.mark.parametrize(
    "text,expected",
    [
        ("plain", "plain"),
        ("# canary\nbody", "body"),
        ("body\n# canary at end", "body\n# canary at end"),
        ("<!-- Canary -->\n\nbody", "body"),
    ],
)
def test_strip_canary(text: str, expected: str) -> None:
    """Only leading canary lines are stripped."""
    assert strip_canary(text) == expected


def test_missing_instruction_raises(tmp_path: Path) -> None:
    """A task without ``instruction.md`` fails verification."""
    with pytest.raises(FileNotFoundError, match="instruction.md"):
        HarborTask(make_task(tmp_path, instruction=None))


def test_missing_test_script_raises(tmp_path: Path) -> None:
    """A Linux task without ``tests/test.sh`` fails verification."""
    with pytest.raises(FileNotFoundError, match=r"tests/test\.sh"):
        HarborTask(make_task(tmp_path, with_test=False))


def test_missing_test_script_ok_when_verification_disabled(tmp_path: Path) -> None:
    """``disable_verification`` skips the test-script check."""
    task = HarborTask(make_task(tmp_path, with_test=False), disable_verification=True)
    assert task.instruction == "Do the thing."


def test_missing_test_script_ok_for_separate_verifier(tmp_path: Path) -> None:
    """A separate verifier environment may ship its tests elsewhere."""
    task = HarborTask(
        make_task(
            tmp_path, '[verifier]\nenvironment_mode = "separate"\n', with_test=False
        )
    )
    assert task.config.verifier_runs_separately()


def test_windows_task_expects_bat(tmp_path: Path) -> None:
    """A Windows task is validated against ``tests/test.bat``."""
    toml = '[environment]\nos = "windows"\n'
    with pytest.raises(FileNotFoundError, match=r"test\.bat"):
        HarborTask(make_task(tmp_path, toml, test_name="test.sh"))
    task = HarborTask(make_task(tmp_path, toml, test_name="test.bat", dirname="w2"))
    assert task.config.environment.os.value == "windows"


def test_steps_task(tmp_path: Path) -> None:
    """Multi-step tasks load with an empty instruction and skip test checks."""
    toml = '[[steps]]\nname = "one"\n'
    task = HarborTask(make_task(tmp_path, toml, instruction=None, with_test=False))
    assert task.has_steps is True
    assert task.instruction == ""


def test_is_valid_dir(tmp_path: Path) -> None:
    """``is_valid_dir`` mirrors the constructor's checks without raising."""
    good = make_task(tmp_path, dirname="good")
    assert HarborTask.is_valid_dir(good) is True

    no_toml = make_task(tmp_path, dirname="no-toml")
    (no_toml / "task.toml").unlink()
    assert HarborTask.is_valid_dir(no_toml) is False

    no_env = make_task(tmp_path, dirname="no-env")
    (no_env / "environment" / "Dockerfile").unlink()
    (no_env / "environment").rmdir()
    assert HarborTask.is_valid_dir(no_env) is False

    bad_toml = make_task(tmp_path, "[environment\n", dirname="bad-toml")
    assert HarborTask.is_valid_dir(bad_toml) is False

    no_tests = make_task(tmp_path, with_test=False, dirname="no-tests")
    assert HarborTask.is_valid_dir(no_tests) is False
    assert HarborTask.is_valid_dir(no_tests, disable_verification=True) is True

    no_instr = make_task(tmp_path, instruction=None, dirname="no-instr")
    assert HarborTask.is_valid_dir(no_instr, disable_verification=True) is False

    assert HarborTask.is_valid_dir(tmp_path / "does-not-exist") is False


def test_fixture_loads() -> None:
    """The integration fixture loads end to end."""
    task = HarborTask(FIXTURE)
    assert task.name == "harbor-test/simple-task"
    assert "2 + 2" in task.instruction
    assert HarborTask.is_valid_dir(FIXTURE)
