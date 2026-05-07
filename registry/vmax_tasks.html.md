# vmax/vmax-tasks – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/vmax_tasks --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import vmax_tasks

eval(vmax_tasks(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [vmax/vmax-tasks](https://hub.harborframework.com/datasets/vmax/vmax-tasks/latest) |
| Inspect task | `vmax_tasks` |
| Latest digest | sha256:b5978ffe255299f8d5729499e7ebd81d3a173cb013d35a901a98c808eab3b3b3 |
| Samples | 1000 |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
