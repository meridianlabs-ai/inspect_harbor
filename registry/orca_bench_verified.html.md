# orca-bench/orca-bench-verified – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/orca_bench_verified --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import orca_bench_verified

eval(orca_bench_verified(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [orca-bench/orca-bench-verified](https://hub.harborframework.com/datasets/orca-bench/orca-bench-verified/latest) |
| Inspect task | `orca_bench_verified` |
| Latest digest | sha256:263a25d01329e4409bc03bfcd9e6d9771d189f6060a4b2db831b5e89783f7162 |
| Samples | 40 |
| Paper | [arxiv](https://arxiv.org/abs/2607.28545) |
| Source | <https://github.com/orca-bench/ORCA-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
