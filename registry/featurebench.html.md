# featurebench/featurebench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/featurebench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import featurebench

eval(featurebench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [featurebench/featurebench](https://hub.harborframework.com/datasets/featurebench/featurebench/latest) |
| Inspect task | `featurebench` |
| Latest digest | sha256:313ee97ae5df80c618cf2818930ca140b3700b828cc336b602b9b19dbd9a59ff |
| Samples | 200 |
| Paper | [arxiv](https://arxiv.org/abs/2602.10975) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
