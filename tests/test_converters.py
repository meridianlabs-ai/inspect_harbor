"""Tests for Harbor to Inspect AI converters."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml
from harbor.models.task.config import (
    AgentConfig,
    EnvironmentConfig,
    HealthcheckConfig,
    NetworkMode,
    TaskConfig,
    VerifierConfig,
)
from inspect_ai.dataset import Sample
from inspect_ai.util import ComposeBuild, ComposeConfig, SandboxEnvironmentSpec
from inspect_ai.util._sandbox.compose import ComposeDeviceReservation
from inspect_harbor._harbor.converters import (
    _expand_compose_vars,
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
    mock_env_config.env = {}
    mock_env_config.cpus = 2.0
    mock_env_config.memory_mb = 4096
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_env_config.network_mode = "public"
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
        # 6GB minimum is applied (config has 4096m which is below minimum)
        assert service.mem_limit == "6144m"
        assert service.network_mode is None


def test_harbor_to_compose_config_with_dockerfile():
    """Test converting Harbor task with Dockerfile (programmatic build)."""
    # Setup mock Harbor task
    mock_task = Mock()
    mock_task.name = "my-task"
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.env = {}
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = None
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
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
        # Built image is given a stable, task-derived tag so subsequent
        # runs can reuse it instead of rebuilding.
        assert service.image == "hb__my-task"
        assert service.cpus == 1.0
        # 6GB minimum is applied (config has 2048m which is below minimum)
        assert service.mem_limit == "6144m"
        assert service.command == "tail -f /dev/null"
        assert service.init is True
        assert service.network_mode == "bridge"


def test_harbor_to_compose_config_dockerfile_image_tag_is_deterministic():
    """Dockerfile-only path stamps the build with a stable ``hb__<task>`` tag.

    Regression test for cache misses on repeat runs: without an explicit
    ``image:``, Compose tags the build as ``<project>-<service>`` and
    ``compose_cleanup_images`` deletes it on shutdown (the project name
    carries a random suffix and the cleanup loop targets that prefix).
    A stable tag both survives cleanup and lets Docker reuse the image
    across runs.
    """
    mock_task = Mock()
    # Task name with characters that must be sanitized for a Docker tag
    # (slash, uppercase) so we lock in the sanitization behavior too.
    mock_task.name = "swe-bench/Django__django-12406"
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.env = {}
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 6144
    mock_env_config.docker_image = None
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_task.config.environment = mock_env_config

    def exists_side_effect(self: Path) -> bool:
        return str(self).endswith("Dockerfile")

    with patch("pathlib.Path.exists", exists_side_effect):
        first = harbor_to_compose_config(mock_task)
        second = harbor_to_compose_config(mock_task)

    # Same task -> same tag across invocations (this is the whole point).
    assert first.services["default"].image == second.services["default"].image
    # Sanitized: lowercased, '/' replaced with '-'.
    assert first.services["default"].image == "hb__swe-bench-django__django-12406"
    # And we're still building from the Dockerfile.
    assert isinstance(first.services["default"].build, ComposeBuild)


def test_harbor_to_compose_config_dockerfile_path_injects_task_env(
    monkeypatch: pytest.MonkeyPatch,
):
    """No-compose-yaml branch resolves ``[environment].env`` host refs.

    Mirrors harbor's ``_maybe_resolve_task_env``: ``${VAR}`` is baked in from
    the host now (so it reaches remote DinD providers), ``${VAR:-default}``
    falls back, and literals pass through.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "sk-resolved")
    mock_task = Mock()
    mock_task.name = "env-injection-task"
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.env = {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "MODEL": "${UNSET_MODEL:-gpt-5}",
        "LOG_LEVEL": "INFO",
    }
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = None
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_task.config.environment = mock_env_config

    def exists_side_effect(self: Path) -> bool:
        return str(self).endswith("Dockerfile")

    with patch("pathlib.Path.exists", exists_side_effect):
        result = harbor_to_compose_config(mock_task)

    service = result.services["default"]
    assert service.environment == {
        "OPENAI_API_KEY": "sk-resolved",
        "MODEL": "gpt-5",
        "LOG_LEVEL": "INFO",
    }


def test_harbor_to_compose_config_dockerfile_path_missing_env_var_raises(
    monkeypatch: pytest.MonkeyPatch,
):
    """A required host var with no default fails fast (matches harbor)."""
    monkeypatch.delenv("MISSING_SECRET", raising=False)
    mock_task = Mock()
    mock_task.name = "env-injection-task"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/task/environment")

    mock_env_config = Mock()
    mock_env_config.env = {"API_KEY": "${MISSING_SECRET}"}
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = None
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_task.config.environment = mock_env_config

    def exists_side_effect(self: Path) -> bool:
        return str(self).endswith("Dockerfile")

    with patch("pathlib.Path.exists", exists_side_effect):
        with pytest.raises(ValueError, match="MISSING_SECRET"):
            harbor_to_compose_config(mock_task)


def test_harbor_to_compose_config_with_prebuilt_image():
    """Test converting Harbor task with pre-built docker_image."""
    # Setup mock Harbor task
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.env = {}
    mock_env_config.cpus = 1.5
    mock_env_config.memory_mb = 3072
    mock_env_config.docker_image = "my-custom-image:latest"
    mock_env_config.network_mode = "no-network"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
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
        # 6GB minimum is applied (config has 3072m which is below minimum)
        assert service.mem_limit == "6144m"
        assert service.network_mode == "none"


def test_harbor_to_compose_config_custom_resource_limits():
    """Test resource limits (cpus, memory_mb) are correctly applied."""
    # Setup mock Harbor task
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.env = {}
    mock_env_config.cpus = 4.0
    mock_env_config.memory_mb = 8192
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_task.config.environment = mock_env_config

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)

        service = result.services["default"]
        assert service.cpus == 4.0
        assert service.mem_limit == "8192m"


def test_harbor_to_compose_config_omitted_resources_impose_no_limits():
    """Omitted resource fields impose no limit, mirroring Harbor >=0.17.

    Harbor >=0.17 leaves ``cpus``/``memory_mb``/``gpus`` as ``None`` when
    task.toml omits them and applies no limit in its docker provider. We do
    the same: no ``cpus``, no ``mem_limit``, and no GPU ``deploy`` on the
    service. Uses a real ``EnvironmentConfig`` so the test tracks the schema.
    """
    mock_task = Mock()
    mock_task.name = "omitted-resources-task"
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    env_config = EnvironmentConfig(docker_image="ubuntu:latest")
    assert env_config.cpus is None
    assert env_config.memory_mb is None
    assert env_config.gpus is None
    mock_task.config.environment = env_config

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)

        service = result.services["default"]
        assert service.cpus is None
        assert service.mem_limit is None
        assert service.deploy is None
        assert service.network_mode == "bridge"


def test_harbor_to_compose_config_omitted_resources_compose_yaml_defaults():
    """Omitted resources: ``${CPUS}``/``${MEMORY}`` use the compose file's defaults.

    No limit is imposed on the service, and — mirroring Harbor — an unset
    resource leaves the env var unset (rather than crashing on None), so a
    ``${CPUS:-N}`` reference falls back to its own default.
    """
    mock_task = Mock()
    mock_task.name = "omitted-resources-task"
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths
    mock_task.config.environment = EnvironmentConfig()
    mock_task.config.verifier.env = {}

    compose_yaml_content = """
services:
  default:
    image: python:3.11
    environment:
      CPU_COUNT: "${CPUS:-4}"
      MEM: "${MEMORY:-2G}"
"""

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=compose_yaml_content)),
    ):
        mock_exists.side_effect = lambda: True
        result = harbor_to_compose_config(mock_task)

    service = result.services["default"]
    assert service.cpus is None
    assert service.mem_limit is None
    assert service.environment == {"CPU_COUNT": "4", "MEM": "2G"}


def test_harbor_to_compose_config_compose_yaml_no_internet_overrides_network_mode():
    """Test that network_mode='no-network' forces network_mode=none even when compose file sets it."""
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.env = {}
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_env_config.network_mode = "no-network"
    mock_task.config.environment = mock_env_config

    compose_yaml_content = """
services:
  default:
    image: python:3.11
    network_mode: bridge
"""

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=compose_yaml_content)),
    ):
        mock_exists.side_effect = lambda: True

        result = harbor_to_compose_config(mock_task)

        service = result.services["default"]
        assert service.network_mode == "none"


def test_harbor_to_compose_config_compose_yaml_preserves_custom_network_mode():
    """Test that compose file's network_mode is preserved when network_mode='public'."""
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.env = {}
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_env_config.network_mode = "public"
    mock_task.config.environment = mock_env_config

    compose_yaml_content = """
services:
  default:
    image: python:3.11
    network_mode: host
"""

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=compose_yaml_content)),
    ):
        mock_exists.side_effect = lambda: True

        result = harbor_to_compose_config(mock_task)

        service = result.services["default"]
        assert service.network_mode == "host"


def test_harbor_to_compose_config_compose_yaml_no_network_mode_left_unset():
    """Test that compose file without network_mode is left unset when network_mode='public'.

    This preserves Docker Compose's default project network with inter-service DNS,
    matching Harbor's behavior of not touching network_mode when the network is allowed.
    """
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.env = {}
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_env_config.network_mode = "public"
    mock_task.config.environment = mock_env_config

    compose_yaml_content = """
services:
  default:
    image: python:3.11
"""

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=compose_yaml_content)),
    ):
        mock_exists.side_effect = lambda: True

        result = harbor_to_compose_config(mock_task)

        service = result.services["default"]
        assert service.network_mode is None


def test_harbor_to_compose_config_network_mode_field_no_network():
    """``network_mode='no-network'`` isolates services (Dockerfile branch)."""
    mock_task = Mock()
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/task/environment")

    mock_env_config = Mock()
    mock_env_config.env = {}
    mock_env_config.cpus = 1
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.network_mode = "no-network"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_task.config.environment = mock_env_config

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)
        assert result.services["default"].network_mode == "none"


@pytest.mark.parametrize("network_mode", ["public", "allowlist"])
def test_harbor_to_compose_config_network_mode_field_allows_network(
    network_mode: str,
):
    """``public``/``allowlist`` allow the network (bridge).

    ``allowlist`` is treated like ``public`` (binary network model); the
    loader emits a degraded-fidelity warning for it separately.
    """
    mock_task = Mock()
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/task/environment")

    mock_env_config = Mock()
    mock_env_config.env = {}
    mock_env_config.cpus = 1
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.network_mode = network_mode
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_task.config.environment = mock_env_config

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)
        assert result.services["default"].network_mode == "bridge"


def test_harbor_to_compose_config_deprecated_allow_internet_isolated():
    """A legacy ``allow_internet = false`` task.toml ends up network-isolated.

    Harbor's ``TaskConfig`` validator migrates the deprecated boolean to
    ``network_mode = no-network`` (and clears the boolean), so no special
    handling is needed on our side. Uses a real ``TaskConfig`` (not a Mock) to
    exercise that migration end to end.
    """
    with pytest.warns(DeprecationWarning, match="allow_internet"):
        config = TaskConfig.model_validate_toml(
            '[environment]\ndocker_image = "ubuntu:latest"\nallow_internet = false\n'
        )
    assert config.environment.network_mode == NetworkMode.NO_NETWORK
    assert config.environment.allow_internet is None

    mock_task = Mock()
    mock_task.name = "legacy-task"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/task/environment")
    mock_task.config.environment = config.environment

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)
        assert result.services["default"].network_mode == "none"


# A kumo-style compose: per-service ``networks:`` plus a top-level network.
# ``network_mode`` and ``networks`` are mutually exclusive in compose.
EXPLICIT_NETWORKS_YAML = """\
services:
  main:
    image: python:3.11
    networks:
      - internal
  verifier:
    image: python:3.11
    networks:
      - internal
networks:
  internal:
    driver: bridge
"""


def test_compose_yaml_explicit_networks_not_clobbered_by_network_mode():
    """Explicit ``networks:`` are never clobbered with ``network_mode``.

    Reproduces the kumo/* failure where docker compose rejected the project
    with "service X declares mutually exclusive network_mode and networks".
    ``network_mode='public'`` means isolation isn't even requested, so no
    ``network_mode`` may be forced onto services with explicit ``networks:``.
    """
    mock_task = Mock()
    mock_task.name = "kumo-style-task"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/task/environment")
    mock_task.config.environment = Mock()
    mock_task.config.environment.cpus = 4
    mock_task.config.environment.memory_mb = 8192
    mock_task.config.environment.gpus = 0
    mock_task.config.environment.gpu_types = None
    mock_task.config.environment.healthcheck = None
    mock_task.config.environment.env = {}
    mock_task.config.environment.network_mode = "public"
    mock_task.config.verifier.env = {}

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=EXPLICIT_NETWORKS_YAML)),
    ):
        mock_exists.side_effect = lambda: True
        result = harbor_to_compose_config(mock_task)

    # Explicit networks are preserved; no mutually-exclusive network_mode added.
    for svc in result.services.values():
        assert svc.networks == ["internal"]
        assert svc.network_mode is None


def test_compose_yaml_no_network_leaves_explicit_networks_alone():
    """No-network isolation leaves a service's explicit ``networks:`` intact.

    User-defined networks already isolate the service from the host, so we
    leave author intent untouched rather than add a mutually-exclusive
    ``network_mode`` that produces an invalid compose project.
    """
    mock_task = Mock()
    mock_task.name = "kumo-style-task"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/task/environment")
    mock_task.config.environment = Mock()
    mock_task.config.environment.cpus = 4
    mock_task.config.environment.memory_mb = 8192
    mock_task.config.environment.gpus = 0
    mock_task.config.environment.gpu_types = None
    mock_task.config.environment.healthcheck = None
    mock_task.config.environment.env = {}
    mock_task.config.environment.network_mode = "no-network"
    mock_task.config.verifier.env = {}

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=EXPLICIT_NETWORKS_YAML)),
    ):
        mock_exists.side_effect = lambda: True
        result = harbor_to_compose_config(mock_task)

    for svc in result.services.values():
        assert svc.networks == ["internal"]
        assert svc.network_mode is None


def test_compose_yaml_no_network_still_isolates_services_without_networks():
    """No-network services without explicit ``networks:`` still get ``none``.

    The isolation path must not regress for the common multi-service case.
    """
    mock_task = _make_multi_service_task(network_mode="no-network")

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=MULTI_SERVICE_YAML)),
    ):
        mock_exists.side_effect = lambda: True
        result = harbor_to_compose_config(mock_task)

    assert result.services["main"].network_mode == "none"
    assert result.services["helper"].network_mode == "none"


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
    mock_env_config.env = {}
    mock_env_config.cpus = 2.0
    mock_env_config.memory_mb = 4096
    mock_env_config.docker_image = "python:3.11"
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_task.config.environment = mock_env_config

    mock_verifier_config = Mock()
    mock_verifier_config.timeout_sec = 300
    mock_task.config.verifier = mock_verifier_config
    mock_task.config.task = None
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
    mock_env_config.env = {}
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.network_mode = "no-network"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_task.config.environment = mock_env_config

    mock_verifier_config = Mock()
    mock_verifier_config.timeout_sec = 60
    mock_task.config.verifier = mock_verifier_config
    mock_task.config.task = None
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
        # 6GB minimum is applied (config has 2048m which is below minimum)
        assert service.mem_limit == "6144m"
        assert service.network_mode == "none"


def test_harbor_to_compose_config_with_gpu_settings():
    """Test GPU configuration is correctly applied to ComposeService."""
    # Setup mock Harbor task with GPU requirements
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.env = {}
    mock_env_config.cpus = 2.0
    mock_env_config.memory_mb = 4096
    mock_env_config.docker_image = "nvidia/cuda:12.0-base"
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 2
    mock_env_config.gpu_types = ["H100", "A100"]
    mock_env_config.healthcheck = None
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
    mock_env_config.env = {}
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
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
    mock_env_config.env = {}
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = "tensorflow/tensorflow:latest-gpu"
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 1
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
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
    mock_task.config.environment.healthcheck = None
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
    mock_env_config.env = {}
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = "python:3.11"
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_task.config.environment = mock_env_config

    # Mock verifier config with env vars
    mock_verifier_config = Mock()
    mock_verifier_config.timeout_sec = 600
    mock_verifier_config.env = {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "MODEL_NAME": "gpt-4o",
    }
    mock_task.config.verifier = mock_verifier_config
    mock_task.config.task = None
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
    mock_env_config.env = {}
    mock_env_config.cpus = 1.0
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = "python:3.11"
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_task.config.environment = mock_env_config

    # Mock verifier config without env vars (Harbor's default empty-dict).
    mock_verifier_config = Mock()
    mock_verifier_config.timeout_sec = 600
    mock_verifier_config.env = {}
    mock_task.config.verifier = mock_verifier_config
    mock_task.config.task = None
    mock_task.config.model_dump = Mock(return_value={"test": "config"})

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_task_to_sample(mock_task)

        assert isinstance(result, Sample)
        assert result.metadata is not None
        assert "verifier_env" in result.metadata
        assert result.metadata["verifier_env"] == {}


def test_harbor_task_to_sample_with_package_info():
    """When ``[task]`` is present in task.toml, surface package metadata."""
    mock_task = Mock()
    mock_task.name = "harbor/hello-world"
    mock_task.instruction = "Say hello."
    mock_task.task_dir = Path("/tasks/harbor-hello-world")

    mock_paths = Mock()
    mock_paths.environment_dir = Path("/tasks/harbor-hello-world/environment")
    mock_paths.test_path = Path("/tasks/harbor-hello-world/tests/test.sh")
    mock_paths.tests_dir = Path("/tasks/harbor-hello-world/tests")
    mock_paths.solution_dir = Path("/tasks/harbor-hello-world/solution")
    mock_paths.solve_path = Path("/tasks/harbor-hello-world/solution/solve.sh")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.env = {}
    mock_env_config.cpus = 1
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = "python:3.11"
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_task.config.environment = mock_env_config

    mock_task.config.verifier = Mock(timeout_sec=60, env={}, user=None)
    mock_task.config.agent = Mock(user=None)
    mock_task.config.solution = Mock(env={})
    mock_task.config.model_dump = Mock(return_value={})

    # Realistic PackageInfo payload — note ``authors`` is a list of pydantic
    # models in production; we mock model_dump() to return its dict form.
    package = Mock()
    package.name = "harbor/hello-world"
    package.description = "A friendly greeting"
    package.keywords = ["hello", "world"]
    author = Mock()
    author.model_dump = Mock(
        return_value={"name": "Alice", "email": "alice@example.com"}
    )
    package.authors = [author]
    mock_task.config.task = package

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_task_to_sample(mock_task)

    assert result.metadata is not None
    assert result.metadata["package_name"] == "harbor/hello-world"
    assert result.metadata["package_description"] == "A friendly greeting"
    assert result.metadata["package_keywords"] == ["hello", "world"]
    assert result.metadata["package_authors"] == [
        {"name": "Alice", "email": "alice@example.com"}
    ]


@pytest.mark.parametrize(
    "verifier_config,agent_config,expected_verifier,expected_agent",
    [
        pytest.param(
            Mock(timeout_sec=60, env={}, user=None),
            Mock(user=None),
            None,
            None,
            id="both-none",
        ),
        pytest.param(
            Mock(timeout_sec=60, env={}, user="agent"),
            Mock(user="root"),
            "agent",
            "root",
            id="both-strings",
        ),
        pytest.param(
            Mock(timeout_sec=60, env={}, user=1000),
            Mock(user="agent"),
            "1000",
            "agent",
            id="int-uid-coerced-mock",
        ),
        pytest.param(
            VerifierConfig(timeout_sec=60, user=1000),
            AgentConfig(user="agent"),
            "1000",
            "agent",
            id="int-uid-coerced-real-pydantic",
        ),
    ],
)
def test_harbor_task_to_sample_user_fields(
    verifier_config: Any,
    agent_config: Any,
    expected_verifier: str | None,
    expected_agent: str | None,
) -> None:
    """User fields from ``[verifier]`` / ``[agent]`` flow into ``Sample.metadata``."""
    mock_task = Mock()
    mock_task.name = "test-task"
    mock_task.instruction = "x"
    mock_task.task_dir = Path("/t")
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/t/env")
    mock_task.paths.test_path = Path("/t/tests/test.sh")
    mock_task.paths.tests_dir = Path("/t/tests")
    mock_task.paths.solution_dir = Path("/t/solution")
    mock_task.paths.solve_path = Path("/t/solution/solve.sh")

    mock_env_config = Mock()
    mock_env_config.env = {}
    mock_env_config.cpus = 1
    mock_env_config.memory_mb = 2048
    mock_env_config.docker_image = "python:3.11"
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_task.config.environment = mock_env_config

    mock_task.config.verifier = verifier_config
    mock_task.config.agent = agent_config
    mock_task.config.solution = Mock(env={})
    mock_task.config.task = None
    mock_task.config.model_dump = Mock(return_value={})

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_task_to_sample(mock_task)

    assert result.metadata is not None
    assert result.metadata["verifier_user"] == expected_verifier
    assert result.metadata["agent_user"] == expected_agent


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
    mock_env_config.env = {}
    mock_env_config.cpus = 2
    mock_env_config.memory_mb = 4096
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 1
    mock_env_config.gpu_types = ["H100"]
    mock_env_config.healthcheck = None
    mock_task.config.environment = mock_env_config

    mock_verifier_config = Mock()
    mock_verifier_config.timeout_sec = 300
    mock_verifier_config.env = {}
    mock_verifier_config.user = None
    mock_task.config.verifier = mock_verifier_config

    mock_agent_config = Mock()
    mock_agent_config.user = None
    mock_task.config.agent = mock_agent_config

    mock_solution_config = Mock()
    mock_solution_config.env = {}
    mock_task.config.solution = mock_solution_config

    mock_task.config.task = None
    mock_task.config.model_dump = Mock(return_value={})

    return mock_task


@pytest.mark.parametrize(
    "override_cpus,override_memory_mb,override_gpus,expected_cpus,expected_memory,expected_gpus",
    [
        # Override all parameters
        (8, 16384, 4, 8, "16384m", 4),
        # Override only cpus (memory uses 6GB minimum since config has 4GB)
        (16, None, None, 16, "6144m", 1),
        # Override only memory
        (None, 8192, None, 2, "8192m", 1),
        # Override only gpus (memory uses 6GB minimum since config has 4GB)
        (None, None, 2, 2, "6144m", 2),
        # Override to zero gpus (memory uses 6GB minimum since config has 4GB)
        (None, None, 0, 2, "6144m", None),
        # No overrides (memory uses 6GB minimum since config has 4GB)
        (None, None, None, 2, "6144m", 1),
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


MULTI_SERVICE_YAML = """\
services:
  main:
    image: python:3.11
    command: tail -f /dev/null
  helper:
    image: redis:7
"""


def _make_multi_service_task(
    cpus: float = 4,
    memory_mb: int = 8192,
    gpus: int = 0,
    gpu_types: list[str] | None = None,
    network_mode: str = "public",
) -> Mock:
    mock_task = Mock()
    mock_task.name = "multi-svc-task"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/task/environment")
    mock_task.config.environment = Mock()
    mock_task.config.environment.cpus = cpus
    mock_task.config.environment.memory_mb = memory_mb
    mock_task.config.environment.gpus = gpus
    mock_task.config.environment.gpu_types = gpu_types
    mock_task.config.environment.healthcheck = None
    mock_task.config.environment.network_mode = network_mode
    mock_task.config.verifier.env = {}
    mock_task.config.environment.env = {}
    return mock_task


def test_multi_service_resources_only_on_default_service():
    """Only the default ('main') service gets resource limits."""
    mock_task = _make_multi_service_task(cpus=4, memory_mb=8192)

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=MULTI_SERVICE_YAML)),
    ):
        mock_exists.side_effect = lambda: True
        result = harbor_to_compose_config(mock_task)

    # Default service ("main") gets resources
    assert result.services["main"].cpus == 4
    assert result.services["main"].mem_limit == "8192m"

    # Sidecar ("helper") is untouched
    assert result.services["helper"].cpus is None
    assert result.services["helper"].mem_limit is None


def test_multi_service_overrides_only_on_default_service():
    """Overrides are applied only to the default service."""
    mock_task = _make_multi_service_task()

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=MULTI_SERVICE_YAML)),
    ):
        mock_exists.side_effect = lambda: True
        result = harbor_to_compose_config(
            mock_task, override_cpus=2, override_memory_mb=4096
        )

    assert result.services["main"].cpus == 2
    assert result.services["main"].mem_limit == "4096m"
    assert result.services["helper"].cpus is None
    assert result.services["helper"].mem_limit is None


def test_multi_service_gpu_only_on_default_service():
    """GPU deploy config is applied only to the default service."""
    mock_task = _make_multi_service_task(gpus=1, gpu_types=["H100"])

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=MULTI_SERVICE_YAML)),
    ):
        mock_exists.side_effect = lambda: True
        result = harbor_to_compose_config(mock_task)

    assert result.services["main"].deploy is not None
    assert result.services["helper"].deploy is None


def test_multi_service_network_isolation_all_services():
    """Network isolation applies to all services, not just default."""
    mock_task = _make_multi_service_task(network_mode="no-network")

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=MULTI_SERVICE_YAML)),
    ):
        mock_exists.side_effect = lambda: True
        result = harbor_to_compose_config(mock_task)

    assert result.services["main"].network_mode == "none"
    assert result.services["helper"].network_mode == "none"


def test_multi_service_x_default_takes_priority():
    """A service with x-default: true is chosen over name-based matching."""
    yaml_with_x_default = """\
services:
  main:
    image: python:3.11
  sidecar:
    image: redis:7
    x-default: true
"""
    mock_task = _make_multi_service_task(cpus=8, memory_mb=16384)

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=yaml_with_x_default)),
    ):
        mock_exists.side_effect = lambda: True
        result = harbor_to_compose_config(mock_task)

    # x-default service gets resources, not "main"
    assert result.services["sidecar"].cpus == 8
    assert result.services["sidecar"].mem_limit == "16384m"
    assert result.services["main"].cpus is None
    assert result.services["main"].mem_limit is None


def test_multi_service_first_service_fallback():
    """When no service is named 'default'/'main' or has x-default, first wins."""
    yaml_no_default = """\
services:
  app:
    image: python:3.11
  db:
    image: postgres:16
"""
    mock_task = _make_multi_service_task(cpus=2, memory_mb=8192)

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=yaml_no_default)),
    ):
        mock_exists.side_effect = lambda: True
        result = harbor_to_compose_config(mock_task)

    # First service gets resources
    assert result.services["app"].cpus == 2
    assert result.services["app"].mem_limit == "8192m"
    assert result.services["db"].cpus is None
    assert result.services["db"].mem_limit is None


def test_expand_compose_vars_basic():
    """Test that ${VAR} references are expanded in compose YAML."""
    mock_task = Mock()
    mock_task.name = "my-task"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/cache/tasks/abc/my-task/environment")
    mock_task.config.verifier.env = {}
    mock_task.config.environment.env = {}

    raw = """\
services:
  main:
    build:
      context: ${CONTEXT_DIR}
      dockerfile: Dockerfile
    image: ${MAIN_IMAGE_NAME}
    deploy:
      resources:
        limits:
          cpus: ${CPUS}
          memory: ${MEMORY}
"""
    result = _expand_compose_vars(raw, mock_task, cpus=4.0, memory_mb=8192)

    assert "${" not in result
    assert "/cache/tasks/abc/my-task/environment" in result
    assert "hb__my-task" in result
    assert "cpus: 4" in result
    assert "memory: 8192M" in result


def test_expand_compose_vars_no_vars():
    """Test that YAML without variables is returned unchanged."""
    mock_task = Mock()
    mock_task.name = "t"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/env")
    mock_task.config.verifier.env = {}
    mock_task.config.environment.env = {}

    raw = "services:\n  default:\n    image: python:3.12\n"
    assert _expand_compose_vars(raw, mock_task, 1.0, 2048) == raw


def test_expand_compose_vars_unknown_left_as_is():
    """Test that unknown variables are left as literal strings."""
    mock_task = Mock()
    mock_task.name = "t"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/env")
    mock_task.config.verifier.env = {}
    mock_task.config.environment.env = {}

    raw = "image: ${UNKNOWN_VAR}"
    result = _expand_compose_vars(raw, mock_task, 1.0, 2048)
    assert result == "image: ${UNKNOWN_VAR}"


@pytest.mark.parametrize(
    "raw,cpus,expected",
    [
        # Unknown var falls back to the default.
        ("image: ${UNKNOWN:-fallback-image}", 1.0, "image: fallback-image"),
        # Known var wins over the default.
        ("cpus: ${CPUS:-99}", 4.0, "cpus: 4"),
    ],
)
def test_expand_compose_vars_default_syntax(
    raw: str, cpus: float, expected: str
) -> None:
    """``${VAR:-default}`` is resolved per Harbor 0.6.3+ template syntax."""
    mock_task = Mock()
    mock_task.name = "t"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/env")
    mock_task.config.verifier.env = {}
    mock_task.config.environment.env = {}

    assert _expand_compose_vars(raw, mock_task, cpus, memory_mb=2048) == expected


def test_expand_compose_vars_image_name_sanitized_for_package_task():
    """Sanitize ``MAIN_IMAGE_NAME`` for package-style task names."""
    mock_task = Mock()
    mock_task.name = "harbor/Hello.World"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/env")
    mock_task.config.verifier.env = {}
    mock_task.config.environment.env = {}

    result = _expand_compose_vars("image: ${MAIN_IMAGE_NAME}", mock_task, 1.0, 2048)
    assert result == "image: hb__harbor-hello.world"


def test_expand_compose_vars_test_dir_from_verifier_env():
    """Test that TEST_DIR is pulled from verifier env if set."""
    mock_task = Mock()
    mock_task.name = "t"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/env")
    mock_task.config.verifier.env = {"TEST_DIR": "/custom/tests"}
    mock_task.config.environment.env = {}

    raw = "TEST_DIR=${TEST_DIR}"
    result = _expand_compose_vars(raw, mock_task, 1.0, 2048)
    assert result == "TEST_DIR=/custom/tests"


@pytest.mark.parametrize(
    "task_env,raw,cpus,expected_substring,reason",
    [
        # Plain literal values from task.toml become substitutable in compose.
        (
            {"LOG_LEVEL": "DEBUG"},
            "env: ${LOG_LEVEL}",
            1.0,
            "env: DEBUG",
            "task-env literal value substitutes",
        ),
        # Built-in keys (CPUS, MEMORY, …) win on collision via setdefault.
        (
            {"CPUS": "999"},
            "cpus: ${CPUS}",
            4.0,
            "cpus: 4",
            "built-in CPUS wins over task-env shadow",
        ),
    ],
)
def test_expand_compose_vars_task_env(
    task_env: dict[str, str],
    raw: str,
    cpus: float,
    expected_substring: str,
    reason: str,
) -> None:
    """``[environment].env`` entries flow into the substitution map."""
    mock_task = Mock()
    mock_task.name = "t"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/env")
    mock_task.config.verifier.env = {}
    mock_task.config.environment.env = task_env

    result = _expand_compose_vars(raw, mock_task, cpus, 2048)
    assert expected_substring in result, reason


def _make_expand_task(task_env: dict[str, str]) -> Mock:
    mock_task = Mock()
    mock_task.name = "t"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/env")
    mock_task.config.verifier.env = {}
    mock_task.config.environment.env = task_env
    return mock_task


def test_expand_compose_vars_resolves_host_ref_in_yaml(
    monkeypatch: pytest.MonkeyPatch,
):
    """A ``${HOST_VAR}`` in the compose text is baked in from ``os.environ``.

    Resolving orchestrator-side is what lets the secret reach a remote DinD
    provider whose ``docker compose`` can't see the host environment.
    """
    monkeypatch.setenv("MY_SECRET", "sk-resolved")
    mock_task = _make_expand_task({})

    result = _expand_compose_vars("env: ${MY_SECRET}", mock_task, 1.0, 2048)
    assert result == "env: sk-resolved"


def test_expand_compose_vars_resolves_host_ref_via_task_env(
    monkeypatch: pytest.MonkeyPatch,
):
    """A task-env value referencing a host var resolves to the host value."""
    monkeypatch.setenv("MY_SECRET", "sk-resolved")
    mock_task = _make_expand_task({"API_KEY": "${MY_SECRET}"})

    result = _expand_compose_vars("env: ${API_KEY}", mock_task, 1.0, 2048)
    assert result == "env: sk-resolved"


def test_expand_compose_vars_unknown_host_ref_left_literal(
    monkeypatch: pytest.MonkeyPatch,
):
    """An unknown ref with no default is left literal (compose YAML is lenient).

    Harbor lets ``docker compose`` resolve these at run-time, so we don't raise
    on bare compose-text references the orchestrator can't satisfy.
    """
    monkeypatch.delenv("TOTALLY_UNKNOWN_VAR", raising=False)
    mock_task = _make_expand_task({})

    result = _expand_compose_vars("env: ${TOTALLY_UNKNOWN_VAR}", mock_task, 1.0, 2048)
    assert result == "env: ${TOTALLY_UNKNOWN_VAR}"


def test_expand_compose_vars_missing_host_ref_in_task_env_raises(
    monkeypatch: pytest.MonkeyPatch,
):
    """A task-env value with an unset host var (no default) fails fast.

    Mirrors harbor's ``resolve_env_vars`` building ``_compose_task_env``.
    """
    monkeypatch.delenv("MISSING_VAR", raising=False)
    mock_task = _make_expand_task({"API_KEY": "${MISSING_VAR}"})

    with pytest.raises(ValueError, match="MISSING_VAR"):
        _expand_compose_vars("env: ${API_KEY}", mock_task, 1.0, 2048)


def test_expand_compose_vars_in_harbor_to_compose_config(tmp_path: Path):
    """Test end-to-end: compose YAML with variables is expanded before parsing."""
    env_dir = tmp_path / "environment"
    env_dir.mkdir()

    compose_yaml = env_dir / "docker-compose.yaml"
    compose_yaml.write_text("""\
services:
  default:
    build:
      context: ${CONTEXT_DIR}
      dockerfile: Dockerfile
    image: ${MAIN_IMAGE_NAME}
""")

    # Create a Dockerfile so the build context is valid
    (env_dir / "Dockerfile").write_text("FROM python:3.12\n")

    mock_task = Mock()
    mock_task.name = "test-task"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = env_dir
    mock_task.config.environment = Mock()
    mock_task.config.environment.cpus = 2
    mock_task.config.environment.memory_mb = 8192
    mock_task.config.environment.gpus = 0
    mock_task.config.environment.gpu_types = None
    mock_task.config.environment.healthcheck = None
    mock_task.config.environment.network_mode = "public"
    mock_task.config.environment.env = {}
    mock_task.config.verifier.env = {}

    result = harbor_to_compose_config(mock_task)

    service = result.services["default"]
    assert service.image == "hb__test-task"
    assert isinstance(service.build, ComposeBuild)
    assert service.build.context == str(env_dir)


def test_harbor_to_compose_config_compose_yaml_build_without_image_gets_stable_tag(
    tmp_path: Path,
):
    """Compose YAML services with ``build:`` but no ``image:`` get a deterministic tag.

    Without this, Compose auto-names the build as ``<project>-<service>`` —
    and the project name carries a random suffix that ``compose_cleanup_images``
    deletes on shutdown. The injected tag tracks the task name plus the
    service name so multi-service compose files don't collide on a single
    image.
    """
    env_dir = tmp_path / "environment"
    env_dir.mkdir()

    # Two services that both build, neither sets image: — the case that
    # vanilla docker-compose tutorials produce.
    compose_yaml = env_dir / "docker-compose.yaml"
    compose_yaml.write_text("""\
services:
  default:
    build:
      context: ${CONTEXT_DIR}
      dockerfile: Dockerfile
  worker:
    build:
      context: ${CONTEXT_DIR}
""")
    (env_dir / "Dockerfile").write_text("FROM python:3.12\n")

    mock_task = Mock()
    mock_task.name = "Compose/Multi-Service"  # exercise sanitization too
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = env_dir
    mock_task.config.environment = Mock()
    mock_task.config.environment.cpus = 1
    mock_task.config.environment.memory_mb = 6144
    mock_task.config.environment.gpus = 0
    mock_task.config.environment.gpu_types = None
    mock_task.config.environment.healthcheck = None
    mock_task.config.environment.network_mode = "public"
    mock_task.config.environment.env = {}
    mock_task.config.verifier.env = {}

    result = harbor_to_compose_config(mock_task)

    # Each service gets its own stable tag derived from task + service.
    assert result.services["default"].image == "hb__compose-multi-service__default"
    assert result.services["worker"].image == "hb__compose-multi-service__worker"
    # And neither tag starts with inspect_ai's random ``inspect-…`` project
    # prefix, so compose_cleanup_images won't delete them.
    assert not result.services["default"].image.startswith("inspect-")
    assert not result.services["worker"].image.startswith("inspect-")


def test_harbor_to_compose_config_compose_yaml_preserves_explicit_image(
    tmp_path: Path,
):
    """We never overwrite an image: that the task author already set.

    Catches a regression where the new tag-injection loop would clobber
    literal images, ``${MAIN_IMAGE_NAME}`` references, or any other
    explicit tag the task ships with.
    """
    env_dir = tmp_path / "environment"
    env_dir.mkdir()

    compose_yaml = env_dir / "docker-compose.yaml"
    compose_yaml.write_text("""\
services:
  default:
    build:
      context: ${CONTEXT_DIR}
    image: my-registry/my-image:v1.2.3
  helper:
    image: redis:7
""")
    (env_dir / "Dockerfile").write_text("FROM python:3.12\n")

    mock_task = Mock()
    mock_task.name = "explicit-image-task"
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = env_dir
    mock_task.config.environment = Mock()
    mock_task.config.environment.cpus = 1
    mock_task.config.environment.memory_mb = 6144
    mock_task.config.environment.gpus = 0
    mock_task.config.environment.gpu_types = None
    mock_task.config.environment.healthcheck = None
    mock_task.config.environment.network_mode = "public"
    mock_task.config.environment.env = {}
    mock_task.config.verifier.env = {}

    result = harbor_to_compose_config(mock_task)

    assert result.services["default"].image == "my-registry/my-image:v1.2.3"
    # Pure pull-only service (no build:) is also left alone.
    assert result.services["helper"].image == "redis:7"


@pytest.mark.parametrize(
    "config_memory_mb,expected_memory",
    [
        (2048, "6144m"),  # 2GB (Harbor default) -> 6GB minimum
        (4096, "6144m"),  # 4GB -> 6GB minimum
        (6144, "6144m"),  # Exactly 6GB -> 6GB
        (8192, "8192m"),  # 8GB -> respected (above minimum)
        (16384, "16384m"),  # 16GB -> respected (above minimum)
    ],
)
def test_harbor_to_compose_config_memory_minimum(
    config_memory_mb: int, expected_memory: str
):
    """Test that 6GB minimum is enforced for low/unset values, but higher values are respected."""
    mock_task = Mock()
    mock_paths = Mock()
    mock_paths.environment_dir = Path("/task/environment")
    mock_task.paths = mock_paths

    mock_env_config = Mock()
    mock_env_config.env = {}
    mock_env_config.cpus = 2
    mock_env_config.memory_mb = config_memory_mb
    mock_env_config.docker_image = "ubuntu:latest"
    mock_env_config.network_mode = "public"
    mock_env_config.gpus = 0
    mock_env_config.gpu_types = None
    mock_env_config.healthcheck = None
    mock_task.config.environment = mock_env_config

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)

        service = result.services["default"]
        assert service.mem_limit == expected_memory


def _make_healthcheck_task(
    healthcheck: HealthcheckConfig | None,
    name: str = "healthcheck-task",
) -> Mock:
    """A task mock whose ``[environment]`` carries only a healthcheck."""
    mock_task = Mock()
    mock_task.name = name
    mock_task.paths = Mock()
    mock_task.paths.environment_dir = Path("/task/environment")
    mock_task.config.environment = Mock()
    mock_task.config.environment.env = {}
    mock_task.config.environment.cpus = None
    mock_task.config.environment.memory_mb = None
    mock_task.config.environment.docker_image = "ubuntu:latest"
    mock_task.config.environment.gpus = 0
    mock_task.config.environment.gpu_types = None
    mock_task.config.environment.network_mode = "public"
    mock_task.config.environment.healthcheck = healthcheck
    mock_task.config.verifier.env = {}
    return mock_task


def test_healthcheck_mapped_on_programmatic_service():
    """A task.toml healthcheck lands on the generated default service."""
    mock_task = _make_healthcheck_task(
        HealthcheckConfig(
            command="curl -f http://localhost:8080/health",
            interval_sec=2.0,
            timeout_sec=10.0,
            start_period_sec=30.0,
            start_interval_sec=1.0,
            retries=5,
        )
    )

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)

    healthcheck = result.services["default"].healthcheck
    assert healthcheck is not None
    assert healthcheck.test == ["CMD-SHELL", "curl -f http://localhost:8080/health"]
    assert healthcheck.interval == "2s"
    assert healthcheck.timeout == "10s"
    assert healthcheck.start_period == "30s"
    assert healthcheck.start_interval == "1s"
    assert healthcheck.retries == 5


def test_healthcheck_absent_leaves_service_without_one():
    """No task.toml healthcheck means no compose healthcheck."""
    mock_task = _make_healthcheck_task(None)

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)

    assert result.services["default"].healthcheck is None


def test_healthcheck_defaults_omit_inert_start_interval():
    """``start_interval`` is dropped when there is no start period.

    Docker only uses it within the start period (as does Harbor's own loop),
    and it requires Docker Engine 25+.
    """
    mock_task = _make_healthcheck_task(HealthcheckConfig(command="test -f /ready"))

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)

    healthcheck = result.services["default"].healthcheck
    assert healthcheck is not None
    # Harbor's HealthcheckConfig defaults.
    assert healthcheck.interval == "5s"
    assert healthcheck.timeout == "30s"
    assert healthcheck.start_period == "0s"
    assert healthcheck.start_interval is None
    assert healthcheck.retries == 3


def test_healthcheck_fractional_seconds_render_as_whole_milliseconds():
    """Fractional seconds become ``ms``: Inspect's duration parser is integer-only.

    ``"1.5s"`` would parse as ``1s`` and ``"2.0s"`` as ``0s``, skewing the
    ``compose up --wait`` timeout Inspect derives from the healthcheck.
    """
    mock_task = _make_healthcheck_task(
        HealthcheckConfig(
            command="test -f /ready",
            interval_sec=1.5,
            timeout_sec=0.25,
            start_period_sec=2.0,
            start_interval_sec=0.5,
        )
    )

    with patch("pathlib.Path.exists", return_value=False):
        result = harbor_to_compose_config(mock_task)

    healthcheck = result.services["default"].healthcheck
    assert healthcheck is not None
    assert healthcheck.interval == "1500ms"
    assert healthcheck.timeout == "250ms"
    assert healthcheck.start_period == "2s"
    assert healthcheck.start_interval == "500ms"


def test_healthcheck_mapped_on_compose_yaml_default_service():
    """A task.toml healthcheck reaches the default service of a task's own compose."""
    mock_task = _make_healthcheck_task(HealthcheckConfig(command="test -f /ready"))
    compose_yaml = """
services:
  main:
    image: python:3.11
    x-default: true
  helper:
    image: redis:7
"""

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=compose_yaml)),
    ):
        mock_exists.side_effect = lambda: True
        result = harbor_to_compose_config(mock_task)

    healthcheck = result.services["main"].healthcheck
    assert healthcheck is not None
    assert healthcheck.test == ["CMD-SHELL", "test -f /ready"]
    # Sidecars keep their own (absent) healthcheck.
    assert result.services["helper"].healthcheck is None


def test_healthcheck_does_not_overwrite_one_declared_in_compose_yaml():
    """A compose-declared healthcheck wins, and the conflict is warned about."""
    mock_task = _make_healthcheck_task(HealthcheckConfig(command="test -f /ready"))
    compose_yaml = """
services:
  default:
    image: python:3.11
    healthcheck:
      test: ["CMD", "pg_isready"]
      retries: 7
"""

    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("builtins.open", mock_open(read_data=compose_yaml)),
    ):
        mock_exists.side_effect = lambda: True
        with pytest.warns(UserWarning, match="healthcheck-task"):
            result = harbor_to_compose_config(mock_task)

    healthcheck = result.services["default"].healthcheck
    assert healthcheck is not None
    assert healthcheck.test == ["CMD", "pg_isready"]
    assert healthcheck.retries == 7
