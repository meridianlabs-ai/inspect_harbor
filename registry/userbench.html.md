# userbench/UserBench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/userbench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import userbench

eval(userbench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [userbench/UserBench](https://hub.harborframework.com/datasets/userbench/UserBench/latest) |
| Inspect task | `userbench` |
| Latest digest | sha256:5ae6956f943da5d0781cf835cd8025a0411160321bb048f12c77bde7aac46bda |
| Samples | 620 |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
