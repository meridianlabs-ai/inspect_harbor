# sldbench/sldbench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/sldbench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import sldbench

eval(sldbench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [sldbench/sldbench](https://hub.harborframework.com/datasets/sldbench/sldbench/latest) |
| Inspect task | `sldbench` |
| Latest digest | sha256:369ce8a4825cae7cfb75ef0f5886f3081f072123fd37630f6d6aeef8dec46089 |
| Samples | 8 |
| Paper | [arxiv](https://arxiv.org/abs/2507.21184) |
| Source | <https://github.com/linhaowei1/SLD> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
