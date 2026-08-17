# nl2repobench/nl2repobench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/nl2repobench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import nl2repobench

eval(nl2repobench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [nl2repobench/nl2repobench](https://hub.harborframework.com/datasets/nl2repobench/nl2repobench/latest) |
| Inspect task | `nl2repobench` |
| Latest digest | sha256:b0d58e327ee30a6e6584bd4843a53db52a3442e230630369da095ec564542712 |
| Samples | 104 |
| Paper | [arxiv](https://arxiv.org/abs/2512.12730) |
| Source | <https://github.com/multimodal-art-projection/NL2RepoBench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
