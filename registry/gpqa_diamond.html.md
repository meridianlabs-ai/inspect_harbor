# gpqa-diamond/gpqa-diamond – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/gpqa_diamond --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import gpqa_diamond

eval(gpqa_diamond(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [gpqa-diamond/gpqa-diamond](https://hub.harborframework.com/datasets/gpqa-diamond/gpqa-diamond/latest) |
| Inspect task | `gpqa_diamond` |
| Latest digest | sha256:87d299c2cd19daac11ff3e8f3dfb61f614cad21a8f93f22e188f4b11282dfcf1 |
| Samples | 198 |
| Paper | [arxiv](https://arxiv.org/abs/2311.12022) |
| Source | <https://github.com/idavidrein/gpqa> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
