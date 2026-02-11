"""Tests for Harbor task."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from harbor.models.task.task import Task as HarborTask
from inspect_harbor.harbor._task import _get_max_timeout_sec, load_harbor_tasks


def test_load_local_single_task():
    """Test loading a single local task."""
    with (
        patch("inspect_harbor.harbor._task._load_local_path") as mock_load_local,
        patch("inspect_harbor.harbor._task.HarborTask") as mock_harbor_task,
    ):
        # Setup mocks - _load_local_path returns list of Path objects
        task_path = Path("/local/path/to/task")
        mock_load_local.return_value = [task_path]

        mock_task = Mock(spec=HarborTask)
        mock_task.name = "test-task"
        mock_task.task_dir = task_path
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
        patch("inspect_harbor.harbor._task._load_git_task") as mock_load_git,
        patch("inspect_harbor.harbor._task.HarborTask") as mock_harbor_task,
    ):
        # Setup mocks - _load_git_task returns list of Path objects
        task_path = Path("/cache/downloaded/task")
        mock_load_git.return_value = [task_path]

        mock_task = Mock(spec=HarborTask)
        mock_task.name = "git-task"
        mock_task.task_dir = task_path
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
        patch("inspect_harbor.harbor._task._load_local_path") as mock_load_local,
        patch("inspect_harbor.harbor._task.HarborTask") as mock_harbor_task,
    ):
        # Setup mocks - _load_local_path returns list of Path objects
        task_path_1 = Path("/dataset/task1")
        task_path_2 = Path("/dataset/task2")
        mock_load_local.return_value = [task_path_1, task_path_2]

        mock_task_1 = Mock(spec=HarborTask)
        mock_task_1.name = "task1"
        mock_task_2 = Mock(spec=HarborTask)
        mock_task_2.name = "task2"
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


def test_load_from_registry():
    """Test loading tasks from a registry dataset."""
    with (
        patch("inspect_harbor.harbor._task._load_from_registry") as mock_load_registry,
        patch("inspect_harbor.harbor._task.HarborTask") as mock_harbor_task,
    ):
        # Setup mocks - _load_from_registry returns list of Path objects
        task_path = Path("/cache/registry/task")
        mock_load_registry.return_value = [task_path]

        mock_task = Mock(spec=HarborTask)
        mock_task.name = "registry-task"
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
        patch("inspect_harbor.harbor._task._load_git_task") as mock_load_git,
        patch("inspect_harbor.harbor._task.HarborTask") as mock_harbor_task,
    ):
        # Setup mocks
        task_path = Path("/cache/downloaded/task")
        mock_load_git.return_value = [task_path]

        mock_task = Mock(spec=HarborTask)
        mock_task.name = "git-task"
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
        patch("inspect_harbor.harbor._task._load_from_registry") as mock_load_registry,
        patch("inspect_harbor.harbor._task.HarborTask") as mock_harbor_task,
    ):
        # Setup mocks
        task_path = Path("/cache/registry/task")
        mock_load_registry.return_value = [task_path]

        mock_task = Mock(spec=HarborTask)
        mock_task.name = "registry-task"
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
            "Cannot specify both task and dataset parameters",
        ),
        (
            {"task_git_url": "https://github.com/org/repo"},
            "Task configuration with task_git_url requires path parameter",
        ),
        ({}, "Must specify either path, task parameters, or dataset parameters"),
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
        patch("inspect_harbor.harbor._task._load_local_path") as mock_load_local,
        patch("inspect_harbor.harbor._task.HarborTask") as mock_harbor_task,
    ):
        task_path = Path("/mock/path")
        mock_load_local.return_value = [task_path]

        mock_task = Mock(spec=HarborTask)
        mock_task.name = "test-task"
        mock_harbor_task.return_value = mock_task

        load_harbor_tasks(**kwargs)

        mock_load_local.assert_called_once_with(*expected_call_args)


@pytest.mark.parametrize(
    "timeout_values,expected",
    [
        ([100, 200, 150], 200),  # Multiple timeouts, returns max
        ([100.5], 100),  # Float conversion to int
        ([], None),  # Empty list returns None
    ],
)
def test_get_max_timeout_sec(
    timeout_values: list[int | float], expected: int | None
) -> None:
    """Test _get_max_timeout_sec with various inputs."""
    tasks = []
    for val in timeout_values:
        task = Mock(spec=HarborTask)
        task.config = Mock()
        task.config.agent = Mock()
        task.config.agent.timeout_sec = val
        tasks.append(task)

    result = _get_max_timeout_sec(tasks)
    assert result == expected
    if expected is not None:
        assert isinstance(result, int)


def test_harbor_task_integration():
    """Integration test: Load a real Harbor task and verify Task object."""
    from inspect_harbor.harbor._task import harbor

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
    assert sample.id == "simple_task"
    assert sample.input is not None
    assert "Simple Addition Task" in sample.input or "2 + 2" in sample.input

    # Verify metadata
    assert sample.metadata is not None
    assert sample.metadata["task_name"] == "simple_task"
    assert "test_path" in sample.metadata


def test_harbor_task_with_overrides():
    """Integration test: Verify override parameters are applied to sample environment."""
    from inspect_harbor.harbor._task import harbor

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
