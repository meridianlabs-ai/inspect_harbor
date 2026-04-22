# mmmlu@parity – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/mmmlu_parity --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import mmmlu_parity

eval(mmmlu_parity(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [mmmlu@parity](https://registry.harborframework.com/datasets/openai/mmmlu/latest) |
| Inspect task | `mmmlu_parity` |
| Version | parity |
| Samples | 150 |
| Paper | [arxiv](https://arxiv.org/abs/2503.10497) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
