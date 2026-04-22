# gaia@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/gaia_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import gaia_1_0

eval(gaia_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [gaia@1.0](https://registry.harborframework.com/datasets/gaia/gaia/latest) |
| Inspect task | `gaia_1_0` |
| Version | 1.0 |
| Samples | 165 |
| Paper | [arxiv](https://arxiv.org/abs/2311.12983) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
