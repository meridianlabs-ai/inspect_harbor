# swt-bench/swt-bench-verified – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/swt_bench_verified --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import swt_bench_verified

eval(swt_bench_verified(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [swt-bench/swt-bench-verified](https://hub.harborframework.com/datasets/swt-bench/swt-bench-verified/latest) |
| Inspect task | `swt_bench_verified` |
| Latest digest | sha256:0263229761bc27de1c646dd5d41f46073653d6cadb4efdeda6c05c879551c94a |
| Samples | 433 |
| Paper | [arxiv](https://arxiv.org/abs/2406.12952) |
| Source | <https://github.com/logic-star-ai/swt-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
