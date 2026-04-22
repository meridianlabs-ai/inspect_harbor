# deveval@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/deveval_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import deveval_1_0

eval(deveval_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [deveval@1.0](https://registry.harborframework.com/datasets/deveval/deveval/latest) |
| Inspect task | `deveval_1_0` |
| Version | 1.0 |
| Samples | 63 |
| Paper | [arxiv](https://arxiv.org/abs/2403.08604) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
