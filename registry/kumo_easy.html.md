# kumo/kumo-easy – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/kumo_easy --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import kumo_easy

eval(kumo_easy(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [kumo/kumo-easy](https://hub.harborframework.com/datasets/kumo/kumo-easy/latest) |
| Inspect task | `kumo_easy` |
| Latest digest | sha256:139cb4201654f1e12a110554b8c8630fa3d7759464436f9b48692d56fdc3d6d8 |
| Samples | 1000 |
| Paper | [arxiv](https://arxiv.org/abs/2504.02810) |
| Source | <https://github.com/linhaowei1/kumo> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
