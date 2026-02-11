# Inspect Harbor

This package provides an interface to run [Harbor](https://harborframework.com/) tasks using [Inspect AI](https://inspect.ai-safety-institute.org.uk/).

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

Run a Harbor dataset with any [Inspect-compatible model](https://inspect.aisi.org.uk/models.html):

```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="hello-world" \
  --model openai/gpt-5-mini
```

Or run a different dataset:

```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="terminal-bench-sample" \
  --model openai/gpt-5-mini
```

This command:
- Loads the `terminal-bench-sample@2.0` dataset (latest version) from the [Harbor registry](https://harborframework.com/registry)
- Downloads and caches all [10 tasks](https://harborframework.com/registry/terminal-bench-sample/2.0)
- Solves the tasks with the [default ReAct agent](#default-agent-scaffold) using GPT-5-mini
- Executes in a [Docker sandbox environment](https://inspect.aisi.org.uk/sandboxing.html#sec-docker-configuration)
- Stores results in `./logs`

### Using the Python API

You can also run Harbor tasks programmatically using the Python API:

```python
from inspect_ai import eval
from inspect_harbor import harbor

eval(
    harbor(dataset_name_version="hello-world"),
    model="openai/gpt-5-mini"
)
```

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

## Task Parameters

The following parameters configure the Inspect Harbor task interface. They can be used in Python by importing `inspect_harbor.harbor` or via the command line with `inspect eval inspect_harbor/harbor -T <parameter>=<value>`.

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `path` | Local path to task/dataset directory, or task identifier for git tasks | `None` | `"/path/to/local_dataset_or_task"` or `"datasets/aime/aime_60"` |
| `task_git_url` | Git repository URL for downloading tasks | `None` | `"https://github.com/laude-institute/harbor-datasets.git"` |
| `task_git_commit_id` | Git commit ID to pin task version | `None` | `"414014c23ce4d32128073d12b057252c918cccf4"` |
| `registry_url` | Custom registry URL | `None` (uses Harbor registry) | `"https://raw.githubusercontent.com/laude-institute/harbor/refs/heads/main/registry.json"` |
| `registry_path` | Path to local registry | `None` | `"/path/to/local/registry.json"` |
| `dataset_name_version` | Dataset name and optional version (format: `name@version`). Omitted versions resolve to: `"head"` > highest semver > lexically last. | `None` | `"aime"` or `"aime@1.0"` |
| `dataset_task_names` | List of task names to include (supports glob patterns) | `None` | `'["aime_60", "aime_61"]'` or `'["aime*"]'` |
| `dataset_exclude_task_names` | List of task names to exclude (supports glob patterns) | `None` | `'["aime_60", "aime_61"]'` or `'["aime*"]'` |
| `n_tasks` | Maximum number of tasks to run. Preferred over `--max-samples`: only downloads n tasks instead of entire dataset. | `None` | `10` |
| `disable_verification` | Skip task verification checks | `False` | `true` or `false` |
| `overwrite_cache` | Force re-download and overwrite cached tasks. Works for both git tasks and registry datasets. | `False` | `true` or `false` |
| `sandbox_env_name` | Sandbox environment name | `"docker"` | `"modal"` or `"docker"` |
| `override_cpus` | Override the number of CPUs from `task.toml` | `None` | `4` |
| `override_memory_mb` | Override the memory (in MB) from `task.toml` | `None` | `16384` |
| `override_gpus` | Override the number of GPUs from `task.toml` | `None` | `1` |

**Note:** These are task-specific parameters passed with `-T`. For additional `inspect eval` command-line flags (like `--model`, `--message-limit`, `--epochs`, `--fail-on-error`, `--log-dir`, `--log-level`, `--max-tasks`, etc.), see the [Inspect eval CLI reference](https://inspect.aisi.org.uk/reference/inspect_eval.html) or [Python API reference](https://inspect.aisi.org.uk/reference/inspect_ai.html#eval).

## Harbor Registry

The Harbor registry is a centralized catalog of curated Harbor datasets and tasks. Inspect Harbor uses this registry to automatically download and resolve datasets, following the same behavior as Harbor.

### Default Registry

By default, Inspect Harbor uses the official [Harbor registry](https://raw.githubusercontent.com/laude-institute/harbor/refs/heads/main/registry.json). When you specify a `dataset_name_version`, it automatically:

1. Looks up the dataset in the registry
2. Finds the corresponding GitHub repository
3. Downloads only the requested tasks (or all tasks if not filtered)
4. Caches them locally for future use

**Example:**
```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="aime@1.0" \
  -T dataset_task_names='["aime_60"]' \
  --model openai/gpt-5-mini
```

→ Resolves to [harbor-datasets/aime](https://github.com/laude-institute/harbor-datasets/tree/main/datasets/aime) version `1.0` and downloads only the `aime_60` task

### Custom Registries

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

### Cache Management

Downloaded tasks are cached locally in `~/.harbor/cache/`. To force a fresh download:

```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="aime@1.0" \
  -T overwrite_cache=true \
  --model openai/gpt-5-mini
```

To manually clear the entire cache:
```bash
rm -rf ~/.harbor/cache/
```

## Usage

### Agents and Solvers

[Solvers](https://inspect.aisi.org.uk/solvers.html) are the execution components in Inspect AI. They can run [agent scaffolds](https://inspect.aisi.org.uk/agents.html) (like [ReAct](https://inspect.aisi.org.uk/react-agent.html)), execute solution scripts (like the Oracle solver), perform prompt engineering, and more. Both solvers and agents can be used to solve Harbor tasks.

#### Default Agent Scaffold

When no agent or solver is specified, Inspect Harbor provides a default agent scaffold for your model:

- **Agent Type**: [ReAct agent](https://inspect.aisi.org.uk/react-agent.html)
- **Tools**: [`bash(timeout=300)`](https://inspect.aisi.org.uk/tools-standard.html#sec-bash-session), [`python(timeout=300)`](https://inspect.aisi.org.uk/tools-standard.html#sec-bash-and-python), [`update_plan()`](https://inspect.aisi.org.uk/tools-standard.html#sec-update-plan)
- **Compaction**: [`CompactionEdit()`](https://inspect.aisi.org.uk/compaction.html) for context window management

This default configuration is suitable for most Harbor tasks that require command execution and file manipulation.

#### Using Custom Agents

You can provide your own agent or solver implementation using the `--solver` flag:

**Using a custom agent:**
```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="aime" \
  --solver path/to/custom/agent.py@custom_agent \
  --model openai/gpt-5-mini
```

**Using Inspect SWE agent framework:**

First install the required package:
```bash
pip install inspect-swe
```

**Note**: Make sure you have your `ANTHROPIC_API_KEY` in a `.env` file or set as an environment variable.

Then use it via CLI:
```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="aime" \
  --solver inspect_swe/claude_code \
  --model anthropic/claude-sonnet-4-5
```

Or via Python API:
```python
from inspect_ai import eval
from inspect_harbor import harbor
from inspect_swe import claude_code

eval(
    harbor(dataset_name_version="aime"),
    solver=claude_code(),
    model="anthropic/claude-sonnet-4-5"
)
```

#### Oracle Solver

The Oracle solver is useful for verifying that a dataset is correctly configured and solvable. It executes the task's reference solution (`solution/solve.sh` script) instead of using a model.

**CLI usage:**
```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="hello-world" \
  --solver inspect_harbor/oracle
```

**Python API usage:**
```python
from inspect_ai import eval
from inspect_harbor import harbor, oracle

eval(
    harbor(dataset_name_version="hello-world"),
    solver=oracle()
)
```

For more details:
- [Agents documentation](https://inspect.aisi.org.uk/agents.html)
- [Solvers documentation](https://inspect.aisi.org.uk/solvers.html)
- [Inspect SWE documentation](https://meridianlabs-ai.github.io/inspect_swe/)

### Task and Dataset Sources

In addition to the [Harbor Registry](#harbor-registry) (covered above), you can also load Harbor tasks from local filesystems or git repositories.

#### Parameter Combinations

There are four primary patterns for loading Harbor tasks:

| Pattern | Required Parameters | Optional Parameters |
|---------|---------------------|---------------------|
| **Registry Dataset** | `dataset_name_version` | `registry_url` or `registry_path`<br>`dataset_task_names`<br>`dataset_exclude_task_names`<br>`n_tasks`<br>`overwrite_cache` |
| **Git Task** | `path`<br>`task_git_url` | `task_git_commit_id`<br>`overwrite_cache` |
| **Local Task** | `path` | `disable_verification` |
| **Local Dataset** | `path` | `dataset_task_names`<br>`dataset_exclude_task_names`<br>`n_tasks`<br>`disable_verification` |

#### From Local Path

```bash
# Run a single local task or dataset
inspect eval inspect_harbor/harbor \
  -T path="/path/to/task_or_dataset/directory" \
  --model openai/gpt-5-mini
```

#### From Git Repository

```bash
# Download and run a task from a git repository
inspect eval inspect_harbor/harbor \
  -T path="datasets/aime/aime_6" \
  -T task_git_url="https://github.com/laude-institute/harbor-datasets.git" \
  -T task_git_commit_id="414014c23ce4d32128073d12b057252c918cccf4" \
  --model openai/gpt-5-mini
```

### Overrides

Inspect Harbor supports overriding resource specifications from a task's `task.toml` configuration. This is useful when you need more resources than specified in the task configuration.

#### Default Values

| Parameter | Default | Notes |
|-----------|---------|-------|
| `cpus` | 1 | Respects task config or override |
| `memory_mb` | 6144 (6GB) | 6GB minimum enforced (uses task config or override if ≥ 6GB) |
| `gpus` | 0 | Respects task config or override |

#### Examples

For example, `terminal-bench-sample` tasks may require more memory than the default 6GB minimum when using agents like Claude Code:

**CLI usage:**
```bash
# Override memory for Claude Code agent
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="terminal-bench-sample" \
  -T override_memory_mb=16384 \
  --solver inspect_swe/claude_code \
  --model anthropic/claude-sonnet-4-5
```

**Python API usage:**
```python
from inspect_ai import eval
from inspect_harbor import harbor
from inspect_swe import claude_code

eval(
    harbor(
        dataset_name_version="terminal-bench-sample",
        override_memory_mb=16384,  # 16GB in MB
    ),
    solver=claude_code(),
    model="anthropic/claude-sonnet-4-5"
)
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
