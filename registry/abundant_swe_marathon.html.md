# abundant/swe-marathon – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/abundant_swe_marathon --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import abundant_swe_marathon

eval(abundant_swe_marathon(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [abundant/swe-marathon](https://hub.harborframework.com/datasets/abundant/swe-marathon/latest) |
| Inspect task | `abundant_swe_marathon` |
| Latest digest | sha256:9b351bf9bd305e6fd8bfdba9120e42551d027bf173b81ea790e8df2f21d7a624 |
| Samples | 20 |
| Paper | [arxiv](https://arxiv.org/abs/2606.07682) |
| Source | <https://github.com/abundant-ai/swe-marathon> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
