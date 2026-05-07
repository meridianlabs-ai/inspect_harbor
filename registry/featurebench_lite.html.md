# featurebench/featurebench-lite – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/featurebench_lite --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import featurebench_lite

eval(featurebench_lite(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [featurebench/featurebench-lite](https://hub.harborframework.com/datasets/featurebench/featurebench-lite/latest) |
| Inspect task | `featurebench_lite` |
| Latest digest | sha256:8cc1a98d3087e46dccce1807f6032dbc12ad054aa8a742e668e31ebc05bb1b4d |
| Samples | 30 |
| Paper | [arxiv](https://arxiv.org/abs/2602.10975) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
