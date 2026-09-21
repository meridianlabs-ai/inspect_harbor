"""Task directory layout, container-side paths, and Docker naming helpers.

Mirrors the conventions Harbor documents for a task directory::

    ├── instruction.md
    ├── task.toml
    ├── environment/   # Dockerfile or docker-compose.yaml
    ├── solution/      # solve.sh, copied to /solution by the oracle
    └── tests/         # test.sh, copied to /tests by the verifier
"""

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


class TaskPaths:
    """File paths inside a Harbor task directory."""

    CONFIG_FILENAME = "task.toml"

    def __init__(self, task_dir: Path | str) -> None:
        """Resolve ``task_dir`` to an absolute path."""
        self.task_dir = Path(task_dir).resolve()

    @property
    def instruction_path(self) -> Path:
        """Path to ``instruction.md``."""
        return self.task_dir / "instruction.md"

    @property
    def config_path(self) -> Path:
        """Path to ``task.toml``."""
        return self.task_dir / self.CONFIG_FILENAME

    @property
    def environment_dir(self) -> Path:
        """Path to the ``environment/`` directory."""
        return self.task_dir / "environment"

    @property
    def solution_dir(self) -> Path:
        """Path to the ``solution/`` directory."""
        return self.task_dir / "solution"

    @property
    def solve_path(self) -> Path:
        """Default path to the solve script."""
        return self.solution_dir / "solve.sh"

    @property
    def tests_dir(self) -> Path:
        """Path to the ``tests/`` directory."""
        return self.task_dir / "tests"

    @property
    def test_path(self) -> Path:
        """Default path to the test script."""
        return self.tests_dir / "test.sh"

    @property
    def steps_dir(self) -> Path:
        """Path to the ``steps/`` directory of a multi-step task."""
        return self.task_dir / "steps"


@dataclass(frozen=True)
class EnvironmentPaths:
    """Static paths inside a Linux task container.

    ``/logs/*`` are the directories Harbor mounts for agent and verifier
    output; ``/tests`` and ``/solution`` are where the verifier and oracle
    copy their files.
    """

    logs_dir: PurePosixPath = PurePosixPath("/logs")
    agent_dir: PurePosixPath = PurePosixPath("/logs/agent")
    verifier_dir: PurePosixPath = PurePosixPath("/logs/verifier")
    artifacts_dir: PurePosixPath = PurePosixPath("/logs/artifacts")
    tests_dir: PurePosixPath = PurePosixPath("/tests")
    solution_dir: PurePosixPath = PurePosixPath("/solution")
    reward_text_path: PurePosixPath = PurePosixPath("/logs/verifier/reward.txt")
    reward_json_path: PurePosixPath = PurePosixPath("/logs/verifier/reward.json")


def sanitize_docker_image_name(name: str) -> str:
    """Make ``name`` a valid single-segment Docker image name.

    Byte-for-byte the same rules as Harbor's sanitiser, so the ``hb__<task>``
    images we tag match the ones Harbor would build for the same task.
    """
    name = name.lower()
    if not re.match(r"^[a-z0-9]", name):
        name = "0" + name
    return re.sub(r"[^a-z0-9._-]", "-", name)
