"""Inspect AI Task interface to Harbor tasks"""

from pathlib import Path

from harbor.dataset.client import DatasetClient
from harbor.models.job.config import LocalDatasetConfig, RegistryDatasetConfig
from harbor.models.registry import LocalRegistryInfo, RemoteRegistryInfo
from harbor.models.task.paths import TaskPaths
from harbor.models.task.task import Task as HarborTask
from harbor.models.trial.config import TaskConfig
from harbor.tasks.client import TaskClient
from inspect_ai import Task, task
from inspect_ai.agent import react
from inspect_ai.model import CompactionEdit
from inspect_ai.tool import bash, python, update_plan

from inspect_harbor.harbor._converters import harbor_task_to_sample
from inspect_harbor.harbor._scorer import harbor_scorer


@task
def harbor(
    path: str | Path | None = None,
    task_git_url: str | None = None,
    task_git_commit_id: str | None = None,
    registry_url: str | None = None,
    registry_path: str | Path | None = None,
    dataset_name_version: str | None = None,
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
              For git tasks: task identifier within the repository (e.g., "aime_i-9").
        task_git_url: Git URL for downloading a task from a remote repository.
        task_git_commit_id: Git commit ID to pin the task version (requires task_git_url).
        registry_url: Registry URL for remote datasets.
        registry_path: Path to local registry for datasets.
        dataset_name_version: Dataset name@version (e.g., 'dataset@1.0').
        dataset_task_names: Task names to include from dataset (supports glob patterns, multiple values).
        dataset_exclude_task_names: Task names to exclude from dataset (supports glob patterns, multiple values).
        n_tasks: Maximum number of tasks to include (applied after task_names/exclude_task_names filtering).
        disable_verification: Disable task verification. Verfication checks whether task files exist.
        overwrite_cache: Force re-download and overwrite cached tasks (default: False).
        sandbox_env_name: Sandbox environment name (default: "docker").
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
        dataset_task_names=dataset_task_names,
        dataset_exclude_task_names=dataset_exclude_task_names,
        n_tasks=n_tasks,
        disable_verification=disable_verification,
        overwrite_cache=overwrite_cache,
    )

    samples = [
        harbor_task_to_sample(
            ht,
            sandbox_env_name=sandbox_env_name,
            override_cpus=override_cpus,
            override_memory_mb=override_memory_mb,
            override_gpus=override_gpus,
        )
        for ht in harbor_task_objects
    ]
    max_timeout = _get_max_timeout_sec(harbor_task_objects)

    return Task(
        dataset=samples,
        solver=react(
            tools=[bash(timeout=300), python(timeout=300), update_plan()],
            compaction=CompactionEdit(),
        ),
        scorer=harbor_scorer(),
        time_limit=max_timeout,
    )


def load_harbor_tasks(
    path: str | Path | None = None,
    task_git_url: str | None = None,
    task_git_commit_id: str | None = None,
    registry_url: str | None = None,
    registry_path: str | Path | None = None,
    dataset_name_version: str | None = None,
    dataset_task_names: list[str] | None = None,
    dataset_exclude_task_names: list[str] | None = None,
    n_tasks: int | None = None,
    disable_verification: bool = False,
    overwrite_cache: bool = False,
) -> list[HarborTask]:
    """Load Harbor tasks from various sources.

    Args:
        path: For local tasks/datasets: absolute path to task or dataset directory.
              For git tasks: task identifier within the repository (e.g., "aime_i-9").
        task_git_url: Git URL for downloading a task from a remote repository.
        task_git_commit_id: Git commit ID to pin the task version (requires task_git_url).
        registry_url: Registry URL for remote datasets.
        registry_path: Path to local registry for datasets.
        dataset_name_version: Dataset name@version (e.g., 'dataset@1.0').
        dataset_task_names: Task names to include from dataset (supports glob patterns, multiple values).
        dataset_exclude_task_names: Task names to exclude from dataset (supports glob patterns, multiple values).
        n_tasks: Maximum number of tasks to include (applied after task_names/exclude_task_names filtering).
        disable_verification: Disable task verification. Verfication checks whether task files exist.
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

    if task_specified and dataset_specified:
        raise ValueError(
            f"Cannot specify both task and dataset parameters. "
            f"Task params: git_url={task_git_url}, commit={task_git_commit_id}. "
            f"Dataset params: name_version={dataset_name_version}, registry_url={registry_url}"
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
        return [HarborTask(task_dir=task_path) for task_path in task_paths]

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
        return [HarborTask(task_dir=task_path) for task_path in task_paths]

    raise ValueError("Must specify either path, task parameters, or dataset parameters")


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
    return task_client.download_tasks(
        task_ids=[task_config.get_task_id()], overwrite=overwrite_cache
    )


def _load_local_path(
    path: Path,
    dataset_task_names: list[str] | None,
    dataset_exclude_task_names: list[str] | None,
    n_tasks: int | None,
    disable_verification: bool,
) -> list[Path]:
    """Load from a local path - either a single task or a dataset directory."""
    harbor_task_paths = TaskPaths(path)
    is_task: bool = harbor_task_paths.is_valid(
        disable_verification=disable_verification
    )

    if is_task:
        return [path]

    dataset_config = LocalDatasetConfig(
        path=path,
        task_names=dataset_task_names,
        exclude_task_names=dataset_exclude_task_names,
        n_tasks=n_tasks,
    )
    local_configs = dataset_config.get_task_configs(disable_verification)
    return [config.path for config in local_configs]


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

    if registry_url is not None:
        registry_info = RemoteRegistryInfo(url=registry_url)
    elif registry_path is not None:
        registry_info = LocalRegistryInfo(path=registry_path)
    else:
        registry_info = RemoteRegistryInfo()

    dataset_config = RegistryDatasetConfig(
        registry=registry_info,
        name=name,
        version=version,
        task_names=dataset_task_names,
        exclude_task_names=dataset_exclude_task_names,
        n_tasks=n_tasks,
        overwrite=overwrite_cache,
    )
    dataset_client = DatasetClient()
    downloaded_tasks = dataset_client.download_dataset_from_config(dataset_config)
    return [dt.local_path for dt in downloaded_tasks]


def _get_max_timeout_sec(harbor_tasks: list[HarborTask]) -> int | None:
    """Extract the maximum timeout_sec from a list of Harbor tasks."""
    timeout_values = [ht.config.agent.timeout_sec for ht in harbor_tasks]
    return int(max(timeout_values)) if timeout_values else None
