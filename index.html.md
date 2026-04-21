# Inspect Harbor

Inspect Harbor provides an interface to run [Harbor](https://harborframework.com/) tasks using [Inspect AI](https://inspect.aisi.org.uk/).

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
# Run hello-world dataset
inspect eval inspect_harbor/hello_world --model openai/gpt-5-mini

# Run terminal-bench-sample dataset
inspect eval inspect_harbor/terminal_bench_sample --model openai/gpt-5
```

**Python API:**

``` python
from inspect_ai import eval
from inspect_harbor import hello_world, terminal_bench_sample

# Run hello-world
eval(hello_world(), model="openai/gpt-5-mini")

# Run terminal-bench-sample
eval(terminal_bench_sample(), model="openai/gpt-5")
```

### What this does

- Loads the dataset from the [Harbor registry](./registry.html.md).
- Downloads and caches all tasks in the dataset.
- Solves the tasks with the [default ReAct agent](./agents.html.md#default-agent-scaffold) scaffold.
- Executes in a [Docker sandbox environment](https://inspect.aisi.org.uk/sandboxing.html#sec-docker-configuration).
- Stores results in `./logs`.

See the [Registry](./registry.html.md) for the full list of available datasets, and the [Using Harbor](./datasets.html.md) guides for more detail on datasets, task parameters, agents, and advanced features.
