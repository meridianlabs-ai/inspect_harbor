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
| Latest digest | sha256:fdb3554453d29f96bfe87ddf36e6770f6ceadd375e8189c62718ef2f215bbbad |
| Samples | 80 |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
