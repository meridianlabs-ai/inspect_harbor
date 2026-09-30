# klinikebench/klinikebench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/klinikebench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import klinikebench

eval(klinikebench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [klinikebench/klinikebench](https://hub.harborframework.com/datasets/klinikebench/klinikebench/latest) |
| Inspect task | `klinikebench` |
| Latest digest | sha256:202c363c2a6ecd1863fa43a52a0753a38e0fa7303c81e9b1ff891f9bb2087b23 |
| Samples | 333 |
| Source | <https://github.com/Zehui127/klinikebench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
