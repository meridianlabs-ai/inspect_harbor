# gabeorlanski/slopcodebench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/gabeorlanski_slopcodebench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import gabeorlanski_slopcodebench

eval(gabeorlanski_slopcodebench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [gabeorlanski/slopcodebench](https://hub.harborframework.com/datasets/gabeorlanski/slopcodebench/latest) |
| Inspect task | `gabeorlanski_slopcodebench` |
| Latest digest | sha256:aec29354c19d3e762640ab6d7d3c63ba8fcf4895e98a5756aecb9157b5bb4ae0 |
| Samples | 36 |
| Paper | [arxiv](https://arxiv.org/abs/2603.24755) |
| Source | <https://github.com/SprocketLab/slop-code-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
