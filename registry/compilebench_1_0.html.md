# compilebench@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/compilebench_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import compilebench_1_0

eval(compilebench_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [compilebench@1.0](https://registry.harborframework.com/datasets/quesma/compilebench/latest) |
| Inspect task | `compilebench_1_0` |
| Version | 1.0 |
| Samples | 15 |
| Paper | [arxiv](https://arxiv.org/abs/2509.25248) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
