# Advanced – Inspect Harbor

## Generic Harbor Interface

For advanced use cases, you can use the generic `harbor()` interface directly. This provides access to all task loading options including custom registries, git repositories, and local paths.

### Harbor Interface Parameters

Harbor task loader for Inspect AI.

[Source](https://github.com/meridianlabs-ai/inspect_harbor/blob/ccbda21ae9d201f15ad02f2d306b9020ca971683/src/inspect_harbor/_harbor/task.py#L21)

``` python
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
) -> Task
```

`path` str \| Path \| None  
For local tasks/datasets: absolute path to task or dataset directory. For git tasks: task identifier within the repository (e.g., “aime_i-9”).

`task_git_url` str \| None  
Git URL for downloading a task from a remote repository.

`task_git_commit_id` str \| None  
Git commit ID to pin the task version (requires task_git_url).

`registry_url` str \| None  
Registry URL for remote datasets.

`registry_path` str \| Path \| None  
Path to local registry for datasets.

`dataset_name_version` str \| None  
Dataset <name@version> (e.g., ‘<dataset@1.0>’).

`dataset_task_names` list\[str\] \| None  
Task names to include from dataset (supports glob patterns, multiple values).

`dataset_exclude_task_names` list\[str\] \| None  
Task names to exclude from dataset (supports glob patterns, multiple values).

`n_tasks` int \| None  
Maximum number of tasks to include (applied after task_names/exclude_task_names filtering).

`disable_verification` bool  
Disable task verification. Verfication checks whether task files exist.

`overwrite_cache` bool  
Force re-download and overwrite cached tasks (default: False).

`sandbox_env_name` str  
Sandbox environment name (default: “docker”).

`override_cpus` int \| None  
Override the number of CPUs for the environment.

`override_memory_mb` int \| None  
Override the memory (in MB) for the environment.

`override_gpus` int \| None  
Override the number of GPUs for the environment.

> **Note:** These are task-specific parameters passed with `-T`. For additional `inspect eval` command-line flags (like `--model`, `--message-limit`, `--epochs`, `--fail-on-error`, `--log-dir`, `--log-level`, `--max-tasks`, etc.), see the [Inspect eval CLI reference](https://inspect.aisi.org.uk/reference/inspect_eval.html) or [Python API reference](https://inspect.aisi.org.uk/reference/inspect_ai.html#eval).

### Parameter Combinations

There are four primary patterns for loading Harbor tasks:

| Pattern | Required Parameters | Optional Parameters |
|----|----|----|
| **Registry Dataset** | `dataset_name_version` | `registry_url` or `registry_path`, `dataset_task_names`, `dataset_exclude_task_names`, `n_tasks`, `overwrite_cache` |
| **Git Task** | `path`, `task_git_url` | `task_git_commit_id`, `overwrite_cache` |
| **Local Task** | `path` | `disable_verification` |
| **Local Dataset** | `path` | `dataset_task_names`, `dataset_exclude_task_names`, `n_tasks`, `disable_verification` |

## Custom Registries

You can use custom registries for private or organization-specific datasets.

**Remote registry:**

``` bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="my_dataset@1.0" \
  -T registry_url="https://github.com/myorg/registry.json" \
  --model openai/gpt-5-mini
```

**Local registry:**

``` bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="my_dataset@1.0" \
  -T registry_path="/path/to/local/registry.json" \
  --model openai/gpt-5-mini
```

## Loading from Git Repositories

You can load tasks directly from git repositories:

``` bash
inspect eval inspect_harbor/harbor \
  -T path="datasets/aime/aime_6" \
  -T task_git_url="https://github.com/laude-institute/harbor-datasets.git" \
  -T task_git_commit_id="414014c23ce4d32128073d12b057252c918cccf4" \
  --model openai/gpt-5-mini
```

## Loading from Local Paths

You can run tasks from your local filesystem:

``` bash
inspect eval inspect_harbor/harbor \
  -T path="/path/to/task_or_dataset/directory" \
  --model openai/gpt-5
```

## Cache Management

Downloaded tasks are cached locally in `~/.harbor/cache/`. To force a fresh download:

``` bash
inspect eval inspect_harbor/aime_1_0 \
  -T overwrite_cache=true \
  --model openai/gpt-5
```

To manually clear the entire cache:

``` bash
rm -rf ~/.harbor/cache/
```
