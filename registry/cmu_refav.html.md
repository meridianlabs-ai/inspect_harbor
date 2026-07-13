# cmu/refav – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/cmu_refav --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import cmu_refav

eval(cmu_refav(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [cmu/refav](https://hub.harborframework.com/datasets/cmu/refav/latest) |
| Inspect task | `cmu_refav` |
| Latest digest | sha256:57c93f1c2f6bda2b015cec8286380cbd33860c6d1d9407f1d17dd656c0b926e0 |
| Samples | 1500 |
| Paper | [arxiv](https://arxiv.org/abs/2505.20981) |
| Source | <https://github.com/CainanD/RefAV> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
