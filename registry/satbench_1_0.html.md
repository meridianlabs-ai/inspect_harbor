# satbench@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/satbench_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import satbench_1_0

eval(satbench_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [satbench@1.0](https://registry.harborframework.com/datasets/satbench/satbench/latest) |
| Inspect task | `satbench_1_0` |
| Version | 1.0 |
| Samples | 2100 |
| Paper | [arxiv](https://arxiv.org/abs/2505.14615) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
