# Task Format

## What is a Harbor Task?

[Harbor](https://harborframework.com/) is a framework for building, evaluating, and optimizing agents and models in containerized environments. A Harbor task is a self-contained evaluation unit that includes an instruction, execution environment, scoring criteria, and optionally a reference solution.

For comprehensive details about Harbor tasks, see the [Harbor documentation](https://harborframework.com/docs/tasks).

## Harbor Task File Structure

A typical Harbor task directory contains the following components:

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

## Harbor to Inspect Mapping

Inspect Harbor bridges Harbor tasks to the Inspect AI evaluation framework using the following mappings:

| Harbor Concept | Inspect Concept | Description |
|----|----|----|
| **Harbor Task** | [`Sample`](https://inspect.aisi.org.uk/datasets.html#dataset-samples) | A single evaluation instance with instructions and environment |
| **Harbor Dataset** | [`Task`](https://inspect.aisi.org.uk/tasks.html) | A collection of related evaluation instances |
| **instruction.md** | [`Sample.input`](https://inspect.aisi.org.uk/datasets.html#dataset-samples) | The prompt/instructions given to the agent |
| **environment/** | [`SandboxEnvironmentSpec`](https://inspect.aisi.org.uk/sandboxing.html#sandbox-environments) | Docker/environment configuration for isolated execution |
| **tests/test.sh** | [`Scorer`](https://inspect.aisi.org.uk/scorers.html) (`harbor_scorer`) | Test script executed by the scorer to produce reward/metrics |
| **solution/solve.sh** | [`Solver`](https://inspect.aisi.org.uk/solvers.html) (`oracle`) | Reference solution script executed by the Oracle solver for sanity checking |
| **task.toml\[metadata\]** | [`Sample.metadata`](https://inspect.aisi.org.uk/datasets.html#dataset-samples) | Task metadata: author, difficulty, category, tags |
| **task.toml\[verifier\]** | Scorer timeout/env vars | Timeout and environment configuration for scorer execution |
| **task.toml\[agent\]** | Agent solver env vars | Environment variables for agent execution. Agent timeout_sec is ignored. |
| **task.toml\[solution\]** | Oracle solver env vars | Environment variables to set when running the solution script |
| **task.toml\[environment\]** | [`SandboxEnvironmentSpec.config`](https://inspect.aisi.org.uk/sandboxing.html#sandbox-environments) | Resource specifications (CPU, memory, storage, GPU, internet). Overwrites resource limits in `environment/docker-compose.yaml` |

## LLM Judges in Verification

Some Harbor tasks use LLM judges for verification (e.g. evaluating open-ended responses or code quality). These tasks specify the model in their `task.toml`:

``` toml
[verifier.env]
MODEL_NAME = "claude-haiku-4-5"
ANTHROPIC_API_KEY = "${ANTHROPIC_API_KEY}"
```

The verifier script (`tests/test.sh`) uses these environment variables to call the LLM. Make sure to set the appropriate API key (e.g. `ANTHROPIC_API_KEY`) when running tasks with LLM judges.
