# otel-bench@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/otel_bench_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import otel_bench_1_0

eval(otel_bench_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [otel-bench@1.0](https://registry.harborframework.com/datasets/quesma/otel-bench/latest) |
| Inspect task | `otel_bench_1_0` |
| Version | 1.0 |
| Samples | 26 |
| Source | <https://github.com/QuesmaOrg/otel-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
