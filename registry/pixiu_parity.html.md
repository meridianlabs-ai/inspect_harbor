# pixiu@parity – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/pixiu_parity --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import pixiu_parity

eval(pixiu_parity(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [pixiu@parity](https://registry.harborframework.com/datasets?q=pixiu) |
| Inspect task | `pixiu_parity` |
| Version | parity |
| Samples | 435 |
| Paper | [arxiv](https://arxiv.org/abs/2306.05443) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
