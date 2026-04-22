# mmau@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/mmau_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import mmau_1_0

eval(mmau_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [mmau@1.0](https://registry.harborframework.com/datasets/apple/mmau/latest) |
| Inspect task | `mmau_1_0` |
| Version | 1.0 |
| Samples | 1000 |
| Paper | [arxiv](https://arxiv.org/abs/2410.19168) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
