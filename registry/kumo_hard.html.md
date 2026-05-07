# kumo/kumo-hard – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/kumo_hard --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import kumo_hard

eval(kumo_hard(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [kumo/kumo-hard](https://hub.harborframework.com/datasets/kumo/kumo-hard/latest) |
| Inspect task | `kumo_hard` |
| Latest digest | sha256:6f175f28349747cc2b018c23e3f60aeafa1ab2c331fc389d69b9308eb68bf458 |
| Samples | 250 |
| Paper | [arxiv](https://arxiv.org/abs/2504.02810) |
| Source | <https://github.com/linhaowei1/kumo> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
