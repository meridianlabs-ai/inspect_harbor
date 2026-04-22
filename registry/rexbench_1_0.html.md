# rexbench@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/rexbench_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import rexbench_1_0

eval(rexbench_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [rexbench@1.0](https://registry.harborframework.com/datasets?q=rexbench) |
| Inspect task | `rexbench_1_0` |
| Version | 1.0 |
| Samples | 2 |
| Paper | [arxiv](https://arxiv.org/abs/2506.22598) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
