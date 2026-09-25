"""Converters for Harbor tasks to Inspect AI structures."""

import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml
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
    ComposeHealthcheck,
    ComposeResourceConfig,
    ComposeResourceReservations,
)

from inspect_harbor._harbor.models import (
    MAIN_SERVICE_NAME,
    EnvironmentConfig,
    HealthcheckConfig,
    NetworkMode,
)
from inspect_harbor._harbor.paths import (
    EnvironmentPaths,
    environment_content_hash,
    sanitize_docker_image_name,
)
from inspect_harbor._harbor.sandbox_utils import resolve_env_vars
from inspect_harbor._harbor.task_dir import HarborTask

logger = logging.getLogger(__name__)

# Named compose volumes that stand in for Harbor's per-trial host log
# directories. A task's docker-compose.yaml mounts them as
# ``${HOST_VERIFIER_LOGS_PATH}:${ENV_VERIFIER_LOGS_PATH}`` and so on; Harbor
# points ``HOST_*`` at directories in the trial's output folder on the Docker
# host. We have no host side (the sandbox may not even be local Docker), so
# ``HOST_*`` expands to a project-scoped named volume instead: still shared
# between the services of one sample, never shared between samples, and torn
# down with the project.
_LOG_VOLUMES: dict[str, str] = {
    "VERIFIER_LOGS": "harbor-verifier-logs",
    "AGENT_LOGS": "harbor-agent-logs",
    "ARTIFACTS": "harbor-artifacts",
}


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

    if override_cpus is not None:
        cpus: float | None = float(override_cpus)
    elif env_config.cpus is not None:
        cpus = float(env_config.cpus)
    else:
        cpus = None

    MIN_MEMORY_MB = 6144  # 6 GB
    if override_memory_mb is not None:
        memory_mb: int | None = override_memory_mb
    elif env_config.memory_mb is not None:
        memory_mb = max(env_config.memory_mb, MIN_MEMORY_MB)
    else:
        memory_mb = None

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
            if MAIN_SERVICE_NAME in compose_config.services:
                _complete_main_service(
                    compose_config.services[MAIN_SERVICE_NAME], harbor_task
                )
            default_name, default_service = _find_default_service(compose_config)
            if default_name != "default":
                # Inspect's Docker provider only recognises a service named
                # ``default`` or one flagged ``x-default``; Harbor's is ``main``.
                default_service.x_default = True
            if cpus is not None:
                default_service.cpus = cpus
            if memory_mb is not None:
                default_service.mem_limit = f"{memory_mb}m"
            if gpu_deploy:
                default_service.deploy = gpu_deploy
            if env_config.healthcheck is not None:
                if default_service.healthcheck is None:
                    default_service.healthcheck = _harbor_healthcheck_to_compose(
                        env_config.healthcheck
                    )
                else:
                    # A compose service can only carry one healthcheck, and the
                    # one the task ships is the more specific declaration.
                    logger.warning(
                        "%r declares both `[environment].healthcheck` in task.toml "
                        "and a healthcheck on the default service of its "
                        "docker-compose.yaml; keeping the compose healthcheck and "
                        "ignoring the task.toml one.",
                        harbor_task.name,
                    )

            # Network isolation applies to every service that does not declare
            # its own networking; Harbor likewise leaves task-authored
            # ``network_mode``/``networks`` alone.
            if _is_no_network(env_config):
                for service in compose_config.services.values():
                    if service.networks or service.network_mode is not None:
                        continue
                    service.network_mode = "none"

            # Pin a stable `image:` tag so builds are reused across runs. The
            # main service gets Harbor's own ``hb__<hash>`` tag.
            for svc_name, svc in compose_config.services.items():
                if svc.build is not None and not svc.image:
                    svc.image = _image_name(
                        harbor_task, None if svc_name == MAIN_SERVICE_NAME else svc_name
                    )

            _declare_log_volumes(compose_config)

        return compose_config
    else:
        # Build programmatically from Dockerfile or docker_image.
        # Resolve ``${VAR}`` / ``${VAR:-default}`` references.
        resolved_env: dict[str, str | None] | None = (
            {k: v for k, v in resolve_env_vars(env_config.env).items()}
            if env_config.env
            else None
        )
        service = ComposeService(
            # Use prebuilt image if specified, otherwise tag our build output
            # with a deterministic name derived from the task.
            image=env_config.docker_image or _image_name(harbor_task),
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
            network_mode="none" if _is_no_network(env_config) else "bridge",
            deploy=gpu_deploy,
            environment=resolved_env,
            healthcheck=(
                _harbor_healthcheck_to_compose(env_config.healthcheck)
                if env_config.healthcheck is not None
                else None
            ),
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


def _image_name(harbor_task: HarborTask, service: str | None = None) -> str:
    """The ``hb__<environment hash>`` tag Harbor gives a task's built image.

    Content-addressed like Harbor 0.23, so two revisions of a task with
    different environments never collide on one tag. Extra compose services
    that build their own image get a ``__<service>`` suffix.
    """
    docker_image = harbor_task.config.environment.docker_image
    digest = environment_content_hash(
        Path(harbor_task.paths.environment_dir),
        docker_image=docker_image if isinstance(docker_image, str) else None,
    )
    suffix = f"__{service}" if service else ""
    return sanitize_docker_image_name(f"hb__{digest}{suffix}")


def _user_to_str(user: str | int | None) -> str | None:
    """Coerce Harbor's ``user`` config (str | int | None) to Inspect's ``str | None``."""
    return str(user) if user is not None else None


def _complete_main_service(main: ComposeService, harbor_task: HarborTask) -> None:
    """Fill in what Harbor's base compose overlay gives the ``main`` service.

    Harbor layers ``docker-compose-build.yaml`` (or ``-prebuilt.yaml`` when
    ``[environment].docker_image`` is set) under every task's compose file, so
    a task may declare ``main`` with only ``depends_on`` or ``environment``
    and still get an image, a build context and a keep-alive command.
    Compose merges mappings, so a task ``build:`` that omits ``context`` picks
    up the environment directory too. The task's own values always win.

    The overlay's ``pull_policy: build`` is not reproduced: our image tag is
    content-addressed, so a stale image cannot hide behind a fixed tag, and
    Inspect builds compose services itself before ``up``.

    Harbor also writes ``[environment].env`` into ``main`` through an override
    that comes after the task's compose file, so on a shared key the task.toml
    value replaces the compose file's.
    """
    env_config = harbor_task.config.environment
    docker_image = env_config.docker_image
    if main.build is None and not main.image:
        if isinstance(docker_image, str):
            main.image = docker_image
        else:
            main.build = ComposeBuild(context=str(harbor_task.paths.environment_dir))
    elif isinstance(main.build, ComposeBuild) and not main.build.context:
        main.build.context = str(harbor_task.paths.environment_dir)
    if main.command is None:
        main.command = ["sh", "-c", "sleep infinity"]
    if env_config.env:
        environment = _environment_dict(main.environment)
        environment.update(resolve_env_vars(env_config.env))
        main.environment = environment


def _environment_dict(
    environment: list[str] | dict[str, str | None] | None,
) -> dict[str, str | None]:
    """A compose ``environment`` block as a mapping, whichever form it used."""
    if environment is None:
        return {}
    if isinstance(environment, dict):
        return dict(environment)
    result: dict[str, str | None] = {}
    for entry in environment:
        key, sep, value = entry.partition("=")
        result[key] = value if sep else None
    return result


def _declare_log_volumes(config: ComposeConfig) -> None:
    """Declare the named log volumes that ``HOST_*`` mounts now refer to."""
    referenced = {
        mount.split(":", 1)[0]
        for service in config.services.values()
        for mount in service.volumes or []
        if isinstance(mount, str)
    } & set(_LOG_VOLUMES.values())
    if referenced:
        config.volumes = {
            **(config.volumes or {}),
            **{
                name: {}
                for name in sorted(referenced)
                if name not in (config.volumes or {})
            },
        }


def _find_default_service(config: ComposeConfig) -> tuple[str, ComposeService]:
    """Find the service the agent runs in.

    Priority: ``x-default: true`` > service named "default" or "main" > first.
    Harbor always runs the agent in ``main``; the other rules keep compose
    files written for Inspect working.
    """
    for name, svc in config.services.items():
        if svc.x_default:
            return name, svc
    for candidate in ("default", "main"):
        if candidate in config.services:
            return candidate, config.services[candidate]
    name = next(iter(config.services))
    return name, config.services[name]


def _harbor_healthcheck_to_compose(
    healthcheck: HealthcheckConfig,
) -> ComposeHealthcheck:
    """Map a Harbor ``[environment].healthcheck`` onto a compose healthcheck.

    Harbor polls the command itself before agent setup, explicitly mirroring
    Docker's HEALTHCHECK semantics, so the fields map one-to-one. Inspect
    brings the environment up with ``docker compose up --wait``, which gates
    readiness on the healthcheck — so the agent no longer starts before the
    services it depends on are ready.

    Harbor's ``command`` is a shell command string, hence ``CMD-SHELL``.
    """
    return ComposeHealthcheck(
        test=["CMD-SHELL", healthcheck.command],
        interval=_compose_duration(healthcheck.interval_sec),
        timeout=_compose_duration(healthcheck.timeout_sec),
        start_period=_compose_duration(healthcheck.start_period_sec),
        # ``start_interval`` only applies within the start period (in Docker and
        # in Harbor's own loop), so omit it when there is no start period —
        # it would be inert and it needs Docker Engine 25+.
        start_interval=(
            _compose_duration(healthcheck.start_interval_sec)
            if healthcheck.start_period_sec > 0
            else None
        ),
        retries=healthcheck.retries,
    )


def _compose_duration(seconds: float) -> str:
    r"""Render a Harbor ``*_sec`` float as a compose duration string.

    Emits whole units only: Inspect's compose duration parser matches
    ``(\d+)([a-z]+)``, so a fractional string like ``"5.5s"`` would silently
    parse as ``5s`` (and ``"5.0s"`` as ``0s``, since ``5`` isn't followed by a
    unit), skewing the ``up --wait`` timeout.
    """
    milliseconds = round(seconds * 1000)
    if milliseconds % 1000 == 0:
        return f"{milliseconds // 1000}s"
    return f"{milliseconds}ms"


def _create_gpu_deploy_config(
    gpus: int | None, gpu_types: list[str] | None
) -> ComposeDeploy | None:
    """Create GPU deployment configuration for ComposeService.

    Args:
        gpus: Number of GPUs to reserve (None or 0 means no GPUs).
        gpu_types: List of acceptable GPU types (e.g., ['H100', 'A100']).
                   Stored in device options for informational purposes.

    Returns:
        ComposeDeploy configuration with GPU reservations, or None if no GPUs.
    """
    if gpus is None or gpus <= 0:
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
    cpus: float | None,
    memory_mb: int | None,
) -> str:
    """Expand ``${VAR}`` and ``${VAR:-default}`` references in a Harbor docker-compose.yaml.

    ``ENV_*_PATH`` are the container-side log directories. ``HOST_*_PATH``,
    the host side of the same mounts in Harbor, expand to the named volumes
    in ``_LOG_VOLUMES`` (see there for why).
    """
    if "${" not in raw_yaml:
        return raw_yaml

    env_dir = str(harbor_task.paths.environment_dir)
    paths = EnvironmentPaths()

    var_map: dict[str, str] = {
        "CONTEXT_DIR": env_dir,
        "MAIN_IMAGE_NAME": _image_name(harbor_task),
        "HOST_VERIFIER_LOGS_PATH": _LOG_VOLUMES["VERIFIER_LOGS"],
        "HOST_AGENT_LOGS_PATH": _LOG_VOLUMES["AGENT_LOGS"],
        "HOST_ARTIFACTS_PATH": _LOG_VOLUMES["ARTIFACTS"],
        "ENV_VERIFIER_LOGS_PATH": str(paths.verifier_dir),
        "ENV_AGENT_LOGS_PATH": str(paths.agent_dir),
        "ENV_ARTIFACTS_PATH": str(paths.artifacts_dir),
    }
    if cpus is not None:
        var_map["CPUS"] = str(int(cpus))
    if memory_mb is not None:
        var_map["MEMORY"] = f"{memory_mb}M"

    verifier_env = harbor_task.config.verifier.env
    if "TEST_DIR" in verifier_env:
        var_map["TEST_DIR"] = verifier_env["TEST_DIR"]
    else:
        var_map["TEST_DIR"] = str(paths.tests_dir)

    for key, value in resolve_env_vars(harbor_task.config.environment.env).items():
        var_map.setdefault(key, value)

    def _replace(match: re.Match[str]) -> str:
        body = match.group(1)
        if ":-" in body:
            var_name, default = body.split(":-", 1)
        else:
            var_name, default = body, None
        if var_name in var_map:
            return var_map[var_name]
        if var_name in os.environ:
            return os.environ[var_name]
        if default is not None:
            return default
        return match.group(0)

    return re.sub(r"\$\{([^}]+)}", _replace, raw_yaml)


def _is_no_network(env_config: EnvironmentConfig) -> bool:
    """Whether an environment should run with no network access.

    Only ``no-network`` isolates the environment. ``allowlist`` cannot be
    enforced in a plain compose project (that's Harbor's egress sidecar), so
    it is treated like ``public``; the loader warns about the degraded
    fidelity. The deprecated ``allow_internet = false`` needs no special
    handling here: Harbor's ``TaskConfig`` validator migrates it to
    ``network_mode = no-network`` (and clears the boolean), so a legacy task
    is isolated through the ``network_mode`` check below.
    """
    return env_config.network_mode == NetworkMode.NO_NETWORK
