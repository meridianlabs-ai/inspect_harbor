# kgmon/deepsearchqa – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/kgmon_deepsearchqa --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import kgmon_deepsearchqa

eval(kgmon_deepsearchqa(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [kgmon/deepsearchqa](https://hub.harborframework.com/datasets/kgmon/deepsearchqa/latest) |
| Inspect task | `kgmon_deepsearchqa` |
| Latest digest | sha256:137df55552cd22440b9a1284609980d1e76920350dd1bf9f38aaa4380da57d15 |
| Samples | 900 |
| Paper | [arxiv](https://arxiv.org/abs/2601.20975) |
| Source | <https://huggingface.co/datasets/google/deepsearchqa> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
