# humanevalfix@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/humanevalfix_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import humanevalfix_1_0

eval(humanevalfix_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [humanevalfix@1.0](https://registry.harborframework.com/datasets/bigcode/humanevalfix/latest) |
| Inspect task | `humanevalfix_1_0` |
| Version | 1.0 |
| Samples | 164 |
| Paper | [arxiv](https://arxiv.org/abs/2308.07124) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
