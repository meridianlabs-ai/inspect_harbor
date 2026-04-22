# swesmith@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/swesmith_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import swesmith_1_0

eval(swesmith_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [swesmith@1.0](https://registry.harborframework.com/datasets?q=swesmith) |
| Inspect task | `swesmith_1_0` |
| Version | 1.0 |
| Samples | 100 |
| Paper | [arxiv](https://arxiv.org/abs/2504.21798) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
