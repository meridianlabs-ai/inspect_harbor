# zenml/zenml-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/zenml_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import zenml_bench

eval(zenml_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [zenml/zenml-bench](https://hub.harborframework.com/datasets/zenml/zenml-bench/latest) |
| Inspect task | `zenml_bench` |
| Latest digest | sha256:5b0d64fed74870782a4c03763e8a4821dae3213c67bd470ae42d6fa854e73aa7 |
| Samples | 18 |
| Source | <https://github.com/zenml-io/zenml-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
