# strongreject/strongreject – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/strongreject --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import strongreject

eval(strongreject(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [strongreject/strongreject](https://hub.harborframework.com/datasets/strongreject/strongreject/latest) |
| Inspect task | `strongreject` |
| Latest digest | sha256:c3d584ac2b1b50436fe5c6e8f99ebef907cf6808747f36371f4975d1b9bc6b2f |
| Samples | 150 |
| Paper | [arxiv](https://arxiv.org/abs/2402.10260) |
| Source | <https://github.com/alexandrasouly/strongreject> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
