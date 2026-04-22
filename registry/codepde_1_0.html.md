# codepde@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/codepde_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import codepde_1_0

eval(codepde_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [codepde@1.0](https://registry.harborframework.com/datasets/codepde/codepde/latest) |
| Inspect task | `codepde_1_0` |
| Version | 1.0 |
| Samples | 5 |
| Paper | [arxiv](https://arxiv.org/abs/2505.08783) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
