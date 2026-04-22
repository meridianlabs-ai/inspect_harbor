# autocodebench@lite200 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/autocodebench_lite200 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import autocodebench_lite200

eval(autocodebench_lite200(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [autocodebench@lite200](https://registry.harborframework.com/datasets/tencent/autocodebench/latest) |
| Inspect task | `autocodebench_lite200` |
| Version | lite200 |
| Samples | 200 |
| Paper | [arxiv](https://arxiv.org/abs/2508.09101) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
