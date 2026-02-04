# Inspect Harbor

Inspect AI adapter for Harbor tasks. This package provides an interface to run [Harbor](https://github.com/meridianlabs-ai/harbor) evaluation tasks using [Inspect AI](https://inspect.ai-safety-institute.org.uk/).

## Installation

Using pip:

```bash
git clone https://github.com/meridianlabs-ai/inspect_harbor.git
cd inspect_harbor
pip install -e .
```

Using uv:

```bash
git clone https://github.com/meridianlabs-ai/inspect_harbor.git
cd inspect_harbor
uv sync
```

## Usage

### Running Tasks with Oracle Solver

The oracle solver executes the provided solution script:

```bash
inspect eval src/inspect_harbor/_task.py@harbor_task \
  -T dataset_name_version="aime@1.0" \
  -T dataset_task_names="aime60" \
  --solver inspect_harbor/oracle
```

### Running Tasks with AI Models

Use the default react solver to evaluate model performance:

```bash
inspect eval src/inspect_harbor/_task.py@harbor_task \
  -T dataset_name_version="aime@1.0" \
  -T dataset_task_names="aime60" \
  --model openai/gpt-4o-mini
```

### Task and Dataset Sources

#### From Registry (Default)

By default, tasks are loaded from the [Harbor registry](https://github.com/laude-institute/harbor/blob/main/registry.json):

```bash
# Load from default Harbor registry
inspect eval src/inspect_harbor/_task.py@harbor_task \
  -T dataset_name_version="aime@1.0" \
  --model openai/gpt-4o-mini
```

```bash
# Load from custom registry URL
inspect eval src/inspect_harbor/_task.py@harbor_task \
  -T dataset_name_version="aime@1.0" \
  -T registry_url="https://github.com/custom/registry.json" \
  --model openai/gpt-4o-mini
```

```bash
# Load from local registry
inspect eval src/inspect_harbor/_task.py@harbor_task \
  -T dataset_name_version="aime@1.0" \
  -T registry_path="/path/to/local/registry.json" \
  --model openai/gpt-4o-mini
```

#### From Local Path

```bash
# Run a single local task
inspect eval src/inspect_harbor/_task.py@harbor_task \
  -T path="/path/to/task/directory" \
  --model openai/gpt-4o-mini
```

```bash
# Run tasks from a local dataset directory
inspect eval src/inspect_harbor/_task.py@harbor_task \
  -T path="/path/to/dataset/directory" \
  -T n_tasks=5 \
  --model openai/gpt-4o-mini
```

#### From Git Repository

```bash
# Download and run a task from a git repository
inspect eval src/inspect_harbor/_task.py@harbor_task \
  -T path="aime_i-9" \
  -T task_git_url="https://github.com/example/tasks.git" \
  -T task_git_commit_id="abc123" \
  --model openai/gpt-4o-mini
```

### Filtering Tasks

```bash
# Run specific tasks by name (supports glob patterns)
inspect eval src/inspect_harbor/_task.py@harbor_task \
  -T dataset_name_version="aime@1.0" \
  -T dataset_task_names='["aime_*", "task-42"]' \
  --model openai/gpt-4o-mini
```

```bash
# Exclude specific tasks (supports glob patterns)
inspect eval src/inspect_harbor/_task.py@harbor_task \
  -T dataset_name_version="aime@1.0" \
  -T dataset_exclude_task_names='["*_test", "debug_*"]' \
  --model openai/gpt-4o-mini
```

```bash
# Limit number of tasks
inspect eval src/inspect_harbor/_task.py@harbor_task \
  -T dataset_name_version="aime@1.0" \
  -T n_tasks=10 \
  --model openai/gpt-4o-mini
```

## Task Parameters

| Parameter | Description |
|-----------|-------------|
| `path` | Local path to task/dataset directory, or task identifier for git tasks |
| `task_git_url` | Git repository URL for downloading tasks |
| `task_git_commit_id` | Git commit ID to pin task version |
| `registry_url` | Custom registry URL (defaults to Harbor registry) |
| `registry_path` | Path to local registry |
| `dataset_name_version` | Dataset name and version (format: `name@version`) |
| `dataset_task_names` | List of task names to include (supports glob patterns) |
| `dataset_exclude_task_names` | List of task names to exclude (supports glob patterns) |
| `n_tasks` | Maximum number of tasks to run |
| `disable_verification` | Skip task verification checks |
| `solver` | Custom solver (defaults to react with bash/python tools) |

## Development

Install development dependencies:

Using pip:

```bash
pip install -e ".[dev]"
```

Using uv:

```bash
uv sync  # Dev dependencies are included by default
```

Run tests and checks:

```bash
# Run tests
pytest

# Run type checking
pyright

# Run linting
ruff check
```
