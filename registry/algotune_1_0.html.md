# algotune@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/algotune_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import algotune_1_0

eval(algotune_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [algotune@1.0](https://registry.harborframework.com/datasets/algotune/algotune/latest) |
| Inspect task | `algotune_1_0` |
| Version | 1.0 |
| Samples | 154 |
| Paper | [arxiv](https://arxiv.org/abs/2507.15887) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
