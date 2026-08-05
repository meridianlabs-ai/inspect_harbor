# orca-bench/orca-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/orca_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import orca_bench

eval(orca_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [orca-bench/orca-bench](https://hub.harborframework.com/datasets/orca-bench/orca-bench/latest) |
| Inspect task | `orca_bench` |
| Latest digest | sha256:1ef729757d4974ffe4e835d541c601f957975edf8c93ef02eec97e26d3069b93 |
| Samples | 755 |
| Paper | [arxiv](https://arxiv.org/abs/2607.28545) |
| Source | <https://github.com/orca-bench/ORCA-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
