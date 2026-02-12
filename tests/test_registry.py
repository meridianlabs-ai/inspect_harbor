"""Tests for Harbor registry task discovery and versioning."""

import inspect
from unittest.mock import Mock, patch

import pytest


def _get_generated_tasks():
    """Helper to get only generated task functions (not imports)."""
    import inspect_harbor.tasks as tasks

    return [
        getattr(tasks, name)
        for name in dir(tasks)
        if not name.startswith("_")
        and callable(getattr(tasks, name))
        and hasattr(getattr(tasks, name), "__module__")
        and getattr(tasks, name).__module__ == "inspect_harbor.tasks"
    ]


def test_has_registered_tasks():
    """Test that at least some tasks are registered in _registry."""
    from inspect_harbor import _registry

    task_attrs = [name for name in dir(_registry) if not name.startswith("_")]
    assert len(task_attrs) > 0, "Should have at least some tasks registered"
    # Should have core functions plus generated tasks
    assert "harbor" in task_attrs
    assert "oracle" in task_attrs


def test_tasks_are_callable():
    """Test that generated tasks are callable."""
    task_funcs = _get_generated_tasks()
    assert len(task_funcs) > 0, "Should have at least some callable tasks"
    assert all(callable(f) for f in task_funcs)


def test_tasks_have_task_decorator():
    """Test that generated tasks have @task decorator."""
    task_funcs = _get_generated_tasks()
    # Check tasks have __wrapped__ attribute (sign of @task decorator)
    for func in task_funcs:
        assert hasattr(func, "__wrapped__"), (
            f"{func.__name__} should have @task decorator"
        )


def test_import_nonexistent_task_raises():
    """Test that importing nonexistent task raises ImportError."""
    with pytest.raises(ImportError, match="cannot import name"):
        from inspect_harbor import (  # type: ignore[attr-defined]
            nonexistent_task_xyz_12345,  # noqa: F401  # type: ignore[attr-defined]
        )


def test_task_has_correct_signature():
    """Test that generated tasks have the expected parameter signature."""
    task_funcs = _get_generated_tasks()
    first_task = task_funcs[0]

    # Check signature has expected parameters
    sig = inspect.signature(first_task)
    param_names = list(sig.parameters.keys())

    expected_params = [
        "dataset_task_names",
        "dataset_exclude_task_names",
        "n_tasks",
        "overwrite_cache",
        "sandbox_env_name",
        "override_cpus",
        "override_memory_mb",
        "override_gpus",
    ]

    for param in expected_params:
        assert param in param_names, f"Task should have {param} parameter"


def test_task_calls_harbor_base():
    """Test that generated tasks call _harbor_base with correct parameters."""
    task_funcs = _get_generated_tasks()
    first_task = task_funcs[0]

    with patch("inspect_harbor.tasks._harbor_base") as mock_harbor:
        mock_harbor.return_value = Mock()

        # Call the task with some parameters
        first_task(n_tasks=5, overwrite_cache=True)

        # Verify _harbor_base was called
        mock_harbor.assert_called_once()
        call_kwargs = mock_harbor.call_args[1]

        # Check expected parameters were passed through
        assert "dataset_name_version" in call_kwargs
        assert call_kwargs["n_tasks"] == 5
        assert call_kwargs["overwrite_cache"] is True


def test_task_parameters_passed_through():
    """Test that all task parameters are correctly passed to _harbor_base."""
    task_funcs = _get_generated_tasks()
    first_task = task_funcs[0]

    with patch("inspect_harbor.tasks._harbor_base") as mock_harbor:
        mock_harbor.return_value = Mock()

        # Call with all parameters
        first_task(
            dataset_task_names=["task1", "task2"],
            dataset_exclude_task_names=["task3"],
            n_tasks=10,
            overwrite_cache=True,
            sandbox_env_name="podman",
            override_cpus=8,
            override_memory_mb=16384,
            override_gpus=2,
        )

        call_kwargs = mock_harbor.call_args[1]
        assert call_kwargs["dataset_task_names"] == ["task1", "task2"]
        assert call_kwargs["dataset_exclude_task_names"] == ["task3"]
        assert call_kwargs["n_tasks"] == 10
        assert call_kwargs["overwrite_cache"] is True
        assert call_kwargs["sandbox_env_name"] == "podman"
        assert call_kwargs["override_cpus"] == 8
        assert call_kwargs["override_memory_mb"] == 16384
        assert call_kwargs["override_gpus"] == 2
