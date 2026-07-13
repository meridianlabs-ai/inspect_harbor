# harbor-index/harbor-index – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/harbor_index --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import harbor_index

eval(harbor_index(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [harbor-index/harbor-index](https://hub.harborframework.com/datasets/harbor-index/harbor-index/latest) |
| Inspect task | `harbor_index` |
| Latest digest | sha256:45f546a3b68abba79a5cbf756c7058cc4884358bd78e510f4cc7342766837acc |
| Samples | 80 |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
