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
| Latest digest | sha256:74af9ee31f50d8dac213e67ebaeeddc6bb0e4470a28968f84766916e09fe13dd |
| Samples | 80 |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
