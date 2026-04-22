# kumo@easy – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/kumo_easy --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import kumo_easy

eval(kumo_easy(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [kumo@easy](https://registry.harborframework.com/datasets?q=kumo) |
| Inspect task | `kumo_easy` |
| Version | easy |
| Samples | 5050 |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
