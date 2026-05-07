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
| Latest digest | sha256:79c6ffe0a2ac7e1a71ec0d0f50799ae235b14efdd65019f059023485db23122e |
| Samples | 36 |
| Paper | [arxiv](https://arxiv.org/abs/2603.24755) |
| Source | <https://github.com/SprocketLab/slop-code-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
