"""Converters for Harbor tasks to Inspect AI structures."""

import re

import yaml
from harbor.models.task.task import Task as HarborTask
from harbor.models.trial.paths import EnvironmentPaths
from inspect_ai.dataset import Sample
from inspect_ai.util import (
    ComposeBuild,
    ComposeConfig,
    ComposeService,
    SandboxEnvironmentSpec,
)
from inspect_ai.util._sandbox.compose import (
    ComposeDeploy,
    ComposeDeviceReservation,
    ComposeResourceConfig,
    ComposeResourceReservations,
)


def harbor_to_compose_config(
    harbor_task: HarborTask,
    override_cpus: int | None = None,
    override_memory_mb: int | None = None,
    override_gpus: int | None = None,
) -> ComposeConfig:
    """Convert Harbor task environment to Inspect ComposeConfig.

    Args:
        harbor_task: The Harbor task to convert.
        override_cpus: Override the number of CPUs for the environment.
        override_memory_mb: Override the memory (in MB) for the environment.
        override_gpus: Override the number of GPUs for the environment.

    Returns:
        ComposeConfig: The compose configuration for the task.
    """
    env_dir = harbor_task.paths.environment_dir
    compose_yaml_path = env_dir / "docker-compose.yaml"
    dockerfile_path = env_dir / "Dockerfile"
    env_config = harbor_task.config.environment

    # Extract resource configuration from Harbor config, applying overrides
    cpus = (
        float(override_cpus)
        if override_cpus is not None
        else (float(env_config.cpus) if env_config.cpus is not None else 1.0)
    )

    # Harbor's default of 2048 MB (2 GB) is too restrictive for modern agents.
    # Enforce a minimum of 6144 MB (6 GB) unless explicitly overridden.
    MIN_MEMORY_MB = 6144  # 6 GB
    memory_mb = (
        override_memory_mb
        if override_memory_mb is not None
        else max(env_config.memory_mb or 0, MIN_MEMORY_MB)
    )

    gpus = (
        override_gpus
        if override_gpus is not None
        else (env_config.gpus if env_config.gpus is not None else 0)
    )
    gpu_types = env_config.gpu_types
    gpu_deploy = _create_gpu_deploy_config(gpus, gpu_types)

    # Use existing docker-compose.yaml if present
    if compose_yaml_path.exists():
        with open(compose_yaml_path, encoding="utf-8") as f:
            raw_yaml = f.read()

        raw_yaml = _expand_compose_vars(raw_yaml, harbor_task, cpus, memory_mb)
        compose_dict = yaml.safe_load(raw_yaml)
        compose_config = ComposeConfig(**compose_dict)

        # Apply resource limits and network mode from Harbor config to services
        if compose_config.services:
            for service in compose_config.services.values():
                service.cpus = cpus
                service.mem_limit = f"{memory_mb}m" if memory_mb is not None else None
                # Harbor's behavior: allow_internet=False forces network
                # isolation; otherwise don't touch network_mode.
                if not env_config.allow_internet:
                    service.network_mode = "none"
                if gpu_deploy:
                    service.deploy = gpu_deploy

        return compose_config
    else:
        # Build programmatically from Dockerfile or docker_image
        service = ComposeService(
            # Use prebuilt image if specified, otherwise will build from Dockerfile
            image=env_config.docker_image if env_config.docker_image else None,
            # Use Dockerfile if it exists and no prebuilt image specified
            build=(
                ComposeBuild(context=str(env_dir))
                if dockerfile_path.exists() and not env_config.docker_image
                else None
            ),
            cpus=cpus,
            mem_limit=f"{memory_mb}m" if memory_mb is not None else None,
            command="tail -f /dev/null",
            init=True,
            network_mode="bridge" if env_config.allow_internet else "none",
            deploy=gpu_deploy,
        )

        return ComposeConfig(services={"default": service})


def harbor_task_to_sample(
    harbor_task: HarborTask,
    sandbox_env_name: str = "docker",
    override_cpus: int | None = None,
    override_memory_mb: int | None = None,
    override_gpus: int | None = None,
) -> Sample:
    """Convert a Harbor task to an Inspect AI Sample.

    Args:
        harbor_task: The Harbor task to convert.
        sandbox_env_name: Sandbox environment name (default: "docker").
        override_cpus: Override the number of CPUs for the environment.
        override_memory_mb: Override the memory (in MB) for the environment.
        override_gpus: Override the number of GPUs for the environment.

    Returns:
        Sample: Inspect AI sample with sandbox configuration.
    """
    compose_config = harbor_to_compose_config(
        harbor_task,
        override_cpus=override_cpus,
        override_memory_mb=override_memory_mb,
        override_gpus=override_gpus,
    )

    return Sample(
        input=harbor_task.instruction,
        id=harbor_task.name,
        sandbox=SandboxEnvironmentSpec(sandbox_env_name, compose_config),
        # Store Harbor task metadata for scorer to access later
        # (tests_dir will be used by scorer to copy tests at scoring time)
        metadata={
            "task_name": harbor_task.name,
            "task_dir": str(harbor_task.task_dir),
            "test_path": str(harbor_task.paths.test_path),
            "tests_dir": str(harbor_task.paths.tests_dir),
            "solution_dir": str(harbor_task.paths.solution_dir),
            "solve_path": str(harbor_task.paths.solve_path),
            "verifier_timeout_sec": harbor_task.config.verifier.timeout_sec,
            "verifier_env": harbor_task.config.verifier.env or {},
            "solution_env": harbor_task.config.solution.env or {},
            "harbor_config": harbor_task.config.model_dump(),
        },
    )


def _create_gpu_deploy_config(
    gpus: int, gpu_types: list[str] | None
) -> ComposeDeploy | None:
    """Create GPU deployment configuration for ComposeService.

    Args:
        gpus: Number of GPUs to reserve (0 means no GPUs).
        gpu_types: List of acceptable GPU types (e.g., ['H100', 'A100']).
                   Stored in device options for informational purposes.

    Returns:
        ComposeDeploy configuration with GPU reservations, or None if gpus=0.
    """
    if gpus <= 0:
        return None

    device_options = {}
    if gpu_types:
        # Store GPU types in options for potential use by sandbox providers
        device_options["gpu_types"] = ",".join(gpu_types)

    device_reservation = ComposeDeviceReservation(
        count=gpus,
        capabilities=["gpu"],
        options=device_options if device_options else None,
    )

    return ComposeDeploy(
        resources=ComposeResourceConfig(
            reservations=ComposeResourceReservations(devices=[device_reservation])
        )
    )


def _expand_compose_vars(
    raw_yaml: str,
    harbor_task: HarborTask,
    cpus: float,
    memory_mb: int,
) -> str:
    """Expand ${VAR} references in a Harbor docker-compose.yaml.

    Harbor passes these variables as environment variables to the
    ``docker compose`` process, which performs the substitution natively.

    The variable mapping matches:
    https://github.com/harbor-framework/harbor/blob/c935c6c06471e6cd891cda50f9e1b65e35bbd486/src/harbor/environments/daytona.py#L329

    Limitation: ``HOST_*`` paths (the host side of volume mounts) are set to
    the same container-side ``EnvironmentPaths`` values as ``ENV_*``. In
    Harbor's DinD setup these differ, but we cannot resolve host-side paths
    here because they depend on the sandbox provider.
    """
    if "${" not in raw_yaml:
        return raw_yaml

    env_dir = str(harbor_task.paths.environment_dir)
    task_name = harbor_task.name

    var_map: dict[str, str] = {
        "CONTEXT_DIR": env_dir,
        "MAIN_IMAGE_NAME": f"hb__{task_name}",
        "CPUS": str(int(cpus)),
        "MEMORY": f"{memory_mb}M",
        "HOST_VERIFIER_LOGS_PATH": str(EnvironmentPaths.verifier_dir),
        "HOST_AGENT_LOGS_PATH": str(EnvironmentPaths.agent_dir),
        "HOST_ARTIFACTS_PATH": str(EnvironmentPaths.artifacts_dir),
        "ENV_VERIFIER_LOGS_PATH": str(EnvironmentPaths.verifier_dir),
        "ENV_AGENT_LOGS_PATH": str(EnvironmentPaths.agent_dir),
        "ENV_ARTIFACTS_PATH": str(EnvironmentPaths.artifacts_dir),
    }

    task_env = harbor_task.config.verifier.env or {}
    if "TEST_DIR" in task_env:
        var_map["TEST_DIR"] = task_env["TEST_DIR"]
    else:
        var_map["TEST_DIR"] = str(EnvironmentPaths.tests_dir)

    def _replace(match: re.Match[str]) -> str:
        var_name = match.group(1)
        return var_map.get(var_name, match.group(0))

    return re.sub(r"\$\{([^}]+)}", _replace, raw_yaml)
