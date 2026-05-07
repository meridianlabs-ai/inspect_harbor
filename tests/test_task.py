"""Tests for Harbor task."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from harbor.models.task.task import Task as HarborTask
from inspect_harbor._harbor.task import (
    _disambiguate_sample_ids,
    harbor,
    load_harbor_tasks,
)


def _make_harbor_task_mock(
    name: str = "test-task",
    task_dir: Path | None = None,
    has_steps: bool = False,
    os: str = "linux",
) -> Mock:
    """Create a Mock HarborTask wired up for ``_build_harbor_tasks``'s validator.

    ``HarborTask.config`` is set in ``__init__`` from ``task.toml`` — it isn't
    a class attribute, so ``Mock(spec=HarborTask)`` doesn't expose it. We
    attach a plain Mock with the ``[environment]`` defaults the validator reads.
    """
    m = Mock(spec=HarborTask)
    m.has_steps = has_steps
    m.name = name
    m.task_dir = task_dir or Path("/tmp")
    m.config = Mock()
    m.config.environment.os = os
    m.config.environment.healthcheck = None
    m.config.environment.mcp_servers = []
    m.config.environment.skills_dir = None
    return m


def test_load_local_single_task():
    """Test loading a single local task."""
    with (
        patch("inspect_harbor._harbor.task._load_local_path") as mock_load_local,
        patch("inspect_harbor._harbor.task.HarborTask") as mock_harbor_task,
    ):
        # Setup mocks - _load_local_path returns list of Path objects
        task_path = Path("/local/path/to/task")
        mock_load_local.return_value = [task_path]

        mock_task = _make_harbor_task_mock(name="test-task", task_dir=task_path)
        mock_harbor_task.return_value = mock_task

        # Execute
        result = load_harbor_tasks(path="/local/path/to/task")

        # Assert
        assert len(result) == 1
        assert result[0] == mock_task
        mock_load_local.assert_called_once_with(
            Path("/local/path/to/task"),
            None,  # dataset_task_names
            None,  # dataset_exclude_task_names
            None,  # n_tasks
            False,  # disable_verification
        )
        mock_harbor_task.assert_called_once_with(task_dir=task_path)


def test_load_git_task():
    """Test loading a task from git repository."""
    with (
        patch("inspect_harbor._harbor.task._load_git_task") as mock_load_git,
        patch("inspect_harbor._harbor.task.HarborTask") as mock_harbor_task,
    ):
        # Setup mocks - _load_git_task returns list of Path objects
        task_path = Path("/cache/downloaded/task")
        mock_load_git.return_value = [task_path]

        mock_task = _make_harbor_task_mock(name="git-task", task_dir=task_path)
        mock_harbor_task.return_value = mock_task

        # Execute
        result = load_harbor_tasks(
            path="task-name",
            task_git_url="https://github.com/org/repo",
            task_git_commit_id="abc123",
        )

        # Assert
        assert len(result) == 1
        assert result[0] == mock_task
        mock_load_git.assert_called_once_with(
            Path("task-name"),
            "https://github.com/org/repo",
            "abc123",
            False,  # overwrite_cache default
        )
        mock_harbor_task.assert_called_once_with(task_dir=task_path)


def test_load_local_dataset():
    """Test loading multiple tasks from a local dataset directory."""
    with (
        patch("inspect_harbor._harbor.task._load_local_path") as mock_load_local,
        patch("inspect_harbor._harbor.task.HarborTask") as mock_harbor_task,
    ):
        # Setup mocks - _load_local_path returns list of Path objects
        task_path_1 = Path("/dataset/task1")
        task_path_2 = Path("/dataset/task2")
        mock_load_local.return_value = [task_path_1, task_path_2]

        mock_task_1 = _make_harbor_task_mock(name="task1", task_dir=task_path_1)
        mock_task_2 = _make_harbor_task_mock(name="task2", task_dir=task_path_2)
        mock_harbor_task.side_effect = [mock_task_1, mock_task_2]

        # Execute
        result = load_harbor_tasks(path="/dataset", n_tasks=2)

        # Assert
        assert len(result) == 2
        assert result[0].name == "task1"
        assert result[1].name == "task2"
        mock_load_local.assert_called_once_with(
            Path("/dataset"),
            None,  # dataset_task_names
            None,  # dataset_exclude_task_names
            2,  # n_tasks
            False,  # disable_verification
        )


def test_load_from_package():
    """Test loading tasks from a package-based dataset (Harbor 0.3.0+)."""
    with (
        patch("inspect_harbor._harbor.task._load_from_package") as mock_load_package,
        patch("inspect_harbor._harbor.task.HarborTask") as mock_harbor_task,
    ):
        task_path = Path("/cache/packages/harbor/hello-world")
        mock_load_package.return_value = [task_path]

        mock_task = _make_harbor_task_mock(
            name="harbor/hello-world", task_dir=task_path
        )
        mock_harbor_task.return_value = mock_task

        result = load_harbor_tasks(
            package_name="harbor/hello-world", package_ref="latest"
        )

        assert len(result) == 1
        assert result[0] == mock_task
        mock_load_package.assert_called_once_with(
            "harbor/hello-world",
            "latest",
            None,  # dataset_task_names
            None,  # dataset_exclude_task_names
            None,  # n_tasks
            False,  # overwrite_cache default
        )


@pytest.mark.parametrize(
    "kwargs,expected_match",
    [
        (
            {"has_steps": True},
            r"Multi-step tasks: \['blocking-task'\]",
        ),
        (
            {"os": "windows"},
            r"Windows containers .*\['blocking-task'\]",
        ),
    ],
    ids=["multi_step", "windows_os"],
)
def test_build_harbor_tasks_blocks_unsupported_features(
    kwargs: dict[str, Any], expected_match: str
) -> None:
    """Multi-step and Windows-OS tasks raise ``NotImplementedError`` from the validator."""
    with (
        patch("inspect_harbor._harbor.task._load_local_path") as mock_load_local,
        patch("inspect_harbor._harbor.task.HarborTask") as mock_harbor_task,
    ):
        mock_load_local.return_value = [Path("/some/blocking/task")]
        mock_harbor_task.return_value = _make_harbor_task_mock(
            name="blocking-task", **kwargs
        )

        with pytest.raises(NotImplementedError, match=expected_match):
            load_harbor_tasks(path="/some/blocking/task")


def test_load_from_registry():
    """Test loading tasks from a registry dataset."""
    with (
        patch("inspect_harbor._harbor.task._load_from_registry") as mock_load_registry,
        patch("inspect_harbor._harbor.task.HarborTask") as mock_harbor_task,
    ):
        # Setup mocks - _load_from_registry returns list of Path objects
        task_path = Path("/cache/registry/task")
        mock_load_registry.return_value = [task_path]

        mock_task = _make_harbor_task_mock(name="registry-task", task_dir=task_path)
        mock_harbor_task.return_value = mock_task

        # Execute
        result = load_harbor_tasks(dataset_name_version="test-dataset@1.0", n_tasks=5)

        # Assert
        assert len(result) == 1
        assert result[0] == mock_task
        mock_load_registry.assert_called_once_with(
            "test-dataset@1.0",
            None,  # registry_url
            None,  # registry_path
            None,  # dataset_task_names
            None,  # dataset_exclude_task_names
            5,  # n_tasks
            False,  # overwrite_cache default
        )
        mock_harbor_task.assert_called_once_with(task_dir=task_path)


def test_load_git_task_with_overwrite_cache():
    """Test loading a git task with overwrite_cache=True."""
    with (
        patch("inspect_harbor._harbor.task._load_git_task") as mock_load_git,
        patch("inspect_harbor._harbor.task.HarborTask") as mock_harbor_task,
    ):
        # Setup mocks
        task_path = Path("/cache/downloaded/task")
        mock_load_git.return_value = [task_path]

        mock_task = _make_harbor_task_mock(name="git-task", task_dir=task_path)
        mock_harbor_task.return_value = mock_task

        # Execute with overwrite_cache=True
        result = load_harbor_tasks(
            path="task-name",
            task_git_url="https://github.com/org/repo",
            task_git_commit_id="abc123",
            overwrite_cache=True,
        )

        # Assert overwrite_cache is passed correctly
        assert len(result) == 1
        mock_load_git.assert_called_once_with(
            Path("task-name"),
            "https://github.com/org/repo",
            "abc123",
            True,  # overwrite_cache=True
        )


def test_load_registry_with_overwrite_cache():
    """Test loading a registry dataset with overwrite_cache=True."""
    with (
        patch("inspect_harbor._harbor.task._load_from_registry") as mock_load_registry,
        patch("inspect_harbor._harbor.task.HarborTask") as mock_harbor_task,
    ):
        # Setup mocks
        task_path = Path("/cache/registry/task")
        mock_load_registry.return_value = [task_path]

        mock_task = _make_harbor_task_mock(name="registry-task", task_dir=task_path)
        mock_harbor_task.return_value = mock_task

        # Execute with overwrite_cache=True
        result = load_harbor_tasks(
            dataset_name_version="test-dataset@1.0",
            n_tasks=5,
            overwrite_cache=True,
        )

        # Assert overwrite_cache is passed correctly
        assert len(result) == 1
        mock_load_registry.assert_called_once_with(
            "test-dataset@1.0",
            None,  # registry_url
            None,  # registry_path
            None,  # dataset_task_names
            None,  # dataset_exclude_task_names
            5,  # n_tasks
            True,  # overwrite_cache=True
        )


@pytest.mark.parametrize(
    "kwargs,expected_match",
    [
        (
            {
                "path": "/some/path",
                "task_git_url": "https://github.com/org/repo",
                "dataset_name_version": "dataset@1.0",
            },
            "Cannot mix task, dataset, and package parameters",
        ),
        (
            {
                "task_git_url": "https://github.com/org/repo",
                "package_name": "harbor/hello-world",
            },
            "Cannot mix task, dataset, and package parameters",
        ),
        (
            {
                "dataset_name_version": "dataset@1.0",
                "package_name": "harbor/hello-world",
            },
            "Cannot mix task, dataset, and package parameters",
        ),
        (
            {
                "task_git_url": "https://github.com/org/repo",
                "dataset_name_version": "dataset@1.0",
                "package_name": "harbor/hello-world",
            },
            "Cannot mix task, dataset, and package parameters",
        ),
        (
            {"task_git_url": "https://github.com/org/repo"},
            "Task configuration with task_git_url requires path parameter",
        ),
        (
            {},
            "Must specify either path, task parameters, dataset parameters, or package parameters",
        ),
        (
            {"registry_url": "https://registry.example.com"},
            "Cannot specify registry_url, registry_path, dataset_task_names, or "
            "dataset_exclude_task_names without also specifying dataset_name_version or path",
        ),
    ],
)
def test_load_harbor_tasks_validation_errors(
    kwargs: dict[str, Any], expected_match: str
) -> None:
    """Test validation errors for invalid parameter combinations."""
    with pytest.raises(ValueError, match=expected_match):
        load_harbor_tasks(**kwargs)


@pytest.mark.parametrize(
    "kwargs,expected_call_args",
    [
        # String path conversion
        (
            {"path": "/string/path"},
            (Path("/string/path"), None, None, None, False),
        ),
        # Disable verification
        (
            {"path": "/some/path", "disable_verification": True},
            (Path("/some/path"), None, None, None, True),
        ),
        # Dataset filtering
        (
            {
                "path": "/dataset",
                "dataset_task_names": ["task1", "task2"],
                "dataset_exclude_task_names": ["task3"],
                "n_tasks": 10,
            },
            (Path("/dataset"), ["task1", "task2"], ["task3"], 10, False),
        ),
    ],
)
def test_load_harbor_tasks_parameter_passing(
    kwargs: dict[str, Any],
    expected_call_args: tuple[
        Path, list[str] | None, list[str] | None, int | None, bool
    ],
) -> None:
    """Test that parameters are correctly passed to internal functions."""
    with (
        patch("inspect_harbor._harbor.task._load_local_path") as mock_load_local,
        patch("inspect_harbor._harbor.task.HarborTask") as mock_harbor_task,
    ):
        task_path = Path("/mock/path")
        mock_load_local.return_value = [task_path]

        mock_task = _make_harbor_task_mock(name="test-task", task_dir=task_path)
        mock_harbor_task.return_value = mock_task

        load_harbor_tasks(**kwargs)

        mock_load_local.assert_called_once_with(*expected_call_args)


def test_harbor_task_integration():
    """Integration test: Load a real Harbor task and verify Task object."""
    # Load the test Harbor task fixture
    task_path = Path(__file__).parent / "fixtures" / "simple_task"
    assert task_path.exists(), f"Test fixture not found at {task_path}"

    # Call harbor() to load the task
    task = harbor(path=task_path)

    # Verify Task object properties
    assert task is not None
    assert hasattr(task, "dataset")
    assert hasattr(task, "solver")
    assert hasattr(task, "scorer")

    # Verify dataset has samples
    assert len(task.dataset) == 1

    # Verify sample structure
    sample = task.dataset[0]
    assert sample.id == "harbor-test/simple-task"
    assert sample.input is not None
    assert "Simple Addition Task" in sample.input or "2 + 2" in sample.input

    # Verify metadata
    assert sample.metadata is not None
    assert sample.metadata["task_name"] == "harbor-test/simple-task"
    assert "test_path" in sample.metadata


def test_disambiguate_sample_ids_no_collisions():
    """Unique names pass through unchanged."""
    t1 = Mock(spec=HarborTask)
    t1.name = "alpha"
    t1.task_dir = Path("/cache/a")
    t2 = Mock(spec=HarborTask)
    t2.name = "beta"
    t2.task_dir = Path("/cache/b")

    assert _disambiguate_sample_ids([t1, t2]) == ["alpha", "beta"]


def test_disambiguate_sample_ids_collisions_get_hash_suffix():
    """Tasks sharing a name get an ``@<hash>`` suffix derived from task_dir."""
    t1 = Mock(spec=HarborTask)
    t1.name = "shared"
    t1.task_dir = Path("/cache/one")
    t2 = Mock(spec=HarborTask)
    t2.name = "shared"
    t2.task_dir = Path("/cache/two")
    t3 = Mock(spec=HarborTask)
    t3.name = "unique"
    t3.task_dir = Path("/cache/three")

    ids = _disambiguate_sample_ids([t1, t2, t3])
    # Unique name unchanged; colliding ones disambiguated and distinct.
    assert ids[2] == "unique"
    assert ids[0].startswith("shared@") and ids[1].startswith("shared@")
    assert ids[0] != ids[1]
    # Suffix shape: 8-hex-char content hash.
    assert len(ids[0].split("@", 1)[1]) == 8


async def test_load_harbor_tasks_inside_running_event_loop():
    """Sync API must bridge correctly when invoked from a running event loop.

    Covers the Jupyter / FastAPI lifespan / ``async def`` user-script case.
    """
    task_path = Path(__file__).parent / "fixtures" / "simple_task"
    assert task_path.exists()

    tasks = load_harbor_tasks(path=task_path)

    assert len(tasks) == 1
    assert tasks[0].name == "harbor-test/simple-task"


def test_harbor_task_with_overrides():
    """Integration test: Verify override parameters are applied to sample environment."""
    # Load the test Harbor task fixture
    task_path = Path(__file__).parent / "fixtures" / "simple_task"
    assert task_path.exists(), f"Test fixture not found at {task_path}"

    # Call harbor() with override parameters
    task = harbor(
        path=task_path,
        override_cpus=8,
        override_memory_mb=16384,
        override_gpus=2,
    )

    # Verify Task object created
    assert task is not None
    assert len(task.dataset) == 1

    # Get the sample and verify sandbox config
    sample = task.dataset[0]
    assert sample.sandbox is not None

    # Verify compose config has overridden values
    compose_config = sample.sandbox.config
    assert compose_config.services is not None
    assert "default" in compose_config.services

    service = compose_config.services["default"]

    # Verify overrides were applied
    assert service.cpus == 8
    assert service.mem_limit == "16384m"
    assert service.deploy is not None
    assert service.deploy.resources is not None
    assert service.deploy.resources.reservations is not None
    assert service.deploy.resources.reservations.devices is not None
    assert len(service.deploy.resources.reservations.devices) == 1
    device = service.deploy.resources.reservations.devices[0]
    assert device.count == 2
