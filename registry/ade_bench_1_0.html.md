# ade-bench@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/ade_bench_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import ade_bench_1_0

eval(ade_bench_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [ade-bench@1.0](https://registry.harborframework.com/datasets/dbt-labs/ade-bench/latest) |
| Inspect task | `ade_bench_1_0` |
| Version | 1.0 |
| Samples | 48 |
| Source | <https://github.com/dbt-labs/ade-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
