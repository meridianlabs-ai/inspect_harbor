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
| Latest digest | sha256:73a17cda817d37ce3352d18c272c40a3f6b623061023bee365b4df74adcd11b5 |
| Samples | 36 |
| Paper | [arxiv](https://arxiv.org/abs/2603.24755) |
| Source | <https://github.com/SprocketLab/slop-code-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
