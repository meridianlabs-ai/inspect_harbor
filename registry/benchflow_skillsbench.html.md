# benchflow/skillsbench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/benchflow_skillsbench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import benchflow_skillsbench

eval(benchflow_skillsbench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [benchflow/skillsbench](https://hub.harborframework.com/datasets/benchflow/skillsbench/latest) |
| Inspect task | `benchflow_skillsbench` |
| Latest digest | sha256:145925c10bc09425dc0201772cfa50d9b800010081cf5ad77969554a644d7ae1 |
| Samples | 87 |
| Source | <https://github.com/benchflow-ai/skillsbench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
