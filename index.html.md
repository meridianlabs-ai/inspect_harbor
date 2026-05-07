# Inspect Harbor

[Harbor](https://harborframework.com/) is a framework for building, evaluating, and optimizing AI agents in containerized environments. Inspect Harbor provides an interface to run Harbor tasks using [Inspect AI](https://inspect.aisi.org.uk/).

## Installation

Install from PyPI:

``` bash
pip install inspect-harbor
```

Or with uv:

``` bash
uv add inspect-harbor
```

## Prerequisites

Before running Harbor tasks, ensure you have:

- **Python 3.12 or higher** – required by inspect_harbor.
- **Docker installed and running** – required for execution when using Docker sandbox (default).
- **Model API keys** – set appropriate environment variables (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).

## Quick Start

The fastest way to get started is to run a dataset from the [Harbor registry](./registry.html.md).

**CLI:**

``` bash
# Run Aider's Polyglot coding benchmark
inspect eval inspect_harbor/aider_polyglot --model openai/gpt-5-mini

# Run Terminal-Bench 2.0
inspect eval inspect_harbor/terminal_bench_2 --model openai/gpt-5
```

**Python API:**

``` python
from inspect_ai import eval
from inspect_harbor import aider_polyglot, terminal_bench_2

# Run Aider's Polyglot coding benchmark
eval(aider_polyglot(), model="openai/gpt-5-mini")

# Run Terminal-Bench 2.0
eval(terminal_bench_2(), model="openai/gpt-5")
```

### What this does

- Loads the dataset from the [Harbor registry](./registry.html.md).
- Downloads and caches all tasks in the dataset.
- Solves the tasks with the [default ReAct agent](./agents.html.md#default-agent) scaffold.
- Executes in a [Docker sandbox environment](https://inspect.aisi.org.uk/sandboxing.html#sec-docker-configuration).
- Stores results in `./logs`.

See the [Registry](./registry.html.md) for the full list of available datasets, and the [Using Harbor](./datasets.html.md) guides for more detail on datasets, task parameters, agents, and advanced features.
