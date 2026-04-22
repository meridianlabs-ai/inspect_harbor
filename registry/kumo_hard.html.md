# kumo@hard – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/kumo_hard --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import kumo_hard

eval(kumo_hard(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [kumo@hard](https://registry.harborframework.com/datasets?q=kumo) |
| Inspect task | `kumo_hard` |
| Version | hard |
| Samples | 250 |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
