# deveval/deveval – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/deveval --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import deveval

eval(deveval(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [deveval/deveval](https://hub.harborframework.com/datasets/deveval/deveval/latest) |
| Inspect task | `deveval` |
| Latest digest | sha256:362b00a719d161f95bbd9a8186ec612d07fcd441fa617fb367f9f9142ecd3c61 |
| Samples | 63 |
| Paper | [arxiv](https://arxiv.org/abs/2403.08604) |
| Source | <https://github.com/seketeam/DevEval> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
