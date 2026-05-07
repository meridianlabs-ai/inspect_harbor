# apple/mmau – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/apple_mmau --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import apple_mmau

eval(apple_mmau(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [apple/mmau](https://hub.harborframework.com/datasets/apple/mmau/latest) |
| Inspect task | `apple_mmau` |
| Latest digest | sha256:435e5f12af62d3a7537608bdc6652757c58488fcc3345e00cc0dcc0340c72417 |
| Samples | 1000 |
| Paper | [arxiv](https://arxiv.org/abs/2410.19168) |
| Source | <https://github.com/apple/axlearn/tree/main/docs/research/mmau> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
