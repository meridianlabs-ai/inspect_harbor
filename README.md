# Inspect Harbor

This package provides an interface to run [Harbor](https://harborframework.com/) tasks using [Inspect AI](https://inspect.aisi.org.uk/).

## Installation

Install from PyPI:

```bash
pip install inspect-harbor
```

Or with uv:

```bash
uv add inspect-harbor
```

For development installation, see the [Development](#development) section.

## Prerequisites

Before running Harbor tasks, ensure you have:

- **Python 3.12 or higher** - Required by inspect_harbor
- **Docker installed and running** - Required for execution when using Docker sandbox (default)
- **Model API keys** - Set appropriate environment variables (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)

## Quick Start

The fastest way to get started is to run a dataset from the [Harbor registry](https://harborframework.com/registry).

### Evaluate with a Model

**CLI:**
```bash
# Run hello-world dataset
inspect eval inspect_harbor/hello_world \
  --model openai/gpt-5-mini

# Run terminal-bench-sample dataset
inspect eval inspect_harbor/terminal_bench_sample \
  --model openai/gpt-5
```

**Python API:**
```python
from inspect_ai import eval
from inspect_harbor import hello_world, terminal_bench_sample

# Run hello-world
eval(hello_world(), model="openai/gpt-5-mini")

# Run terminal-bench-sample
eval(terminal_bench_sample(), model="openai/gpt-5")
```

**What this does:**
- Loads the dataset from the [Harbor registry](https://harborframework.com/registry)
- Downloads and caches all tasks in the dataset
- Solves the tasks with the [default ReAct agent](#default-agent-scaffold) scaffold
- Executes in a [Docker sandbox environment](https://inspect.aisi.org.uk/sandboxing.html#sec-docker-configuration)
- Stores results in `./logs`

## Available Datasets

Inspect Harbor provides task functions for each dataset in the [Harbor registry](https://harborframework.com/registry). You can import and use them directly:

```python
from inspect_harbor import (
    terminal_bench,
    swebenchpro,
    swe_lancer_diamond,
    swebench_verified,
    # ... and many more
)
```

**For a complete list of available datasets and versions (including swebenchpro, terminal-bench-pro, replicationbench, compilebench, and 40+ more), see [`REGISTRY.md`](REGISTRY.md).**

### Dataset Versioning

Each dataset has both **unversioned** and **versioned** task functions:

- **Unversioned functions** (e.g., `terminal_bench()`) automatically use the latest version available in the registry
- **Versioned functions** (e.g., `terminal_bench_2_0()`) pin to a specific version for reproducibility

**Example:**
```python
from inspect_harbor import terminal_bench, terminal_bench_2_0

# Uses latest version (currently 2.0)
eval(terminal_bench(), model="openai/gpt-5-mini")

# Pins to version 2.0 explicitly
eval(terminal_bench_2_0(), model="openai/gpt-5-mini")
```

## Agents and Solvers

[Solvers](https://inspect.aisi.org.uk/solvers.html) are the execution components in Inspect AI. They can run [agent scaffolds](https://inspect.aisi.org.uk/agents.html) (like [ReAct](https://inspect.aisi.org.uk/react-agent.html)), execute solution scripts (like the Oracle solver), perform prompt engineering, and more. Both solvers and agents can be used to solve Harbor tasks.

### Default Agent Scaffold

When no agent or solver is specified, Inspect Harbor provides a default agent scaffold for your model:

- **Agent Type**: [ReAct agent](https://inspect.aisi.org.uk/react-agent.html)
- **Tools**: [`bash(timeout=300)`](https://inspect.aisi.org.uk/tools-standard.html#sec-bash-session), [`python(timeout=300)`](https://inspect.aisi.org.uk/tools-standard.html#sec-bash-and-python), [`update_plan()`](https://inspect.aisi.org.uk/tools-standard.html#sec-update-plan)
- **Compaction**: [`CompactionEdit()`](https://inspect.aisi.org.uk/compaction.html) for context window management

This default configuration is suitable for most Harbor tasks that require command execution and file manipulation.

### Using Custom Agents

You can provide your own agent or solver implementation using the `--solver` flag:

**Using a custom agent:**
```bash
inspect eval inspect_harbor/terminal_bench \
  --solver path/to/custom/agent.py@custom_agent \
  --model openai/gpt-5
```

**Using Inspect SWE agent framework:**

First install the required package:

```bash
pip install inspect-swe
```

**CLI:**
```bash
inspect eval inspect_harbor/terminal_bench_sample \
  --solver inspect_swe/claude_code \
  --model anthropic/claude-sonnet-4-5
```

**Python API:**
```python
from inspect_ai import eval
from inspect_harbor import terminal_bench_sample
from inspect_swe import claude_code

eval(
    terminal_bench_sample(),
    solver=claude_code(),
    model="anthropic/claude-sonnet-4-5"
)
```

For more details:
- [Agents documentation](https://inspect.aisi.org.uk/agents.html)
- [Solvers documentation](https://inspect.aisi.org.uk/solvers.html)
- [Inspect SWE documentation](https://meridianlabs-ai.github.io/inspect_swe/)

## Task Parameters

Task functions (like `terminal_bench()`, `swe_lancer_diamond()`, etc.) accept the following parameters:

| Parameter | Description | Default | Python Example | CLI Example |
|-----------|-------------|---------|----------------|-------------|
| `dataset_task_names` | List of task names to include (supports glob patterns) | `None` | `["aime_60", "aime_61"]` | `'["aime_60"]'` |
| `dataset_exclude_task_names` | List of task names to exclude (supports glob patterns) | `None` | `["aime_60"]` | `'["aime_60"]'` |
| `n_tasks` | Maximum number of tasks to run | `None` | `10` | `10` |
| `overwrite_cache` | Force re-download and overwrite cached tasks | `False` | `True` | `true` |
| `sandbox_env_name` | Sandbox environment name | `"docker"` | `"modal"` | `"modal"` |
| `override_cpus` | Override the number of CPUs from `task.toml` | `None` | `4` | `4` |
| `override_memory_mb` | Override the memory (in MB) from `task.toml` | `None` | `16384` | `16384` |
| `override_gpus` | Override the number of GPUs from `task.toml` | `None` | `1` | `1` |

### Example

Here's an example showing how to use multiple parameters together:

**CLI:**
```bash
inspect eval inspect_harbor/terminal_bench_sample \
  -T n_tasks=5 \
  -T overwrite_cache=true \
  -T override_memory_mb=8192 \
  --model anthropic/claude-sonnet-4-5
```

**Python API:**
```python
from inspect_ai import eval
from inspect_harbor import terminal_bench_sample

eval(
    terminal_bench_sample(
        n_tasks=5,
        overwrite_cache=True,
        override_memory_mb=8192,
    ),
    model="anthropic/claude-sonnet-4-5"
)
```

This example:
- Limits to 5 tasks using `n_tasks`
- Forces fresh download with `overwrite_cache`
- Allocates 8GB of memory

## Understanding Harbor Tasks

### What is a Harbor Task?

[Harbor](https://harborframework.com/) is a framework for building, evaluating, and optimizing agents and models in containerized environments. A Harbor task is a self-contained evaluation unit that includes an instruction, execution environment, scoring criteria, and optionally a reference solution.

For comprehensive details about Harbor tasks, see the [Harbor documentation](https://harborframework.com/docs/tasks).

### Harbor Task File Structure

A typical Harbor task directory contains the following components:

```
my_task/
├── instruction.md      # Task instructions/prompt shown to the agent
├── task.toml           # Metadata, timeouts, resource specs (CPU/memory/GPU), env vars
├── environment/        # Environment setup - Dockerfile or docker-compose.yaml
│   └── Dockerfile      # Docker environment spec (varies by sandbox provider)
├── solution/           # (Optional) Reference solution for sanity checking
│   ├── solve.sh        # Executable solution script used by Oracle solver
│   └── ...             # Supporting solution files and dependencies
└── tests/              # Verification and scoring
    ├── test.sh         # Test script executed by verifier
    └── ...             # Outputs reward.txt or reward.json to /logs/verifier/
```

### Harbor to Inspect Mapping

Inspect Harbor bridges Harbor tasks to the Inspect AI evaluation framework using the following mappings:

| Harbor Concept | Inspect Concept | Description |
|----------------|-----------------|-------------|
| **Harbor Task** | [`Sample`](https://inspect.aisi.org.uk/datasets.html#dataset-samples) | A single evaluation instance with instructions and environment |
| **Harbor Dataset** | [`Task`](https://inspect.aisi.org.uk/tasks.html) | A collection of related evaluation instances |
| **instruction.md** | [`Sample.input`](https://inspect.aisi.org.uk/datasets.html#dataset-samples) | The prompt/instructions given to the agent |
| **environment/** | [`SandboxEnvironmentSpec`](https://inspect.aisi.org.uk/sandboxing.html#sandbox-environments) | Docker/environment configuration for isolated execution |
| **tests/test.sh** | [`Scorer`](https://inspect.aisi.org.uk/scorers.html) ([`inspect_harbor/harbor_scorer`](src/inspect_harbor/harbor/_scorer.py)) | Test script executed by the scorer to produce reward/metrics |
| **solution/solve.sh** | [`Solver`](https://inspect.aisi.org.uk/solvers.html) ([`inspect_harbor/oracle`](src/inspect_harbor/harbor/_solver.py)) | Reference solution script executed by the Oracle solver for sanity checking |
| **task.toml[metadata]** | [`Sample.metadata`](https://inspect.aisi.org.uk/datasets.html#dataset-samples) | Task metadata: author, difficulty, category, tags |
| **task.toml[verifier]** | Scorer timeout/env vars | Timeout and environment configuration for scorer execution |
| **task.toml[agent]** | Agent solver env vars | Environment variables for agent execution. Agent timeout_sec is ignored. |
| **task.toml[solution]** | Oracle solver env vars | Environment variables to set when running the solution script |
| **task.toml[environment]** | [`SandboxEnvironmentSpec.config`](https://inspect.aisi.org.uk/sandboxing.html#sandbox-environments) | Resource specifications (CPU, memory, storage, GPU, internet). Overwrites resource limits in `environment/docker-compose.yaml` |

### LLM Judges in Verification

Some Harbor tasks use LLM judges for verification (e.g., evaluating open-ended responses or code quality). These tasks specify the model in their `task.toml`:

```toml
[verifier.env]
MODEL_NAME = "claude-haiku-4-5"
ANTHROPIC_API_KEY = "${ANTHROPIC_API_KEY}"
```

The verifier script (`tests/test.sh`) uses these environment variables to call the LLM. Make sure to set the appropriate API key (e.g., `ANTHROPIC_API_KEY`) when running tasks with LLM judges.

## Advanced

### Oracle Solver

The Oracle solver is useful for verifying that a dataset is correctly configured and solvable. It executes the task's reference solution (`solution/solve.sh` script) instead of using a model.

**CLI:**
```bash
inspect eval inspect_harbor/hello_world \
  --solver inspect_harbor/oracle
```

**Python API:**
```python
from inspect_ai import eval
from inspect_harbor import hello_world, oracle

eval(hello_world(), solver=oracle())
```

### Generic Harbor Interface

For advanced use cases, you can use the generic `harbor()` interface directly. This provides access to all task loading options including custom registries, git repositories, and local paths.

#### Harbor Interface Parameters

The `harbor()` function accepts all parameters from the [Task Parameters](#task-parameters) table plus additional parameters for advanced task loading:

| Parameter | Description | Default | Python Example | CLI Example |
|-----------|-------------|---------|----------------|-------------|
| `path` | Local path to task/dataset directory, or task identifier for git tasks | `None` | `"/path/to/local_dataset"` | `"/path/to/local_dataset"` |
| `task_git_url` | Git repository URL for downloading tasks | `None` | `"https://github.com/laude-institute/harbor-datasets.git"` | `"https://github.com/..."` |
| `task_git_commit_id` | Git commit ID to pin task version | `None` | `"414014c23ce4d32128073d12b057252c918cccf4"` | `"414014c..."` |
| `registry_url` | Custom registry URL | `None` (uses Harbor registry) | `"https://github.com/myorg/registry.json"` | `"https://..."` |
| `registry_path` | Path to local registry | `None` | `"/path/to/local/registry.json"` | `"/path/to/local/registry.json"` |
| `dataset_name_version` | Dataset name and optional version (format: `name@version`). Omitted versions resolve to: `"head"` > highest semver > lexically last. | `None` | `"aime"` or `"aime@1.0"` | `"aime@1.0"` |
| `disable_verification` | Skip task verification checks | `False` | `True` | `true` |

**Note:** These are task-specific parameters passed with `-T`. For additional `inspect eval` command-line flags (like `--model`, `--message-limit`, `--epochs`, `--fail-on-error`, `--log-dir`, `--log-level`, `--max-tasks`, etc.), see the [Inspect eval CLI reference](https://inspect.aisi.org.uk/reference/inspect_eval.html) or [Python API reference](https://inspect.aisi.org.uk/reference/inspect_ai.html#eval).

#### Parameter Combinations

There are four primary patterns for loading Harbor tasks:

| Pattern | Required Parameters | Optional Parameters |
|---------|---------------------|---------------------|
| **Registry Dataset** | `dataset_name_version` | `registry_url` or `registry_path`<br>`dataset_task_names`<br>`dataset_exclude_task_names`<br>`n_tasks`<br>`overwrite_cache` |
| **Git Task** | `path`<br>`task_git_url` | `task_git_commit_id`<br>`overwrite_cache` |
| **Local Task** | `path` | `disable_verification` |
| **Local Dataset** | `path` | `dataset_task_names`<br>`dataset_exclude_task_names`<br>`n_tasks`<br>`disable_verification` |

#### Custom Registries

You can use custom registries for private or organization-specific datasets:

**Remote registry:**
```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="my_dataset@1.0" \
  -T registry_url="https://github.com/myorg/registry.json" \
  --model openai/gpt-5-mini
```

**Local registry:**
```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="my_dataset@1.0" \
  -T registry_path="/path/to/local/registry.json" \
  --model openai/gpt-5-mini
```

#### Loading from Git Repositories

You can load tasks directly from git repositories:

```bash
inspect eval inspect_harbor/harbor \
  -T path="datasets/aime/aime_6" \
  -T task_git_url="https://github.com/laude-institute/harbor-datasets.git" \
  -T task_git_commit_id="414014c23ce4d32128073d12b057252c918cccf4" \
  --model openai/gpt-5-mini
```

#### Loading from Local Paths

You can run tasks from your local filesystem:

```bash
inspect eval inspect_harbor/harbor \
  -T path="/path/to/task_or_dataset/directory" \
  --model openai/gpt-5
```

### Cache Management

Downloaded tasks are cached locally in `~/.harbor/cache/`. To force a fresh download:

```bash
inspect eval inspect_harbor/aime_1_0 \
  -T overwrite_cache=true \
  --model openai/gpt-5
```

To manually clear the entire cache:
```bash
rm -rf ~/.harbor/cache/
```

## Development

Clone the repository and install development dependencies:

```bash
git clone https://github.com/meridianlabs-ai/inspect_harbor.git
cd inspect_harbor
make install  # Installs dependencies and sets up pre-commit hooks
```

Run tests and checks:

```bash
make check    # Run linting (ruff check + format) and type checking (pyright)
make test     # Run tests
make cov      # Run tests with coverage report
```

Clean up build artifacts:

```bash
make clean    # Remove cache and build artifacts
```

## Credits

This work is based on contributions by [@iphan](https://github.com/iphan) and [@anthonyduong9](https://github.com/anthonyduong9) from the `inspect_evals` repository:

- [@iphan](https://github.com/iphan)'s [Terminal Bench implementation](https://github.com/UKGovernmentBEIS/inspect_evals/pull/791)
- [@anthonyduong9](https://github.com/anthonyduong9)'s [Harbor task implementation](https://github.com/UKGovernmentBEIS/inspect_evals/pull/945)
