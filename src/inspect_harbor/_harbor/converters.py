"""Converters for Harbor tasks to Inspect AI structures."""

import re
from typing import Any

import yaml
from harbor.environments.docker.docker import _sanitize_docker_image_name
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
        override_cpus: Override the number of CPUs for the default service.
        override_memory_mb: Override the memory (in MB) for the default service.
        override_gpus: Override the number of GPUs for the default service.

    Returns:
        ComposeConfig: The compose configuration for the task.
    """
    env_dir = harbor_task.paths.environment_dir
    compose_yaml_path = env_dir / "docker-compose.yaml"
    dockerfile_path = env_dir / "Dockerfile"
    env_config = harbor_task.config.environment

    # Extract resource configuration from Harbor config, applying overrides
    cpus = float(override_cpus) if override_cpus is not None else float(env_config.cpus)

    # Harbor's default of 2048 MB (2 GB) is too restrictive for modern agents.
    # Enforce a minimum of 6144 MB (6 GB) unless explicitly overridden.
    MIN_MEMORY_MB = 6144  # 6 GB
    memory_mb = (
        override_memory_mb
        if override_memory_mb is not None
        else max(env_config.memory_mb, MIN_MEMORY_MB)
    )

    gpus = override_gpus if override_gpus is not None else env_config.gpus
    gpu_deploy = _create_gpu_deploy_config(gpus, env_config.gpu_types)

    # Use existing docker-compose.yaml if present
    if compose_yaml_path.exists():
        with open(compose_yaml_path, encoding="utf-8") as f:
            raw_yaml = f.read()

        raw_yaml = _expand_compose_vars(raw_yaml, harbor_task, cpus, memory_mb)
        compose_dict = yaml.safe_load(raw_yaml)
        compose_config = ComposeConfig(**compose_dict)

        if compose_config.services:
            _, default_service = _find_default_service(compose_config)
            default_service.cpus = cpus
            default_service.mem_limit = f"{memory_mb}m"
            if gpu_deploy:
                default_service.deploy = gpu_deploy

            # Network isolation applies to all services.
            if not env_config.allow_internet:
                for service in compose_config.services.values():
                    service.network_mode = "none"

            # Pin a stable `image:` tag make them reusable across runs.
            for svc_name, svc in compose_config.services.items():
                if svc.build is not None and not svc.image:
                    svc.image = _sanitize_docker_image_name(
                        f"hb__{harbor_task.name}__{svc_name}"
                    )

        return compose_config
    else:
        # Build programmatically from Dockerfile or docker_image
        service = ComposeService(
            # Use prebuilt image if specified, otherwise tag our build output
            # with a deterministic name derived from the task.
            image=(
                env_config.docker_image
                or _sanitize_docker_image_name(f"hb__{harbor_task.name}")
            ),
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
            deploy=gpu_deploy,
            environment=dict(env_config.env) if env_config.env else None,
        )

        return ComposeConfig(services={"default": service})


def harbor_task_to_sample(
    harbor_task: HarborTask,
    sandbox_env_name: str = "docker",
    override_cpus: int | None = None,
    override_memory_mb: int | None = None,
    override_gpus: int | None = None,
    sample_id: str | None = None,
) -> Sample:
    """Convert a Harbor task to an Inspect AI Sample.

    Args:
        harbor_task: The Harbor task to convert.
        sandbox_env_name: Sandbox environment name (default: ``docker``).
        override_cpus: Override the number of CPUs for the environment.
        override_memory_mb: Override the memory (in MB) for the environment.
        override_gpus: Override the number of GPUs for the environment.
        sample_id: Override the resulting ``Sample.id``. Defaults to
            ``harbor_task.name`` when ``None``. Used by the loader to
            disambiguate samples whose Harbor names collide.

    Returns:
        Sample: Inspect AI sample with sandbox configuration.
    """
    compose_config = harbor_to_compose_config(
        harbor_task,
        override_cpus=override_cpus,
        override_memory_mb=override_memory_mb,
        override_gpus=override_gpus,
    )

    metadata: dict[str, Any] = {
        "task_name": harbor_task.name,
        "task_dir": str(harbor_task.task_dir),
        "test_path": str(harbor_task.paths.test_path),
        "tests_dir": str(harbor_task.paths.tests_dir),
        "solution_dir": str(harbor_task.paths.solution_dir),
        "solve_path": str(harbor_task.paths.solve_path),
        "verifier_timeout_sec": harbor_task.config.verifier.timeout_sec,
        "verifier_env": harbor_task.config.verifier.env,
        "solution_env": harbor_task.config.solution.env,
        "verifier_user": _user_to_str(harbor_task.config.verifier.user),
        "agent_user": _user_to_str(harbor_task.config.agent.user),
        "harbor_config": harbor_task.config.model_dump(),
    }

    if harbor_task.config.task is not None:
        package_info = harbor_task.config.task
        metadata["package_name"] = package_info.name
        metadata["package_description"] = package_info.description
        metadata["package_keywords"] = list(package_info.keywords)
        metadata["package_authors"] = [a.model_dump() for a in package_info.authors]

    return Sample(
        input=harbor_task.instruction,
        id=sample_id if sample_id is not None else harbor_task.name,
        sandbox=SandboxEnvironmentSpec(sandbox_env_name, compose_config),
        metadata=metadata,
    )


def _user_to_str(user: str | int | None) -> str | None:
    """Coerce Harbor's ``user`` config (str | int | None) to Inspect's ``str | None``."""
    return str(user) if user is not None else None


def _find_default_service(config: ComposeConfig) -> tuple[str, ComposeService]:
    """Find the default service in a compose config.

    Priority: ``x-default: true`` > service named "default" or "main" > first.
    """
    for name, svc in config.services.items():
        if svc.x_default:
            return name, svc
    for candidate in ("default", "main"):
        if candidate in config.services:
            return candidate, config.services[candidate]
    name = next(iter(config.services))
    return name, config.services[name]


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
    """Expand ``${VAR}`` and ``${VAR:-default}`` references in a Harbor docker-compose.yaml.

    Harbor passes these variables as environment variables to the
    ``docker compose`` process, which performs the substitution natively.

    Limitation: ``HOST_*`` paths (the host side of volume mounts) are set to
    the same container-side ``EnvironmentPaths`` values as ``ENV_*``. In
    Harbor's DinD setup these differ, but we cannot resolve host-side paths
    here because they depend on the sandbox provider.
    """
    if "${" not in raw_yaml:
        return raw_yaml

    env_dir = str(harbor_task.paths.environment_dir)
    paths = EnvironmentPaths()

    var_map: dict[str, str] = {
        "CONTEXT_DIR": env_dir,
        # Mirror Harbor's own ``hb__<task.name>`` + ``_sanitize_docker_image_name``
        # so package tasks (org/name) produce the same image name Harbor would.
        "MAIN_IMAGE_NAME": _sanitize_docker_image_name(f"hb__{harbor_task.name}"),
        "CPUS": str(int(cpus)),
        "MEMORY": f"{memory_mb}M",
        "HOST_VERIFIER_LOGS_PATH": str(paths.verifier_dir),
        "HOST_AGENT_LOGS_PATH": str(paths.agent_dir),
        "HOST_ARTIFACTS_PATH": str(paths.artifacts_dir),
        "ENV_VERIFIER_LOGS_PATH": str(paths.verifier_dir),
        "ENV_AGENT_LOGS_PATH": str(paths.agent_dir),
        "ENV_ARTIFACTS_PATH": str(paths.artifacts_dir),
    }

    verifier_env = harbor_task.config.verifier.env
    if "TEST_DIR" in verifier_env:
        var_map["TEST_DIR"] = verifier_env["TEST_DIR"]
    else:
        var_map["TEST_DIR"] = str(paths.tests_dir)

    task_env = harbor_task.config.environment.env
    for key, value in task_env.items():
        var_map.setdefault(key, value)

    def _replace(match: re.Match[str]) -> str:
        body = match.group(1)
        if ":-" in body:
            var_name, default = body.split(":-", 1)
        else:
            var_name, default = body, None
        if var_name in var_map:
            return var_map[var_name]
        if default is not None:
            return default
        return match.group(0)

    return re.sub(r"\$\{([^}]+)}", _replace, raw_yaml)
