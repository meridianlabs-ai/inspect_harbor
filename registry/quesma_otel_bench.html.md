# quesma/otel-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/quesma_otel_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import quesma_otel_bench

eval(quesma_otel_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [quesma/otel-bench](https://hub.harborframework.com/datasets/quesma/otel-bench/latest) |
| Inspect task | `quesma_otel_bench` |
| Latest digest | sha256:a6ca75f833dedb831238b42c5dccab7f4d95713db9f6933560a6cca2c052b4b9 |
| Samples | 26 |
| Source | <https://github.com/QuesmaOrg/otel-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
