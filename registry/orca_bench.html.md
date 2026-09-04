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
| Latest digest | sha256:3e53f8f8e64b58400549e793b280b59166a0dd64ccb656657c29c9f5f98b02c3 |
| Samples | 755 |
| Paper | [arxiv](https://arxiv.org/abs/2607.28545) |
| Source | <https://github.com/orca-bench/ORCA-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
