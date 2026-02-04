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


def harbor_to_compose_config(harbor_task: HarborTask) -> ComposeConfig:
    """Convert Harbor task environment to Inspect ComposeConfig."""
    env_dir = harbor_task.paths.environment_dir
    compose_yaml_path = env_dir / "docker-compose.yaml"
    dockerfile_path = env_dir / "Dockerfile"
    env_config = harbor_task.config.environment

    # Use existing docker-compose.yaml if present
    if compose_yaml_path.exists():
        with open(compose_yaml_path) as f:
            compose_dict = yaml.safe_load(f)

        compose_config = ComposeConfig(**compose_dict)

        # Apply resource limits from Harbor config to services
        if compose_config.services:
            cpus = float(env_config.cpus) if env_config.cpus is not None else 1.0
            memory_mb = env_config.memory_mb if env_config.memory_mb is not None else 2048
            # Note: storage_mb is not currently supported by Inspect AI's ComposeService

            for service in compose_config.services.values():
                service.cpus = cpus
                service.mem_limit = f"{memory_mb}m"

        return compose_config

    # Build programmatically from Dockerfile or docker_image
    cpus = float(env_config.cpus) if env_config.cpus is not None else 1.0
    memory_mb = env_config.memory_mb if env_config.memory_mb is not None else 2048
    # Note: storage_mb is not currently supported by Inspect AI's ComposeService

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
        mem_limit=f"{memory_mb}m",
        command="tail -f /dev/null",
        init=True,
        network_mode="bridge" if env_config.allow_internet else "none",
    )

    return ComposeConfig(services={"default": service})


def harbor_task_to_sample(harbor_task: HarborTask) -> Sample:
    """Convert a Harbor task to an Inspect AI Sample."""
    compose_config = harbor_to_compose_config(harbor_task)
    verifier_timeout_sec = harbor_task.config.verifier.timeout_sec

    return Sample(
        input=harbor_task.instruction,
        id=harbor_task.name,
        sandbox=SandboxEnvironmentSpec("docker", compose_config),
        # Store Harbor task metadata for scorer to access later
        # (tests_dir will be used by scorer to copy tests at scoring time)
        metadata={
            "task_name": harbor_task.name,
            "task_dir": str(harbor_task.task_dir),
            "test_path": str(harbor_task.paths.test_path),
            "tests_dir": str(harbor_task.paths.tests_dir),
            "solution_dir": str(harbor_task.paths.solution_dir),
            "solve_path": str(harbor_task.paths.solve_path),
            "verifier_timeout_sec": verifier_timeout_sec,
            "harbor_config": harbor_task.config.model_dump(),
        },
    )
