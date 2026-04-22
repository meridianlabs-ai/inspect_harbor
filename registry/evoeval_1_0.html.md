# evoeval@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/evoeval_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import evoeval_1_0

eval(evoeval_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [evoeval@1.0](https://registry.harborframework.com/datasets/evoeval/evoeval/latest) |
| Inspect task | `evoeval_1_0` |
| Version | 1.0 |
| Samples | 100 |
| Source | <https://github.com/evo-eval/evoeval> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
