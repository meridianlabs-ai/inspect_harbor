# itmo-autods/scientific-cases – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/itmo_autods_scientific_cases --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import itmo_autods_scientific_cases

eval(itmo_autods_scientific_cases(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [itmo-autods/scientific-cases](https://hub.harborframework.com/datasets/itmo-autods/scientific-cases/latest) |
| Inspect task | `itmo_autods_scientific_cases` |
| Latest digest | sha256:9b46bced2f653dcfbbf07b2ab5e4d97be5e1221c70cd12bbb480cd80d20da715 |
| Samples | 3 |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
