# featurebench@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/featurebench_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import featurebench_1_0

eval(featurebench_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [featurebench@1.0](https://registry.harborframework.com/datasets/featurebench/featurebench/latest) |
| Inspect task | `featurebench_1_0` |
| Version | 1.0 |
| Samples | 200 |
| Paper | [arxiv](https://arxiv.org/abs/2602.10975) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
