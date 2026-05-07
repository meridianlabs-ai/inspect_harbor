# adyen/dabstep – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/adyen_dabstep --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import adyen_dabstep

eval(adyen_dabstep(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [adyen/dabstep](https://hub.harborframework.com/datasets/adyen/dabstep/latest) |
| Inspect task | `adyen_dabstep` |
| Latest digest | sha256:0edf62c0bdf7003b1d1f934f1547df1c051877e076d5b6f6a2d99caf8b6432b3 |
| Samples | 450 |
| Paper | [arxiv](https://arxiv.org/abs/2506.23719) |
| Source | <https://huggingface.co/datasets/adyen/DABstep> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
