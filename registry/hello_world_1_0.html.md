# hello-world@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/hello_world_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import hello_world_1_0

eval(hello_world_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [hello-world@1.0](https://registry.harborframework.com/datasets/harbor/hello-world/latest) |
| Inspect task | `hello_world_1_0` |
| Version | 1.0 |
| Samples | 1 |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
