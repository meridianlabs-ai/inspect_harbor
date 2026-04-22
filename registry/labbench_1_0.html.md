# labbench@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/labbench_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import labbench_1_0

eval(labbench_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [labbench@1.0](https://registry.harborframework.com/datasets/futurehouse/labbench/latest) |
| Inspect task | `labbench_1_0` |
| Version | 1.0 |
| Samples | 181 |
| Paper | [arxiv](https://arxiv.org/abs/2407.10362) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
