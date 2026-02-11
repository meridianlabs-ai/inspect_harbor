"""Converters for Harbor tasks to Inspect AI structures."""

import yaml
from harbor.models.task.task import Task as HarborTask
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
            compose_dict = yaml.safe_load(f)

        compose_config = ComposeConfig(**compose_dict)

        # Apply resource limits from Harbor config to services
        if compose_config.services:
            for service in compose_config.services.values():
                service.cpus = cpus
                service.mem_limit = f"{memory_mb}m" if memory_mb is not None else None
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
