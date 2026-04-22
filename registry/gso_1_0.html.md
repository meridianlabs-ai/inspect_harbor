# gso@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/gso_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import gso_1_0

eval(gso_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [gso@1.0](https://registry.harborframework.com/datasets?q=gso) |
| Inspect task | `gso_1_0` |
| Version | 1.0 |
| Samples | 102 |
| Paper | [arxiv](https://arxiv.org/abs/2505.23671) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
