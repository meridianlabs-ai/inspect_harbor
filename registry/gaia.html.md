# gaia/gaia – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/gaia --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import gaia

eval(gaia(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [gaia/gaia](https://hub.harborframework.com/datasets/gaia/gaia/latest) |
| Inspect task | `gaia` |
| Latest digest | sha256:bbc356f476e0b70ba77da11a9be7d6345918d1e4a2daade0d6dfb82ee6f7b761 |
| Samples | 165 |
| Paper | [arxiv](https://arxiv.org/abs/2311.12983) |
| Source | <https://huggingface.co/datasets/gaia-benchmark/GAIA> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
