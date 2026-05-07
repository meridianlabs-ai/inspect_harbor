# dbt-labs/ade-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/dbt_labs_ade_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import dbt_labs_ade_bench

eval(dbt_labs_ade_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [dbt-labs/ade-bench](https://hub.harborframework.com/datasets/dbt-labs/ade-bench/latest) |
| Inspect task | `dbt_labs_ade_bench` |
| Latest digest | sha256:2c1f9e6966d01b0a5de2235d1a0b64089c7eead42c85c3b7b61d0929405c2bd5 |
| Samples | 48 |
| Source | <https://github.com/dbt-labs/ade-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
