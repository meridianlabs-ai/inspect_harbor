# ds-1000@head – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/ds_1000_head --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import ds_1000_head

eval(ds_1000_head(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [ds-1000@head](https://registry.harborframework.com/datasets/xlang/ds-1000/latest) |
| Inspect task | `ds_1000_head` |
| Version | head |
| Samples | 1000 |
| Paper | [arxiv](https://arxiv.org/abs/2211.11501) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
