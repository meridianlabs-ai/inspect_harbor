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
| Latest digest | sha256:862b01dc3c8d3bf5b8016ea68181c3963d62588ab03b928e5c6646cfce4e7b3f |
| Samples | 20 |
| Paper | [arxiv](https://arxiv.org/abs/2606.07682) |
| Source | <https://github.com/abundant-ai/swe-marathon> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
