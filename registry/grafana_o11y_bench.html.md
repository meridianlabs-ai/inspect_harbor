# grafana/o11y-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/grafana_o11y_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import grafana_o11y_bench

eval(grafana_o11y_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [grafana/o11y-bench](https://hub.harborframework.com/datasets/grafana/o11y-bench/latest) |
| Inspect task | `grafana_o11y_bench` |
| Latest digest | sha256:21da264a4a15f52bfe92d858a7b766d28f92f9f85607dfa9be35c8d58fb035ac |
| Samples | 63 |
| Source | <https://github.com/grafana/o11y-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
