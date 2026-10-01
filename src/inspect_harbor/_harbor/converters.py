"""Converters for Harbor tasks to Inspect AI structures."""

import logging
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

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
            _, default_service = _find_default_service(compose_config)
            _complete_default_service(
                default_service, harbor_task, env_config, dockerfile_path
            )
            for svc in compose_config.services.values():
                _absolutize_build_context(svc, env_dir)
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

            # Network isolation applies to all services.
            if _is_no_network(env_config):
                for service in compose_config.services.values():
                    if service.networks:
                        continue
                    service.network_mode = "none"

            # Pin a stable `image:` tag so builds are reused across runs.
            for svc_name, svc in compose_config.services.items():
                if svc.build is not None and not svc.image:
                    svc.image = _image_name(harbor_task, svc_name)

            _share_harbor_log_mounts(compose_config)

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
        "mcp_servers": mcp_server_specs(harbor_task, compose_config),
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
        "MAIN_IMAGE_NAME": _image_name(harbor_task),
        "HOST_VERIFIER_LOGS_PATH": str(paths.verifier_dir),
        "HOST_AGENT_LOGS_PATH": str(paths.agent_dir),
        "HOST_ARTIFACTS_PATH": str(paths.artifacts_dir),
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


def _complete_default_service(
    service: ComposeService,
    harbor_task: HarborTask,
    env_config: EnvironmentConfig,
    dockerfile_path: Path,
) -> None:
    """Fill in what Harbor adds to the main service of a task's docker-compose.yaml.

    Harbor merges the compose file over its own definition of the main service
    (image built from ``environment/Dockerfile`` or ``[environment].docker_image``,
    ``[environment.env]``, a long-running command), so compose files often only
    declare ``depends_on`` or extra mounts for it. Inspect also needs the agent's
    service marked as its default sandbox (``x-default``).
    """
    if service.image is None and service.build is None:
        if env_config.docker_image:
            service.image = env_config.docker_image
        else:
            service.image = _image_name(harbor_task)
            if dockerfile_path.exists():
                service.build = ComposeBuild(context=str(dockerfile_path.parent))
    if service.command is None:
        service.command = "tail -f /dev/null"
    if service.init is None:
        service.init = True
    if service.x_default is None:
        service.x_default = True
    if env_config.env and not service.environment:
        service.environment = {
            k: v for k, v in resolve_env_vars(env_config.env).items()
        }


def _absolutize_build_context(service: ComposeService, env_dir: Path) -> None:
    """Resolve a relative ``build.context`` against the task's environment directory.

    Inspect writes the compose config to its own location, so a context such as
    ``./runtime-server`` must not stay relative to the original file.
    """
    build = service.build
    if (
        isinstance(build, ComposeBuild)
        and build.context
        and not os.path.isabs(build.context)
    ):
        build.context = os.path.normpath(os.path.join(str(env_dir), build.context))


_HARBOR_LOG_MOUNTS = ("agent_dir", "verifier_dir", "artifacts_dir")


def _share_harbor_log_mounts(compose_config: ComposeConfig) -> None:
    """Turn Harbor log-directory bind mounts into named volumes shared with the default service.

    A Harbor compose file mounts ``${HOST_AGENT_LOGS_PATH}:${ENV_AGENT_LOGS_PATH}``
    (and the verifier / artifacts equivalents) into sidecar services so they share
    ``/logs/...`` with the main container. ``_expand_compose_vars`` resolves both
    sides to the container path, which would bind-mount a host directory that does
    not exist. A named volume mounted at the same path in the sidecar and in the
    default service gives the same sharing without touching the host.
    """
    if not compose_config.services:
        return
    default_name, default_service = _find_default_service(compose_config)
    paths = EnvironmentPaths()
    log_paths = {str(getattr(paths, attr)) for attr in _HARBOR_LOG_MOUNTS}
    shared: dict[str, str] = {}
    for svc_name, svc in compose_config.services.items():
        if svc_name == default_name or not svc.volumes:
            continue
        rewritten: list[Any] = []
        for mount in svc.volumes:
            if isinstance(mount, str) and ":" in mount:
                src, dst = mount.split(":", 1)
                dst_path = dst.split(":", 1)[0]
                if src in log_paths and dst_path in log_paths:
                    vol = "harbor-logs-" + dst_path.strip("/").replace("/", "-")
                    shared[vol] = dst_path
                    rewritten.append(f"{vol}:{dst_path}")
                    continue
            rewritten.append(mount)
        svc.volumes = rewritten
    if not shared:
        return
    default_service.volumes = list(default_service.volumes or []) + [
        f"{vol}:{dst}" for vol, dst in shared.items()
    ]
    compose_config.volumes = {
        **(compose_config.volumes or {}),
        **{vol: {} for vol in shared},
    }


def mcp_server_specs(
    harbor_task: HarborTask, compose_config: ComposeConfig
) -> list[dict[str, Any]]:
    """Describe how Inspect reaches each ``[[environment.mcp_servers]]`` entry.

    HTTP servers live on the compose network (``http://<service>:<port>/mcp``),
    which the Inspect process cannot reach, so they are proxied over stdio by
    ``mcp_bridge.py`` started with ``mcp_server_sandbox()`` inside the service that
    hosts them (URL host = service name), falling back to the default service.
    Stdio servers are started directly in the default service.
    """
    servers = getattr(harbor_task.config.environment, "mcp_servers", None)
    if not isinstance(servers, (list, tuple)):
        return []
    services = compose_config.services or {}
    default_name = _find_default_service(compose_config)[0] if services else "default"
    return [_mcp_server_spec(dict(cfg), services, default_name) for cfg in servers]


def _mcp_server_spec(
    cfg: dict[str, Any], services: dict[str, Any], default_name: str
) -> dict[str, Any]:
    name = str(cfg.get("name") or "mcp")
    transport = str(cfg.get("transport") or "sse")
    if transport == "http":
        transport = "streamable-http"
    if transport == "stdio":
        return {
            "name": name,
            "transport": "stdio",
            "sandbox": default_name,
            "command": cfg.get("command"),
            "args": list(cfg.get("args") or []),
        }
    url = str(cfg.get("url") or "")
    parts = urlsplit(url)
    host = parts.hostname or ""
    sandbox = default_name
    if host in services:
        # Run the bridge inside the service that serves the MCP endpoint.
        sandbox = host
        netloc = "localhost" + (f":{parts.port}" if parts.port else "")
        url = urlunsplit(
            (parts.scheme, netloc, parts.path, parts.query, parts.fragment)
        )
    return {"name": name, "transport": transport, "sandbox": sandbox, "url": url}
