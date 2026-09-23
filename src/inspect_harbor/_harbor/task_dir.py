"""Load a Harbor task from its directory.

A task directory holds ``task.toml``, ``instruction.md``, an ``environment/``
directory with a Dockerfile or compose file, and ``tests/test.sh`` that the
verifier runs after the agent finishes (see ``paths.TaskPaths``).
"""

import re
import tomllib
from pathlib import Path

from pydantic import ValidationError

from inspect_harbor._harbor.models import TaskConfig, TaskOS
from inspect_harbor._harbor.paths import TaskPaths

# Canary lines are data-provenance markers (HTML or hash comments containing
# "canary") that must not be shown to the agent.
_CANARY_LINE_RE = re.compile(r"^(<!--.*canary.*-->|#.*canary.*)$", re.IGNORECASE)


class HarborTask:
    """A Harbor task loaded from disk.

    Attributes:
        task_dir: Absolute path to the task directory.
        paths: Conventional file locations inside ``task_dir``.
        config: The parsed ``task.toml``.
        name: ``[task].name`` when present, else the directory name.
        instruction: Contents of ``instruction.md`` with canary lines removed
            (empty for multi-step tasks, which inspect_harbor does not run).
    """

    def __init__(self, task_dir: Path | str, disable_verification: bool = False):
        """Load and, unless ``disable_verification``, validate a task directory.

        Raises:
            ValueError: When ``task.toml`` cannot be parsed (the message names
                the file).
            FileNotFoundError: When ``instruction.md`` or the test script the
                verifier needs is missing.
        """
        self.paths = TaskPaths(task_dir)
        self.task_dir = self.paths.task_dir
        self.config = load_task_config(self.paths.config_path)
        self.name = (
            self.config.task.name
            if self.config.task is not None
            else self.paths.task_dir.name
        )
        if not disable_verification:
            _validate_files(self.config, self.paths)
        if self.has_steps:
            self.instruction = ""
        else:
            self.instruction = strip_canary(self.paths.instruction_path.read_text())

    @property
    def has_steps(self) -> bool:
        """Whether ``task.toml`` declares ``[[steps]]`` (a multi-step task)."""
        return bool(self.config.steps)

    @staticmethod
    def is_valid_dir(task_dir: Path | str, disable_verification: bool = False) -> bool:
        """Whether ``task_dir`` is a loadable task directory.

        Mirrors the constructor's checks without raising, for scanning a
        dataset directory.
        """
        paths = TaskPaths(task_dir)
        if not paths.config_path.exists() or not paths.environment_dir.exists():
            return False
        try:
            config = load_task_config(paths.config_path)
        except (OSError, ValueError):
            return False
        if disable_verification:
            if config.steps:
                return all(
                    paths.step_instruction_path(step.name).exists()
                    for step in config.steps
                )
            return paths.instruction_path.exists()
        try:
            _validate_files(config, paths)
        except FileNotFoundError:
            return False
        return True


def load_task_config(config_path: Path) -> TaskConfig:
    """Parse a ``task.toml`` file, naming the file in any error.

    Raises:
        ValueError: On TOML syntax or validation errors (``ValidationError``
            is a ``ValueError``; ``TOMLDecodeError`` is wrapped).
    """
    try:
        return TaskConfig.from_toml(config_path.read_text())
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Invalid TOML in {config_path}: {exc}") from exc
    except ValidationError as exc:
        exc.add_note(f"while parsing {config_path}")
        raise


def strip_canary(text: str) -> str:
    """Remove leading canary comment lines, and blank lines after them."""
    lines = text.split("\n")
    idx = 0
    while idx < len(lines) and _CANARY_LINE_RE.match(lines[idx].strip()):
        idx += 1
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    return "\n".join(lines[idx:])


def _test_script_name(task_os: TaskOS) -> str:
    return "test.bat" if task_os is TaskOS.WINDOWS else "test.sh"


def _validate_files(config: TaskConfig, paths: TaskPaths) -> None:
    """Raise ``FileNotFoundError`` if files needed at run time are missing.

    Multi-step tasks are checked the way Harbor checks them (each step has a
    directory and an instruction) so dataset scans skip the same broken
    tasks Harbor would; inspect_harbor refuses them later with a clear
    ``NotImplementedError``.
    """
    if config.steps:
        for step in config.steps:
            step_dir = paths.step_dir(step.name)
            if not step_dir.exists():
                raise FileNotFoundError(f"Step directory not found: {step_dir}")
            instruction = paths.step_instruction_path(step.name)
            if not instruction.exists():
                raise FileNotFoundError(f"Step instruction not found: {instruction}")
        return
    if not paths.instruction_path.exists():
        raise FileNotFoundError(
            f"Task directory {paths.task_dir} is missing instruction.md."
        )
    # A separately-run verifier brings its own environment and tests.
    if config.verifier_runs_separately():
        return
    expected = paths.tests_dir / _test_script_name(config.environment.os)
    if not expected.exists():
        rel = expected.relative_to(paths.task_dir).as_posix()
        raise FileNotFoundError(
            f"Task directory {paths.task_dir} declares [environment].os = "
            f"{config.environment.os.value!r} but does not contain {rel}."
        )
