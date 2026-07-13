# satbench/satbench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/satbench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import satbench

eval(satbench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [satbench/satbench](https://hub.harborframework.com/datasets/satbench/satbench/latest) |
| Inspect task | `satbench` |
| Latest digest | sha256:4b921bb49ebe0513a784783eeac9561e9d216339de1e4cb20c43018dd0502a1e |
| Samples | 2100 |
| Paper | [arxiv](https://arxiv.org/abs/2505.14615) |
| Source | <https://github.com/Anjiang-Wei/SATBench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
