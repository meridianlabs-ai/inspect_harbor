# infra-bench/infra-bench-v1 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/infra_bench_v1 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import infra_bench_v1

eval(infra_bench_v1(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [infra-bench/infra-bench-v1](https://hub.harborframework.com/datasets/infra-bench/infra-bench-v1/latest) |
| Inspect task | `infra_bench_v1` |
| Latest digest | sha256:ee4dab2ad2279aaf0bc52c2736083844e9555ef86236e8ee7867bd0ba7afde87 |
| Samples | 20 |
| Source | <https://github.com/sammysun0711/InfraBench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
