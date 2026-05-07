# quesma/compilebench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/quesma_compilebench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import quesma_compilebench

eval(quesma_compilebench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [quesma/compilebench](https://hub.harborframework.com/datasets/quesma/compilebench/latest) |
| Inspect task | `quesma_compilebench` |
| Latest digest | sha256:8b7ea3e0618b0f3fb2db1b5695628cfc2b2d5f405c5624b3b44d1602beca338a |
| Samples | 15 |
| Paper | [arxiv](https://arxiv.org/abs/2509.25248) |
| Source | <https://github.com/QuesmaOrg/CompileBench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
