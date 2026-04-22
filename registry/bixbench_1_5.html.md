# bixbench@1.5 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/bixbench_1_5 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import bixbench_1_5

eval(bixbench_1_5(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [bixbench@1.5](https://registry.harborframework.com/datasets/futurehouse/bixbench/latest) |
| Inspect task | `bixbench_1_5` |
| Version | 1.5 |
| Samples | 205 |
| Paper | [arxiv](https://arxiv.org/abs/2503.00096) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
