# livecodebench@6.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/livecodebench_6_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import livecodebench_6_0

eval(livecodebench_6_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [livecodebench@6.0](https://registry.harborframework.com/datasets/livecodebench/livecodebench/latest) |
| Inspect task | `livecodebench_6_0` |
| Version | 6.0 |
| Samples | 100 |
| Paper | [arxiv](https://arxiv.org/abs/2403.07974) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
