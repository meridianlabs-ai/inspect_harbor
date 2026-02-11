"""Tests for Harbor to Inspect AI converters."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml
from inspect_ai.dataset import Sample
from inspect_ai.util import ComposeBuild, ComposeConfig, SandboxEnvironmentSpec
from inspect_ai.util._sandbox.compose import ComposeDeviceReservation
from inspect_harbor.harbor._converters import (
    harbor_task_to_sample,
    harbor_to_compose_config,
)


def test_harbor_to_compose_config_with_existing_compose_yaml():
    """Test converting Harbor task with existing docker-compose.yaml file."""
    # Setup mock Harbor task
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = 2.0
    mock_env_config.memory_mb = 4096
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_task.config.environment = mock_env_config

    # Mock docker-compose.yaml content (without version field as ComposeConfig doesn't accept it)
    compose_yaml_content = """
services:
  default:
    image: python:3.11
    command: tail -f /dev/null
"""

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=compose_yaml_content)),
    ):
        # docker-compose.yaml exists, Dockerfile does not
        mock_exists.side_effect = lambda: True

        result = harbor_to_compose_config(mock_task)

        assert isinstance(result, ComposeConfig)
        assert result.services is not None
        assert len(result.services) == 1
        assert "default" in result.services

        service = result.services["default"]
        assert service.cpus == 2.0
        assert service.mem_limit == "4096m"


def test_harbor_to_compose_config_with_dockerfile():
    """Test converting Harbor task with Dockerfile (programmatic build)."""
    # Setup mock Harbor task
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = None
    mock_env_config.allow_internet = True
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_task.config.environment = mock_env_config

    def exists_side_effect(self: Path) -> bool:
        # docker-compose.yaml does not exist, Dockerfile exists
        return str(self).endswith("Dockerfile")

    with patch("pathlib.Path.exists", exists_side_effect):
        result = harbor_to_compose_config(mock_task)

        assert isinstance(result, ComposeConfig)
        assert result.services is not None
        assert "default" in result.services

        service = result.services["default"]
        assert service.build is not None
        assert isinstance(service.build, ComposeBuild)
        assert service.build.context == "/task/environment"
        assert service.image is None
        assert service.cpus == 1.0
        assert service.mem_limit == "2048m"
        assert service.command == "tail -f /dev/null"
        assert service.init is True
        assert service.network_mode == "bridge"


def test_harbor_to_compose_config_with_prebuilt_image():
    """Test converting Harbor task with pre-built docker_image."""
    # Setup mock Harbor task
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = 1.5
    mock_env_config.memory_mb = 3072
    mock_env_config.docker_image = "my-custom-image:latest"
    mock_env_config.allow_internet = False
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_task.config.environment = mock_env_config

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)

        assert isinstance(result, ComposeConfig)
        assert result.services is not None
        assert "default" in result.services

        service = result.services["default"]
        assert service.image == "my-custom-image:latest"
        assert service.build is None
        assert service.cpus == 1.5
        assert service.mem_limit == "3072m"
        assert service.network_mode == "none"


def test_harbor_to_compose_config_custom_resource_limits():
    """Test resource limits (cpus, memory_mb) are correctly applied."""
    # Setup mock Harbor task
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = 4.0
    mock_env_config.memory_mb = 8192
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.allow_internet = True
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_task.config.environment = mock_env_config

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)

        service = result.services["default"]
        assert service.cpus == 4.0
        assert service.mem_limit == "8192m"


def test_harbor_to_compose_config_default_resource_limits():
    """Test default resource limits when not specified."""
    # Setup mock Harbor task
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = None
    mock_env_config.memory_mb = None
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.allow_internet = True
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_task.config.environment = mock_env_config

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)

        service = result.services["default"]
        assert service.cpus == 1.0
        # When memory_mb is None, no limit is set (unlimited memory)
        assert service.mem_limit is None


def test_harbor_to_compose_config_network_mode_with_internet():
    """Test network mode (bridge vs none) based on allow_internet setting."""
    # Test with internet allowed
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = None
    mock_env_config.memory_mb = None
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.allow_internet = True
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_task.config.environment = mock_env_config

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)
        assert result.services["default"].network_mode == "bridge"


def test_harbor_to_compose_config_network_mode_without_internet():
    """Test network mode is 'none' when internet is not allowed."""
    # Test with internet not allowed
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = None
    mock_env_config.memory_mb = None
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.allow_internet = False
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_task.config.environment = mock_env_config

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)
        assert result.services["default"].network_mode == "none"


def test_harbor_task_to_sample_metadata_preserved():
    """Test Harbor task to Sample conversion with all metadata preserved."""
    # Setup mock Harbor task
    mock_task = Mock()
    mock_task.name = "test-task"
    mock_task.instruction = "Complete this coding task"
    mock_task.task_dir = Path("/tasks/test-task")

    mock_paths = Mock()
    mock_paths.environment_dir = Path("/tasks/test-task/environment")
    mock_paths.test_path = Path("/tasks/test-task/tests/test.py")
    mock_paths.tests_dir = Path("/tasks/test-task/tests")
    mock_paths.solution_dir = Path("/tasks/test-task/solution")
    mock_paths.solve_path = Path("/tasks/test-task/solution/solve.py")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = 2.0
    mock_env_config.memory_mb = 4096
    mock_env_config.docker_image = "python:3.11"
    mock_env_config.allow_internet = True
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_task.config.environment = mock_env_config

    mock_verifier_config = Mock()
    mock_verifier_config.timeout_sec = 300
    mock_task.config.verifier = mock_verifier_config
    mock_task.config.model_dump = Mock(return_value={"test": "config"})

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_task_to_sample(mock_task)

        assert isinstance(result, Sample)
        assert result.input == "Complete this coding task"
        assert result.id == "test-task"

        assert result.metadata is not None
        assert result.metadata["task_name"] == "test-task"
        assert result.metadata["task_dir"] == "/tasks/test-task"
        assert result.metadata["test_path"] == "/tasks/test-task/tests/test.py"
        assert result.metadata["tests_dir"] == "/tasks/test-task/tests"
        assert result.metadata["solution_dir"] == "/tasks/test-task/solution"
        assert result.metadata["solve_path"] == "/tasks/test-task/solution/solve.py"
        assert result.metadata["verifier_timeout_sec"] == 300
        assert result.metadata["harbor_config"] == {"test": "config"}


def test_harbor_task_to_sample_sandbox_spec():
    """Test that SandboxEnvironmentSpec is correctly created with docker and compose config."""
    # Setup mock Harbor task
    mock_task = Mock()
    mock_task.name = "test-task"
    mock_task.instruction = "Test instruction"
    mock_task.task_dir = Path("/tasks/test-task")

    mock_paths = Mock()
    mock_paths.environment_dir = Path("/tasks/test-task/environment")
    mock_paths.test_path = Path("/tasks/test-task/tests/test.py")
    mock_paths.tests_dir = Path("/tasks/test-task/tests")
    mock_paths.solution_dir = Path("/tasks/test-task/solution")
    mock_paths.solve_path = Path("/tasks/test-task/solution/solve.py")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.allow_internet = False
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_task.config.environment = mock_env_config

    mock_verifier_config = Mock()
    mock_verifier_config.timeout_sec = 60
    mock_task.config.verifier = mock_verifier_config
    mock_task.config.model_dump = Mock(return_value={})

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_task_to_sample(mock_task)

        assert isinstance(result.sandbox, SandboxEnvironmentSpec)
        assert result.sandbox.type == "docker"
        assert isinstance(result.sandbox.config, ComposeConfig)

        compose_config = result.sandbox.config
        assert compose_config.services is not None
        assert "default" in compose_config.services

        service = compose_config.services["default"]
        assert service.image == "ubuntu:latest"
        assert service.cpus == 1.0
        assert service.mem_limit == "2048m"
        assert service.network_mode == "none"


def test_harbor_to_compose_config_with_gpu_settings():
    """Test GPU configuration is correctly applied to ComposeService."""
    # Setup mock Harbor task with GPU requirements
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = 2.0
    mock_env_config.memory_mb = 4096
    mock_env_config.docker_image = "nvidia/cuda:12.0-base"
    mock_env_config.allow_internet = True
    mock_env_config.gpus = 2
    mock_env_config.gpu_types = ["H100", "A100"]
    mock_task.config.environment = mock_env_config

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)

        assert isinstance(result, ComposeConfig)
        assert result.services is not None
        assert "default" in result.services

        service = result.services["default"]
        assert service.deploy is not None
        assert service.deploy.resources is not None
        assert service.deploy.resources.reservations is not None
        assert service.deploy.resources.reservations.devices is not None
        assert len(service.deploy.resources.reservations.devices) == 1

        device = service.deploy.resources.reservations.devices[0]
        assert isinstance(device, ComposeDeviceReservation)
        assert device.count == 2
        assert device.capabilities == ["gpu"]
        assert device.options is not None
        assert device.options["gpu_types"] == "H100,A100"


def test_harbor_to_compose_config_without_gpus():
    """Test that no GPU deployment config is created when gpus=0."""
    # Setup mock Harbor task without GPU requirements
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.allow_internet = True
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_task.config.environment = mock_env_config

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)

        service = result.services["default"]
        # deploy should be None when gpus=0
        assert service.deploy is None


def test_harbor_to_compose_config_with_gpus_no_types():
    """Test GPU configuration without specific GPU types."""
    # Setup mock Harbor task with GPUs but no specific types
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = "tensorflow/tensorflow:latest-gpu"
    mock_env_config.allow_internet = True
    mock_env_config.gpus = 1
    mock_env_config.gpu_types = None
    mock_task.config.environment = mock_env_config

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)

        service = result.services["default"]
        assert service.deploy is not None
        assert service.deploy.resources is not None
        assert service.deploy.resources.reservations is not None
        assert service.deploy.resources.reservations.devices is not None

        device = service.deploy.resources.reservations.devices[0]
        assert device.count == 1
        assert device.capabilities == ["gpu"]
        # options should be None when no gpu_types specified
        assert device.options is None


def test_harbor_to_compose_config_with_malformed_yaml(tmp_path: Path):
    """Test harbor_to_compose_config with malformed YAML file."""
    # Create task with malformed docker-compose.yaml
    env_dir = tmp_path / "environment"
    env_dir.mkdir()

    # Create malformed YAML (unclosed quote)
    compose_yaml = env_dir / "docker-compose.yaml"
    compose_yaml.write_text(
        """
services:
  default:
    image: "test:latest
    cpus: 1
    """
    )

    mock_task = Mock()
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = env_dir
    mock_task.config = Mock()
    mock_task.config.environment = Mock()
    mock_task.config.environment.cpus = 1.0
    mock_task.config.environment.memory_mb = 2048
    mock_task.config.environment.gpus = 0
    mock_task.config.environment.gpu_types = None
    mock_task.config.environment.docker_image = None

    with pytest.raises(yaml.YAMLError):
        harbor_to_compose_config(mock_task)


def test_harbor_task_to_sample_with_verifier_env():
    """Test that verifier_env is properly extracted and added to sample metadata."""
    # Setup mock Harbor task
    mock_task = Mock()
    mock_task.name = "test-task"
    mock_task.instruction = "Complete this task"
    mock_task.task_dir = Path("/tasks/test-task")

    mock_paths = Mock()
    mock_paths.environment_dir = Path("/tasks/test-task/environment")
    mock_paths.test_path = Path("/tasks/test-task/tests/test.sh")
    mock_paths.tests_dir = Path("/tasks/test-task/tests")
    mock_paths.solution_dir = Path("/tasks/test-task/solution")
    mock_paths.solve_path = Path("/tasks/test-task/solution/solve.sh")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = "python:3.11"
    mock_env_config.allow_internet = True
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_task.config.environment = mock_env_config

    # Mock verifier config with env vars
    mock_verifier_config = Mock()
    mock_verifier_config.timeout_sec = 600
    mock_verifier_config.env = {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "MODEL_NAME": "gpt-4o",
    }
    mock_task.config.verifier = mock_verifier_config
    mock_task.config.model_dump = Mock(return_value={"test": "config"})

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_task_to_sample(mock_task)

        assert isinstance(result, Sample)
        assert result.metadata is not None
        assert "verifier_env" in result.metadata
        assert result.metadata["verifier_env"] == {
            "OPENAI_API_KEY": "${OPENAI_API_KEY}",
            "MODEL_NAME": "gpt-4o",
        }


def test_harbor_task_to_sample_without_verifier_env():
    """Test that verifier_env defaults to empty dict when not specified."""
    # Setup mock Harbor task
    mock_task = Mock()
    mock_task.name = "test-task"
    mock_task.instruction = "Complete this task"
    mock_task.task_dir = Path("/tasks/test-task")

    mock_paths = Mock()
    mock_paths.environment_dir = Path("/tasks/test-task/environment")
    mock_paths.test_path = Path("/tasks/test-task/tests/test.sh")
    mock_paths.tests_dir = Path("/tasks/test-task/tests")
    mock_paths.solution_dir = Path("/tasks/test-task/solution")
    mock_paths.solve_path = Path("/tasks/test-task/solution/solve.sh")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = "python:3.11"
    mock_env_config.allow_internet = True
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_task.config.environment = mock_env_config

    # Mock verifier config WITHOUT env vars (None or not set)
    mock_verifier_config = Mock()
    mock_verifier_config.timeout_sec = 600
    mock_verifier_config.env = None
    mock_task.config.verifier = mock_verifier_config
    mock_task.config.model_dump = Mock(return_value={"test": "config"})

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_task_to_sample(mock_task)

        assert isinstance(result, Sample)
        assert result.metadata is not None
        assert "verifier_env" in result.metadata
        assert result.metadata["verifier_env"] == {}


@pytest.fixture
def mock_harbor_task():
    """Create a mock Harbor task with standard test configuration."""
    mock_task = Mock()
    mock_task.name = "test-task"
    mock_task.instruction = "Test instruction"
    mock_task.task_dir = Path("/tasks/test-task")

    mock_paths = Mock()
    mock_paths.environment_dir = Path("/tasks/test-task/environment")
    mock_paths.test_path = Path("/tasks/test-task/tests/test.py")
    mock_paths.tests_dir = Path("/tasks/test-task/tests")
    mock_paths.solution_dir = Path("/tasks/test-task/solution")
    mock_paths.solve_path = Path("/tasks/test-task/solution/solve.py")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = 2
    mock_env_config.memory_mb = 4096
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.allow_internet = True
    mock_env_config.gpus = 1
    mock_env_config.gpu_types = ["H100"]
    mock_task.config.environment = mock_env_config

    mock_verifier_config = Mock()
    mock_verifier_config.timeout_sec = 300
    mock_verifier_config.env = {}
    mock_task.config.verifier = mock_verifier_config

    mock_solution_config = Mock()
    mock_solution_config.env = {}
    mock_task.config.solution = mock_solution_config

    mock_task.config.model_dump = Mock(return_value={})

    return mock_task


@pytest.mark.parametrize(
    "override_cpus,override_memory_mb,override_gpus,expected_cpus,expected_memory,expected_gpus",
    [
        # Override all parameters
        (8, 16384, 4, 8, "16384m", 4),
        # Override only cpus
        (16, None, None, 16, "4096m", 1),
        # Override only memory
        (None, 8192, None, 2, "8192m", 1),
        # Override only gpus
        (None, None, 2, 2, "4096m", 2),
        # Override to zero gpus (disables GPU)
        (None, None, 0, 2, "4096m", None),
        # No overrides (use config defaults)
        (None, None, None, 2, "4096m", 1),
    ],
)
def test_harbor_to_compose_config_overrides(
    mock_harbor_task: Any,
    override_cpus: int | None,
    override_memory_mb: int | None,
    override_gpus: int | None,
    expected_cpus: int,
    expected_memory: str,
    expected_gpus: int | None,
):
    """Test that override parameters correctly override task config values."""
    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(
            mock_harbor_task,
            override_cpus=override_cpus,
            override_memory_mb=override_memory_mb,
            override_gpus=override_gpus,
        )

        service = result.services["default"]
        assert service.cpus == expected_cpus
        assert service.mem_limit == expected_memory

        if expected_gpus is None:
            assert service.deploy is None
        else:
            assert service.deploy is not None
            assert service.deploy.resources is not None
            assert service.deploy.resources.reservations is not None
            assert service.deploy.resources.reservations.devices is not None
            device = service.deploy.resources.reservations.devices[0]
            assert device.count == expected_gpus


def test_harbor_task_to_sample_passes_overrides(mock_harbor_task: Any):
    """Test that harbor_task_to_sample correctly passes overrides through."""
    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_task_to_sample(
            mock_harbor_task,
            override_cpus=8,
            override_memory_mb=16384,
            override_gpus=4,
        )

        assert result.sandbox is not None
        compose_config = result.sandbox.config
        service = compose_config.services["default"]

        assert service.cpus == 8
        assert service.mem_limit == "16384m"
        assert service.deploy is not None
        assert service.deploy.resources is not None
        assert service.deploy.resources.reservations is not None
        assert service.deploy.resources.reservations.devices is not None
        device = service.deploy.resources.reservations.devices[0]
        assert device.count == 4


def test_harbor_to_compose_config_unlimited_memory():
    """Test that memory_mb=None results in no memory limit (unlimited)."""
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.cpus = 2
    mock_env_config.memory_mb = None  # No memory limit specified
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.allow_internet = True
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_task.config.environment = mock_env_config

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)

        service = result.services["default"]
        assert service.cpus == 2
        # mem_limit should be None when memory_mb is None (unlimited)
        assert service.mem_limit is None
        assert service.deploy is None
