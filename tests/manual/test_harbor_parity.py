"""Opt-in parity check between our task loader and the ``harbor`` package.

Last verified against harbor 0.23.0 (task.toml schema 1.4). Bump the pin
below deliberately when adopting a newer Harbor release, and re-run.

Excluded by default (``--ignore=tests/manual``). It needs an environment
with both ``inspect_harbor`` and ``harbor`` installed, which our own venv
deliberately does not have (install from outside the repo so the project's
``exclude-newer`` window does not apply)::

    uv venv /tmp/venv-harbor
    cd /tmp && uv pip install --python /tmp/venv-harbor/bin/python \
        "harbor==0.23.0" pytest pytest-asyncio -e <path to this checkout>
    export INSPECT_HARBOR_CACHE_DIR=~/.cache/inspect_harbor/tasks
    /tmp/venv-harbor/bin/pytest tests/manual/test_harbor_parity.py -q

Every task directory in the hub cache, plus the integration fixture, is
loaded with both implementations and the fields inspect_harbor reads are
compared, along with the derived values we ship: the image tag's content
hash, the canary-stripped instruction, and separate-verifier detection.
Warm the cache first by loading a few datasets.
"""

import warnings
from pathlib import Path

import pytest

harbor_task = pytest.importorskip("harbor.models.task.task")
harbor_docker = pytest.importorskip("harbor.environments.docker.docker")
harbor_definition = pytest.importorskip("harbor.environments.definition")
harbor_verifier_mode = pytest.importorskip("harbor.models.task.verifier_mode")

from inspect_harbor._harbor.cache import cache_root  # noqa: E402
from inspect_harbor._harbor.paths import (  # noqa: E402
    environment_content_hash,
    sanitize_docker_image_name,
)
from inspect_harbor._harbor.task_dir import HarborTask  # noqa: E402

pytestmark = pytest.mark.slow

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "simple_task"


def _task_dirs() -> list[Path]:
    hub = cache_root() / "hub"
    cached = sorted(
        p for p in hub.glob("*/*/*") if p.is_dir() and (p / "task.toml").exists()
    )
    return [FIXTURE, *cached]


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)


@pytest.mark.parametrize("task_dir", _task_dirs(), ids=lambda p: p.name[:40])
def test_task_parity(task_dir: Path) -> None:
    """Our loader agrees with Harbor's on every field inspect_harbor reads."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ours = HarborTask(task_dir, disable_verification=True)
        theirs = harbor_task.Task(task_dir, disable_verification=True)

    assert ours.name == theirs.name
    assert ours.instruction == theirs.instruction
    assert ours.has_steps == theirs.has_steps
    assert ours.paths.tests_dir == theirs.paths.tests_dir
    assert ours.paths.test_path == theirs.paths.test_path
    assert ours.paths.solution_dir == theirs.paths.solution_dir
    assert ours.paths.environment_dir == theirs.paths.environment_dir

    env_a, env_b = ours.config.environment, theirs.config.environment
    for field in ("docker_image", "cpus", "memory_mb", "gpus", "gpu_types", "env"):
        assert getattr(env_a, field) == getattr(env_b, field), field
    assert _enum_value(env_a.network_mode) == _enum_value(env_b.network_mode)
    assert _enum_value(env_a.os) == _enum_value(env_b.os)
    assert (env_a.healthcheck is None) == (env_b.healthcheck is None)
    if env_a.healthcheck is not None and env_b.healthcheck is not None:
        assert env_a.healthcheck.model_dump() == env_b.healthcheck.model_dump()
    assert env_a.skills_dir == env_b.skills_dir
    assert len(env_a.mcp_servers) == len(env_b.mcp_servers)

    ver_a, ver_b = ours.config.verifier, theirs.config.verifier
    assert ver_a.timeout_sec == ver_b.timeout_sec
    assert ver_a.env == ver_b.env
    assert ver_a.user == ver_b.user
    assert ours.config.agent.user == theirs.config.agent.user
    assert ours.config.solution.env == theirs.config.solution.env

    if theirs.config.task is None:
        assert ours.config.task is None
    else:
        assert ours.config.task is not None
        assert ours.config.task.name == theirs.config.task.name
        assert ours.config.task.description == theirs.config.task.description
        assert ours.config.task.keywords == theirs.config.task.keywords

    assert sanitize_docker_image_name(
        f"hb__{ours.name}"
    ) == harbor_docker._sanitize_docker_image_name(f"hb__{theirs.name}")

    # Derived values we ship: image tag hash and separate-verifier detection.
    assert environment_content_hash(
        ours.paths.environment_dir, docker_image=env_a.docker_image
    ) == harbor_definition.environment_content_hash(
        theirs.paths.environment_dir, docker_image=env_b.docker_image
    )
    assert ours.config.verifier_runs_separately() == (
        harbor_verifier_mode.resolve_effective_verifier_env_config(
            theirs.config, step_cfg=None
        )
        is not None
    )


def test_is_valid_dir_parity() -> None:
    """``is_valid_dir`` agrees with Harbor's on every cached task."""
    for task_dir in _task_dirs():
        for flag in (False, True):
            assert HarborTask.is_valid_dir(
                task_dir, disable_verification=flag
            ) == harbor_task.Task.is_valid_dir(task_dir, disable_verification=flag), (
                task_dir,
                flag,
            )
