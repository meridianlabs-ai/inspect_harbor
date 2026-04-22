# medagentbench@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/medagentbench_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import medagentbench_1_0

eval(medagentbench_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [medagentbench@1.0](https://registry.harborframework.com/datasets/stanford/medagentbench/latest) |
| Inspect task | `medagentbench_1_0` |
| Version | 1.0 |
| Samples | 300 |
| Paper | [arxiv](https://arxiv.org/abs/2501.14654) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
