# Inspect Harbor

This package provides an interface to run [Harbor](https://harborframework.com/docs/tasks) tasks using [Inspect AI](https://inspect.ai-safety-institute.org.uk/).

## Installation

Using uv:

```bash
git clone https://github.com/meridianlabs-ai/inspect_harbor.git
cd inspect_harbor
uv sync
```

Using pip:

```bash
git clone https://github.com/meridianlabs-ai/inspect_harbor.git
cd inspect_harbor
pip install -e .
```

## Prerequisites

Before running Harbor tasks, ensure you have:

- **Python 3.12 or higher** - Required by inspect_harbor
- **Docker installed and running** - Required for execution when using Docker sandbox (default)
- **Model API keys** - Set appropriate environment variables (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)

## Understanding Harbor Tasks

### What is a Harbor Task?

Harbor is a framework for building, evaluating, and optimizing agents and models in containerized environments. A Harbor task is a self-contained evaluation unit that includes an instruction, execution environment, scoring criteria, and optionally a reference solution.

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
| **task.toml[verifier]** | Scorer timeout/env vars | Timeout and environment configuration for test execution |
| **task.toml[agent]** | [`Task.time_limit`](https://inspect.aisi.org.uk/tasks.html#task-options) | Agent timeout per Harbor task. Mapped to `Task.time_limit` using the maximum value across all samples |
| **task.toml[solution]** | Oracle solver env vars | Environment variables to set when running the solution script |
| **task.toml[environment]** | [`SandboxEnvironmentSpec.config`](https://inspect.aisi.org.uk/sandboxing.html#sandbox-environments) | Resource specifications (CPU, memory, storage, GPU, internet). Overwrites resource limits in `environment/docker-compose.yaml` |

## Quick Start

The fastest way to get started is to run a task from the [Harbor registry](https://harborframework.com/registry).

### Evaluate with a Model

Run a Harbor task with any [Inspect-compatible model](https://inspect.aisi.org.uk/models.html):

```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="aime@1.0" \
  -T dataset_task_names='["aime_60"]' \
  --model openai/gpt-4o-mini
```

This command:
- Loads the `aime@1.0` dataset from the [Harbor registry](https://harborframework.com/registry)
- Downloads and caches the `aime_60` task
- Runs the `aime_60` task
- Evaluates using GPT-4o-mini with the [default ReAct agent scaffold](#default-agent-scaffold)
- Executes in a [Docker sandbox environment](https://inspect.aisi.org.uk/sandboxing.html#sec-docker-configuration)
- Stores results in `./logs`

**Note:** To execute the whole dataset, omit the `dataset_task_names` task parameter.

### Verify with Oracle Solver

Before evaluating with models, you can verify that a task is solvable using its reference solution:

```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="aime@1.0" \
  -T dataset_task_names='["aime_60"]' \
  --solver inspect_harbor/oracle
```

The Oracle solver executes the task's `solution/solve.sh` script to confirm the task is correctly configured and solvable.

### Using the Python API

You can also run Harbor tasks programmatically using the Python API:

```python
from inspect_ai import eval
from inspect_harbor import harbor

eval(
    harbor(
        dataset_name_version="aime@1.0",
        dataset_task_names=["aime_60"]
    ),
    model="openai/gpt-4o-mini"
)
```

**With Oracle solver:**
```python
from inspect_ai import eval
from inspect_harbor import harbor, oracle

eval(
    harbor(
        dataset_name_version="aime@1.0",
        dataset_task_names=["aime_60"],
        solver=oracle()
    )
)
```

**With custom parameters:**
```python
from inspect_ai import eval
from inspect_harbor import harbor

eval(
    harbor(
        path="/path/to/local/dataset",
        message_limit=100,
    ),
    model="openai/gpt-4o-mini",
    continue_on_fail=True
)
```

## Harbor Registry

The Harbor registry is a centralized catalog of curated Harbor datasets and tasks. Inspect Harbor uses this registry to automatically download and resolve datasets, following the same behavior as Harbor.

### Default Registry

By default, Inspect Harbor uses the official [Harbor registry](https://github.com/laude-institute/harbor/blob/main/registry.json). When you specify a `dataset_name_version`, it automatically:

1. Looks up the dataset in the registry
2. Finds the corresponding GitHub repository
3. Downloads only the requested tasks (or all tasks if not filtered)
4. Caches them locally for future use

**Example:**
```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="aime@1.0" \
  -T dataset_task_names='["aime_60"]' \
  --model openai/gpt-4o-mini
```

→ Resolves to [harbor-datasets/aime](https://github.com/laude-institute/harbor-datasets/tree/main/datasets/aime) version `1.0` and downloads only the `aime_60` task

### Custom Registries

You can use custom registries for private or organization-specific datasets:

**Remote registry:**
```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="my_dataset@1.0" \
  -T registry_url="https://github.com/myorg/registry.json" \
  --model openai/gpt-4o-mini
```

**Local registry:**
```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="my_dataset@1.0" \
  -T registry_path="/path/to/local/registry.json" \
  --model openai/gpt-4o-mini
```

### Cache Management

Downloaded tasks are cached locally. To force a fresh download:

```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="aime@1.0" \
  -T overwrite_cache=true \
  --model openai/gpt-4o-mini
```

## Usage

### Agents and Solvers

[Solvers](https://inspect.aisi.org.uk/solvers.html) are the execution components in Inspect AI. They can run [agent scaffolds](https://inspect.aisi.org.uk/agents.html) (like [ReAct](https://inspect.aisi.org.uk/react-agent.html)), execute solution scripts (like the Oracle solver), perform prompt engineering, and more. Both solvers and agents can be used to solve Harbor tasks.

#### Default Agent Scaffold

When no agent or solver is specified, Inspect Harbor provides a default agent scaffold for your model:

- **Agent Type**: [ReAct agent](https://inspect.aisi.org.uk/react-agent.html)
- **Tools**: [`bash(timeout=300)`](https://inspect.aisi.org.uk/tools-standard.html#sec-bash-session), [`python(timeout=300)`](https://inspect.aisi.org.uk/tools-standard.html#sec-bash-and-python), [`memory()`](https://inspect.aisi.org.uk/tools-standard.html#sec-memory), [`update_plan()`](https://inspect.aisi.org.uk/tools-standard.html#sec-update-plan)
- **Submission**: Disabled (`submit=False`) - agents write answers to files for evaluation
- **Compaction**: [`CompactionEdit()`](https://inspect.aisi.org.uk/compaction.html) for context window management

This default configuration is suitable for most Harbor tasks that require command execution and file manipulation.

#### Using Custom Agents

You can provide your own agent or solver implementation using the `--solver` flag:

**Using a custom agent:**
```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="aime@1.0" \
  --solver path/to/custom/agent.py@custom_agent
  --model openai/gpt-4o-mini
```

**Using Inspect SWE agent framework:**

First install the required package:
```bash
pip install inspect-swe
```

Then use it via CLI:
```bash
inspect eval inspect_harbor/harbor \
  -T dataset_name_version="aime@1.0" \
  --solver inspect_swe/claude_code
```

Or via Python API:
```python
from inspect_ai import eval
from inspect_harbor import harbor
from inspect_swe import claude_code

eval(
    harbor(dataset_name_version="aime@1.0"),
    solver=claude_code(),
)
```

For more details:
- [Agents documentation](https://inspect.aisi.org.uk/agents.html)
- [Solvers documentation](https://inspect.aisi.org.uk/solvers.html)
- [Inspect SWE documentation](https://meridianlabs-ai.github.io/inspect_swe/)

### Task and Dataset Sources

In addition to the [Harbor Registry](#harbor-registry) (covered above), you can also load Harbor tasks from local filesystems or git repositories.

#### From Local Path

```bash
# Run a single local task or dataset
inspect eval inspect_harbor/harbor \
  -T path="/path/to/task_or_dataset/directory" \
  --model openai/gpt-4o-mini
```

#### From Git Repository

```bash
# Download and run a task from a git repository
inspect eval inspect_harbor/harbor \
  -T path="aime_60" \
  -T task_git_url="https://github.com/example/tasks.git" \
  -T task_git_commit_id="abc123" \
  --model openai/gpt-4o-mini
```

### Task Parameters

The following parameters configure the Inspect Harbor task interface. They can be used in Python by importing `inspect_harbor.harbor` or via the command line with `inspect eval inspect_harbor/harbor -T <parameter>=<value>`.

| Parameter | Description | Example |
|-----------|-------------|---------|
| `path` | Local path to task/dataset directory, or task identifier for git tasks | `"/path/to/task"` or `"aime_i-9"` |
| `task_git_url` | Git repository URL for downloading tasks | `"https://github.com/example/tasks.git"` |
| `task_git_commit_id` | Git commit ID to pin task version | `"abc123"` |
| `registry_url` | Custom registry URL (defaults to Harbor registry) | `"https://github.com/custom/registry.json"` |
| `registry_path` | Path to local registry | `"/path/to/registry.json"` |
| `dataset_name_version` | Dataset name and version (format: `name@version`) | `"aime@1.0"` |
| `dataset_task_names` | List of task names to include (supports glob patterns) | `'["aime_60", "aime_61"]'` or `'["aime*"]'` |
| `dataset_exclude_task_names` | List of task names to exclude (supports glob patterns) | `'["task1", "task2"]'` |
| `n_tasks` | Maximum number of tasks to run | `10` |
| `disable_verification` | Skip task verification checks | `true` or `false` |
| `overwrite_cache` | Force re-download and overwrite cached tasks (default: `false`). Works for both git tasks and registry datasets. | `true` or `false` |
| `sandbox_env_name` | Sandbox environment name (default: `"docker"`) | `"modal"` or `"docker"` |
| `solver` | Custom solver (defaults to ReAct agent with bash/python/memory/update_plan tools) | `inspect_harbor/oracle` |
| `**kwargs` | Additional keyword arguments passed to `Task()` (e.g., `message_limit`, `epochs`, `fail_on_error`) | `message_limit=100` |

**Note:** These are task-specific parameters passed with `-T`. For additional `inspect eval` command-line flags (like `--model`, `--log-dir`, `--log-level`, `--max-tasks`, etc.), see the [Inspect eval reference documentation](https://inspect.aisi.org.uk/reference/inspect_eval.html).

## Development

Install development dependencies:

```bash
make install  # Installs dependencies and sets up pre-commit hooks
```

Or manually using uv:

```bash
uv sync
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
