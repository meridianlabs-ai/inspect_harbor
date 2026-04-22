# sldbench@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/sldbench_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import sldbench_1_0

eval(sldbench_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [sldbench@1.0](https://registry.harborframework.com/datasets/sldbench/sldbench/latest) |
| Inspect task | `sldbench_1_0` |
| Version | 1.0 |
| Samples | 8 |
| Paper | [arxiv](https://arxiv.org/abs/2507.21184) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
