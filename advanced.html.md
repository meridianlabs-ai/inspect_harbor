# Advanced – Inspect Harbor

## Generic Harbor Interface

For advanced use cases, you can use the generic `harbor()` interface directly. This provides access to all task loading options: `org/name` datasets from the Harbor hub, `name@version` datasets from a Harbor registry file, git repositories, and local paths.

### Harbor Interface Parameters

Harbor task loader for Inspect AI.

[Source](https://github.com/meridianlabs-ai/inspect_harbor/blob/fba546348277fd1c4f5daba2c6569c755731e59d/src/inspect_harbor/_harbor/task.py#L23)

``` python
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
) -> Task
```

`path` str \| Path \| None  
For local tasks/datasets: absolute path to task or dataset directory. For git tasks: task identifier within the repository (e.g. `aime_i-9`).

`task_git_url` str \| None  
Git URL for downloading a task from a remote repository.

`task_git_commit_id` str \| None  
Git commit ID to pin the task version (requires task_git_url).

`registry_url` str \| None  
Registry URL for remote datasets.

`registry_path` str \| Path \| None  
Path to local registry for datasets.

`dataset_name_version` str \| None  
Dataset `name@version` (e.g. `dataset@1.0`).

`package_name` str \| None  
Slug of a hub-published dataset in `org/name` form (e.g. `harbor/hello-world`).

`package_ref` str  
Harbor ref to pin to (digest, revision number, tag, or `latest`). Defaults to `latest`.

`dataset_task_names` list\[str\] \| None  
Task names to include from dataset (supports glob patterns, multiple values).

`dataset_exclude_task_names` list\[str\] \| None  
Task names to exclude from dataset (supports glob patterns, multiple values).

`n_tasks` int \| None  
Maximum number of tasks to include (applied after task_names/exclude_task_names filtering).

`disable_verification` bool  
Disable task verification. Verification checks whether task files exist.

`overwrite_cache` bool  
Force re-download and overwrite cached tasks (default: False).

`sandbox_env_name` str  
Sandbox environment name (default: `docker`).

`override_cpus` int \| None  
Override the number of CPUs for the environment.

`override_memory_mb` int \| None  
Override the memory (in MB) for the environment.

`override_gpus` int \| None  
Override the number of GPUs for the environment.

> **Note:** These are task-specific parameters passed with `-T`. For additional `inspect eval` command-line flags (like `--model`, `--message-limit`, `--epochs`, `--fail-on-error`, `--log-dir`, `--log-level`, `--max-tasks`, etc.), see the [Inspect eval CLI reference](https://inspect.aisi.org.uk/reference/inspect_eval.html) or [Python API reference](https://inspect.aisi.org.uk/reference/inspect_ai.html#eval).

### Parameter Combinations

There are five primary patterns for loading Harbor tasks:

| Pattern | Required Parameters | Optional Parameters |
|----|----|----|
| **`org/name` dataset** | `package_name` | `package_ref` (defaults to `"latest"`), `dataset_task_names`, `dataset_exclude_task_names`, `n_tasks`, `overwrite_cache` |
| **`name@version` dataset** | `dataset_name_version` | `registry_url` or `registry_path`, `dataset_task_names`, `dataset_exclude_task_names`, `n_tasks`, `overwrite_cache` |
| **Git task** | `path`, `task_git_url` | `task_git_commit_id`, `overwrite_cache` |
| **Local task** | `path` | `disable_verification` |
| **Local dataset** | `path` | `dataset_task_names`, `dataset_exclude_task_names`, `n_tasks`, `disable_verification` |

The **`org/name`** pattern is what every dataset on the [Registry](./registry.html.md) uses under the hood. Use `harbor()` directly when you need a slug that isn’t exposed on the [Registry](./registry.html.md) (e.g. a private fork).

> **Two ways to reference a dataset.** Harbor has two slug formats and two backends behind them:
>
> - **`org/name`** — published self-service to [hub.harborframework.com](https://hub.harborframework.com/datasets), pinned via `package_ref` (digest, revision number, tag, or `latest`). This is the [self-service Harbor registry](https://www.harborframework.com/news/harbor-registry) introduced in March 2026.
> - **`name@version`** — entry in a Harbor `registry.json`, resolved against the curated [`laude-institute/harbor`](https://github.com/laude-institute/harbor) registry by default; override via `registry_url=`/`registry_path=` for private/org registries.
>
> Most public datasets are now on the hub; the `name@version` form remains useful for curated benchmarks not yet on the hub and for private registries.

## Loading an `org/name` Dataset

Pass a Harbor slug directly to `harbor()`. The default `package_ref="latest"` follows the upstream tag; pin to a `sha256:...` digest, revision number, or named tag for reproducibility.

``` bash
inspect eval inspect_harbor/harbor \
  -T package_name="aider/aider-polyglot" \
  --model openai/gpt-5-mini
```

**Pinned to a specific digest:**

``` bash
inspect eval inspect_harbor/harbor \
  -T package_name="aider/aider-polyglot" \
  -T package_ref="sha256:01e28d85e46beae5b7e29a29f57cb49d882b5486583d52cec4ee5bf3540a1c84" \
  --model openai/gpt-5-mini
```

## Loading a `name@version` Dataset

Datasets keyed by `name@version` are resolved against the default Harbor registry unless `registry_url` or `registry_path` is supplied:

``` bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="aime@1.0" \
  --model openai/gpt-5-mini
```

**Custom remote registry** (for private or organization-specific datasets):

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
  -T path="datasets/aime/aime_60" \
  -T task_git_url="https://github.com/laude-institute/harbor-datasets.git" \
  -T task_git_commit_id="515f914f9e5ecc3bc3f421307f455f6694ce5a01" \
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
inspect eval inspect_harbor/aime \
  -T overwrite_cache=true \
  --model openai/gpt-5
```

To manually clear the entire cache:

``` bash
rm -rf ~/.harbor/cache/
```
