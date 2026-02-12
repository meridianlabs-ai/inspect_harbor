"""Tests for the Harbor registry task generator script."""

import sys
from pathlib import Path
from typing import Any

import pytest

# Add scripts directory to path to allow importing generate_tasks
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from generate_tasks import (  # type: ignore[import-not-found]  # noqa: E402
    dataset_name_to_function_name,
    generate_tasks_content,
)


@pytest.fixture
def mock_registry_data() -> list[dict[str, Any]]:
    """Mock Harbor registry data with versioned datasets."""
    return [
        {
            "name": "test-dataset",
            "version": "1.0",
            "description": "Test dataset version 1.0",
        },
        {
            "name": "test-dataset",
            "version": "2.0",
            "description": "Test dataset version 2.0",
        },
        {
            "name": "multi-variant",
            "version": "all",
            "description": "Multi variant dataset - all",
        },
        {
            "name": "multi-variant",
            "version": "subset",
            "description": "Multi variant dataset - subset",
        },
        {
            "name": "simple-dataset",
            "version": "1.0",
            "description": "Simple dataset",
        },
    ]


def test_dataset_name_to_function_name_basic() -> None:
    """Test basic dataset name conversion."""
    assert dataset_name_to_function_name("terminal-bench") == "terminal_bench"
    assert dataset_name_to_function_name("hello-world") == "hello_world"
    assert dataset_name_to_function_name("simple") == "simple"


def test_dataset_name_to_function_name_with_version() -> None:
    """Test dataset name conversion with versions."""
    assert dataset_name_to_function_name("terminal-bench@2.0") == "terminal_bench_2_0"
    assert dataset_name_to_function_name("bixbench@1.5") == "bixbench_1_5"
    assert dataset_name_to_function_name("dataset@all") == "dataset_all"


def test_dataset_name_to_function_name_complex() -> None:
    """Test complex dataset name conversion."""
    assert (
        dataset_name_to_function_name("swe-lancer-diamond@all")
        == "swe_lancer_diamond_all"
    )
    assert (
        dataset_name_to_function_name("multi-part-name@1.2.3")
        == "multi_part_name_1_2_3"
    )


def test_generate_tasks_creates_versioned_functions(
    mock_registry_data: list[dict[str, Any]],
) -> None:
    """Test that versioned task functions are generated."""
    content = generate_tasks_content(mock_registry_data)

    # Check versioned functions are created
    assert "def test_dataset_1_0(" in content
    assert "def test_dataset_2_0(" in content
    assert "def multi_variant_all(" in content
    assert "def multi_variant_subset(" in content
    assert "def simple_dataset_1_0(" in content


def test_generate_tasks_creates_unversioned_functions(
    mock_registry_data: list[dict[str, Any]],
) -> None:
    """Test that unversioned task functions are created for backwards compatibility."""
    content = generate_tasks_content(mock_registry_data)

    # Check unversioned functions are created (one per unique dataset name)
    assert "def test_dataset(" in content
    assert "def multi_variant(" in content
    assert "def simple_dataset(" in content


def test_generate_tasks_includes_correct_dataset_name_version(
    mock_registry_data: list[dict[str, Any]],
) -> None:
    """Test that generated functions pass correct dataset_name_version."""
    content = generate_tasks_content(mock_registry_data)

    # Versioned tasks should pass dataset@version
    assert 'dataset_name_version="test-dataset@1.0"' in content
    assert 'dataset_name_version="test-dataset@2.0"' in content
    assert 'dataset_name_version="multi-variant@all"' in content

    # Unversioned tasks should pass just dataset name
    # These appear in the unversioned function definitions
    assert 'dataset_name_version="test-dataset"' in content
    assert 'dataset_name_version="multi-variant"' in content


def test_generate_tasks_includes_descriptions(
    mock_registry_data: list[dict[str, Any]],
) -> None:
    """Test that generated functions include dataset descriptions in docstrings."""
    content = generate_tasks_content(mock_registry_data)

    assert "Test dataset version 1.0" in content
    assert "Test dataset version 2.0" in content
    assert "Multi variant dataset - all" in content
    assert "Simple dataset" in content


def test_generate_tasks_includes_version_info(
    mock_registry_data: list[dict[str, Any]],
) -> None:
    """Test that generated functions include version information."""
    content = generate_tasks_content(mock_registry_data)

    # Versioned tasks should show explicit version
    assert "Version: 1.0" in content
    assert "Version: 2.0" in content
    assert "Version: all" in content

    # Unversioned tasks should indicate they're using latest
    assert "Latest available" in content


def test_generate_tasks_includes_required_imports(
    mock_registry_data: list[dict[str, Any]],
) -> None:
    """Test that generated code includes necessary imports."""
    content = generate_tasks_content(mock_registry_data)

    assert "from inspect_ai import Task, task" in content
    assert "from inspect_harbor.harbor._task import harbor as _harbor_base" in content


def test_generate_tasks_includes_task_decorator(
    mock_registry_data: list[dict[str, Any]],
) -> None:
    """Test that all generated functions have @task decorator."""
    content = generate_tasks_content(mock_registry_data)

    # Count @task decorators - should equal number of generated functions
    # 5 versioned + 3 unversioned (test-dataset, multi-variant, simple-dataset)
    decorator_count = content.count("@task\n")
    assert decorator_count == 8


def test_generate_tasks_includes_all_parameters(
    mock_registry_data: list[dict[str, Any]],
) -> None:
    """Test that generated functions include all expected parameters."""
    content = generate_tasks_content(mock_registry_data)

    assert "dataset_task_names: list[str] | None = None" in content
    assert "dataset_exclude_task_names: list[str] | None = None" in content
    assert "n_tasks: int | None = None" in content
    assert "overwrite_cache: bool = False" in content
    assert "sandbox_env_name: str = " in content
    assert "override_cpus: int | None = None" in content
    assert "override_memory_mb: int | None = None" in content
    assert "override_gpus: int | None = None" in content


def test_generate_tasks_passes_parameters_to_base(
    mock_registry_data: list[dict[str, Any]],
) -> None:
    """Test that generated functions pass parameters to _harbor_base."""
    content = generate_tasks_content(mock_registry_data)

    assert "dataset_task_names=dataset_task_names" in content
    assert "dataset_exclude_task_names=dataset_exclude_task_names" in content
    assert "n_tasks=n_tasks" in content
    assert "overwrite_cache=overwrite_cache" in content
    assert "sandbox_env_name=sandbox_env_name" in content
    assert "override_cpus=override_cpus" in content
    assert "override_memory_mb=override_memory_mb" in content
    assert "override_gpus=override_gpus" in content


def test_generate_tasks_skips_entries_without_name() -> None:
    """Test that generator skips registry entries without a name."""
    invalid_registry = [
        {"version": "1.0", "description": "No name"},
        {"name": "valid-dataset", "version": "1.0", "description": "Has name"},
    ]

    content = generate_tasks_content(invalid_registry)

    # Should only generate function for valid entry
    assert "def valid_dataset_1_0(" in content
    assert "@task" in content
    # Count should be 2: versioned + unversioned for valid-dataset
    assert content.count("@task") == 2


def test_generate_tasks_deduplicates_versions(
    mock_registry_data: list[dict[str, Any]],
) -> None:
    """Test that duplicate version entries are handled correctly."""
    # Add duplicate entry
    registry_with_duplicate = mock_registry_data + [
        {
            "name": "test-dataset",
            "version": "1.0",
            "description": "Duplicate entry",
        }
    ]

    content = generate_tasks_content(registry_with_duplicate)

    # Should still only have one function for test-dataset@1.0
    # Count how many times the exact function definition appears
    test_dataset_1_0_count = content.count("def test_dataset_1_0(")
    assert test_dataset_1_0_count == 1
