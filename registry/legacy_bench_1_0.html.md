# legacy-bench@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/legacy_bench_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import legacy_bench_1_0

eval(legacy_bench_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [legacy-bench@1.0](https://registry.harborframework.com/datasets/factory-ai/legacy-bench/latest) |
| Inspect task | `legacy_bench_1_0` |
| Version | 1.0 |
| Samples | 10 |
| Source | <https://factory.ai/news/legacy-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
