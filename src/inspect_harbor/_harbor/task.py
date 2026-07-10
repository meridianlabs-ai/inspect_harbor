"""Inspect AI Task interface to Harbor tasks"""

import hashlib
import warnings
from collections import Counter
from pathlib import Path

from harbor.models.job.config import DatasetConfig
from harbor.models.task.config import NetworkMode
from harbor.models.task.task import Task as HarborTask
from harbor.models.trial.config import TaskConfig
from harbor.tasks.client import TaskClient
from inspect_ai import Task, task
from inspect_ai._util._async import run_coroutine
from inspect_ai.agent import react
from inspect_ai.model import CompactionEdit
from inspect_ai.tool import bash, python, update_plan

from inspect_harbor._harbor.converters import harbor_task_to_sample
from inspect_harbor._harbor.scorer import harbor_scorer


@task
def harbor(
    path: str | Path | None = None,
    task_git_url: str | None = None,
    task_git_commit_id: str | None = None,
    registry_url: str | None = None,
    registry_path: str | Path | None = None,
    dataset_name_version: str | None = None,
    package_name: str | None = None,
    package_ref: str = "latest",
    dataset_task_names: list[str] | None = None,
    dataset_exclude_task_names: list[str] | None = None,
    n_tasks: int | None = None,
    disable_verification: bool = False,
    overwrite_cache: bool = False,
    sandbox_env_name: str = "docker",
    override_cpus: int | None = None,
    override_memory_mb: int | None = None,
    override_gpus: int | None = None,
) -> Task:
    """Harbor task loader for Inspect AI.

    Args:
        path: For local tasks/datasets: absolute path to task or dataset directory.
              For git tasks: task identifier within the repository (e.g. ``aime_i-9``).
        task_git_url: Git URL for downloading a task from a remote repository.
        task_git_commit_id: Git commit ID to pin the task version (requires task_git_url).
        registry_url: Registry URL for remote datasets.
        registry_path: Path to local registry for datasets.
        dataset_name_version: Dataset ``name@version`` (e.g. ``dataset@1.0``).
        package_name: Slug of a hub-published dataset in ``org/name`` form (e.g. ``harbor/hello-world``).
        package_ref: Harbor ref to pin to (digest, revision number, tag, or ``latest``). Defaults to ``latest``.
        dataset_task_names: Task names to include from dataset (supports glob patterns, multiple values).
        dataset_exclude_task_names: Task names to exclude from dataset (supports glob patterns, multiple values).
        n_tasks: Maximum number of tasks to include (applied after task_names/exclude_task_names filtering).
        disable_verification: Disable task verification. Verification checks whether task files exist.
        overwrite_cache: Force re-download and overwrite cached tasks (default: False).
        sandbox_env_name: Sandbox environment name (default: ``docker``).
        override_cpus: Override the number of CPUs for the environment.
        override_memory_mb: Override the memory (in MB) for the environment.
        override_gpus: Override the number of GPUs for the environment.

    Returns:
        Task: Configured Inspect AI task
    """
    harbor_task_objects = load_harbor_tasks(
        path=path,
        task_git_url=task_git_url,
        task_git_commit_id=task_git_commit_id,
        registry_url=registry_url,
        registry_path=registry_path,
        dataset_name_version=dataset_name_version,
        package_name=package_name,
        package_ref=package_ref,
        dataset_task_names=dataset_task_names,
        dataset_exclude_task_names=dataset_exclude_task_names,
        n_tasks=n_tasks,
        disable_verification=disable_verification,
        overwrite_cache=overwrite_cache,
    )

    sample_ids = _disambiguate_sample_ids(harbor_task_objects)
    samples = [
        harbor_task_to_sample(
            ht,
            sandbox_env_name=sandbox_env_name,
            override_cpus=override_cpus,
            override_memory_mb=override_memory_mb,
            override_gpus=override_gpus,
            sample_id=sid,
        )
        for ht, sid in zip(harbor_task_objects, sample_ids, strict=True)
    ]

    return Task(
        dataset=samples,
        solver=react(
            tools=[bash(timeout=300), python(timeout=300), update_plan()],
            compaction=CompactionEdit(),
        ),
        scorer=harbor_scorer(),
    )


def load_harbor_tasks(
    path: str | Path | None = None,
    task_git_url: str | None = None,
    task_git_commit_id: str | None = None,
    registry_url: str | None = None,
    registry_path: str | Path | None = None,
    dataset_name_version: str | None = None,
    package_name: str | None = None,
    package_ref: str = "latest",
    dataset_task_names: list[str] | None = None,
    dataset_exclude_task_names: list[str] | None = None,
    n_tasks: int | None = None,
    disable_verification: bool = False,
    overwrite_cache: bool = False,
) -> list[HarborTask]:
    """Load Harbor tasks from various sources.

    Args:
        path: For local tasks/datasets: absolute path to task or dataset directory.
              For git tasks: task identifier within the repository (e.g. ``aime_i-9``).
        task_git_url: Git URL for downloading a task from a remote repository.
        task_git_commit_id: Git commit ID to pin the task version (requires task_git_url).
        registry_url: Registry URL for remote datasets.
        registry_path: Path to local registry for datasets.
        dataset_name_version: Dataset ``name@version`` (e.g. ``dataset@1.0``).
        package_name: Slug of a hub-published dataset in ``org/name`` form (e.g. ``harbor/hello-world``).
        package_ref: Harbor ref to pin to (digest, revision number, tag, or ``latest``). Defaults to ``latest``.
        dataset_task_names: Task names to include from dataset (supports glob patterns, multiple values).
        dataset_exclude_task_names: Task names to exclude from dataset (supports glob patterns, multiple values).
        n_tasks: Maximum number of tasks to include (applied after task_names/exclude_task_names filtering).
        disable_verification: Disable task verification. Verification checks whether task files exist.
        overwrite_cache: Force re-download and overwrite cached tasks.

    Returns:
        list[HarborTask]: List of loaded Harbor task objects.
    """
    path, registry_path = _normalize_paths(path, registry_path)

    task_specified: bool = task_git_url is not None or task_git_commit_id is not None
    dataset_specified: bool = (
        dataset_name_version is not None
        or registry_url is not None
        or registry_path is not None
        or dataset_task_names is not None
        or dataset_exclude_task_names is not None
    )
    package_specified: bool = package_name is not None

    sources = sum([task_specified, dataset_specified, package_specified])
    if sources > 1:
        raise ValueError(
            "Cannot mix task, dataset, and package parameters. "
            f"Task params: git_url={task_git_url}, commit={task_git_commit_id}. "
            f"Dataset params: name_version={dataset_name_version}, registry_url={registry_url}. "
            f"Package params: package_name={package_name}, package_ref={package_ref}."
        )

    if path is not None:
        if task_git_url:
            task_paths = _load_git_task(
                path, task_git_url, task_git_commit_id, overwrite_cache
            )
        else:
            task_paths = _load_local_path(
                path,
                dataset_task_names,
                dataset_exclude_task_names,
                n_tasks,
                disable_verification,
            )
        return _build_harbor_tasks(task_paths, disable_verification)

    if task_specified:
        raise ValueError("Task configuration with task_git_url requires path parameter")

    if dataset_specified:
        if dataset_name_version is None:
            raise ValueError(
                "Cannot specify registry_url, registry_path, dataset_task_names, or "
                "dataset_exclude_task_names without also specifying dataset_name_version or path"
            )

        task_paths = _load_from_registry(
            dataset_name_version,
            registry_url,
            registry_path,
            dataset_task_names,
            dataset_exclude_task_names,
            n_tasks,
            overwrite_cache,
        )
        return _build_harbor_tasks(task_paths, disable_verification)

    if package_name is not None:
        task_paths = _load_from_package(
            package_name,
            package_ref,
            dataset_task_names,
            dataset_exclude_task_names,
            n_tasks,
            overwrite_cache,
        )
        return _build_harbor_tasks(task_paths, disable_verification)

    raise ValueError(
        "Must specify either path, task parameters, dataset parameters, or package parameters"
    )


def _disambiguate_sample_ids(harbor_tasks: list[HarborTask]) -> list[str]:
    """Return a unique ``Sample.id`` for each task."""
    name_counts = Counter(t.name for t in harbor_tasks)
    return [
        t.name
        if name_counts[t.name] == 1
        else f"{t.name}@{hashlib.sha256(str(t.task_dir).encode()).hexdigest()[:8]}"
        for t in harbor_tasks
    ]


def _build_harbor_tasks(
    task_paths: list[Path], disable_verification: bool
) -> list[HarborTask]:
    """Construct ``HarborTask`` objects, validating unsupported task.toml shapes."""
    harbor_tasks = [
        HarborTask(task_dir=p, disable_verification=disable_verification)
        for p in task_paths
    ]

    multi_step: list[str] = []
    windows: list[str] = []
    healthcheck: list[str] = []
    mcp_servers: list[str] = []
    skills_dir: list[str] = []
    allowlist: list[str] = []

    for t in harbor_tasks:
        if t.has_steps:
            multi_step.append(t.name)
        env = t.config.environment
        if str(getattr(env.os, "value", env.os)).lower() == "windows":
            windows.append(t.name)
        if env.healthcheck is not None:
            healthcheck.append(t.name)
        if env.mcp_servers:
            mcp_servers.append(t.name)
        if env.skills_dir is not None:
            skills_dir.append(t.name)
        if env.network_mode == NetworkMode.ALLOWLIST:
            allowlist.append(t.name)

    blocking: list[str] = []
    if multi_step:
        blocking.append(f"Multi-step tasks: {multi_step}")
    if windows:
        blocking.append(
            f"Windows containers (`[environment].os = 'windows'`): {windows}"
        )
    if blocking:
        raise NotImplementedError(
            "task.toml features not yet supported by inspect_harbor:\n  - "
            + "\n  - ".join(blocking)
        )

    degraded: list[str] = []
    if healthcheck:
        degraded.append(f"`[environment].healthcheck`: {healthcheck}")
    if mcp_servers:
        degraded.append(f"`[environment].mcp_servers`: {mcp_servers}")
    if skills_dir:
        degraded.append(f"`[environment].skills_dir`: {skills_dir}")
    if allowlist:
        degraded.append(
            "`[environment].network_mode = 'allowlist'` (egress allowlist cannot "
            f"be enforced in a plain compose project; treated as 'public'): {allowlist}"
        )
    if degraded:
        warnings.warn(
            "task.toml fields declared but not wired up by inspect_harbor "
            "(task will run with degraded fidelity):\n  - " + "\n  - ".join(degraded),
            UserWarning,
            stacklevel=2,
        )

    return harbor_tasks


def _normalize_paths(*paths: str | Path | None) -> tuple[Path | None, ...]:
    """Normalize string paths to Path objects."""
    return tuple(Path(p) if p is not None else None for p in paths)


def _load_git_task(
    path: Path,
    task_git_url: str,
    task_git_commit_id: str | None,
    overwrite_cache: bool,
) -> list[Path]:
    """Load a task from a git repository."""
    task_config = TaskConfig(
        path=path, git_url=task_git_url, git_commit_id=task_git_commit_id
    )
    task_client = TaskClient()
    result = run_coroutine(
        task_client.download_tasks(
            task_ids=[task_config.get_task_id()], overwrite=overwrite_cache
        )
    )
    return result.paths


def _load_local_path(
    path: Path,
    dataset_task_names: list[str] | None,
    dataset_exclude_task_names: list[str] | None,
    n_tasks: int | None,
    disable_verification: bool,
) -> list[Path]:
    """Load from a local path - either a single task or a dataset directory."""
    is_task: bool = HarborTask.is_valid_dir(
        path, disable_verification=disable_verification
    )

    if is_task:
        return [path]

    dataset_config = DatasetConfig(
        path=path,
        task_names=dataset_task_names,
        exclude_task_names=dataset_exclude_task_names,
        n_tasks=n_tasks,
    )
    local_configs = run_coroutine(
        dataset_config.get_task_configs(disable_verification=disable_verification)
    )
    return [config.path for config in local_configs if config.path is not None]


def _load_from_registry(
    dataset_name_version: str,
    registry_url: str | None,
    registry_path: Path | None,
    dataset_task_names: list[str] | None,
    dataset_exclude_task_names: list[str] | None,
    n_tasks: int | None,
    overwrite_cache: bool,
) -> list[Path]:
    """Load tasks from a registry dataset."""
    if "@" in dataset_name_version:
        name, version = dataset_name_version.split("@", 1)
    else:
        name, version = dataset_name_version, None

    dataset_config = DatasetConfig(
        name=name,
        version=version,
        registry_url=registry_url,
        registry_path=registry_path,
        task_names=dataset_task_names,
        exclude_task_names=dataset_exclude_task_names,
        n_tasks=n_tasks,
        overwrite=overwrite_cache,
    )
    return _download_dataset(dataset_config, overwrite_cache)


def _load_from_package(
    package_name: str,
    package_ref: str,
    dataset_task_names: list[str] | None,
    dataset_exclude_task_names: list[str] | None,
    n_tasks: int | None,
    overwrite_cache: bool,
) -> list[Path]:
    """Load tasks from a package-based dataset."""
    dataset_config = DatasetConfig(
        name=package_name,
        ref=package_ref,
        task_names=dataset_task_names,
        exclude_task_names=dataset_exclude_task_names,
        n_tasks=n_tasks,
        overwrite=overwrite_cache,
    )
    return _download_dataset(dataset_config, overwrite_cache)


def _download_dataset(
    dataset_config: DatasetConfig, overwrite_cache: bool
) -> list[Path]:
    """Resolve a dataset to TaskConfigs, then download to local paths."""

    async def _resolve_and_download() -> list[Path]:
        task_configs = await dataset_config.get_task_configs()
        result = await TaskClient().download_tasks(
            task_ids=[tc.get_task_id() for tc in task_configs],
            overwrite=overwrite_cache,
        )
        return result.paths

    return run_coroutine(_resolve_and_download())
