# kumo/kumo-1 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/kumo_1 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import kumo_1

eval(kumo_1(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [kumo/kumo-1](https://hub.harborframework.com/datasets/kumo/kumo-1/latest) |
| Inspect task | `kumo_1` |
| Latest digest | sha256:a70e4f6c1a7cca8977db77461c8d341fb8dc481c857a48e28bc2b4ddcfa9e0ef |
| Samples | 5300 |
| Paper | [arxiv](https://arxiv.org/abs/2504.02810) |
| Source | <https://github.com/linhaowei1/kumo> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
