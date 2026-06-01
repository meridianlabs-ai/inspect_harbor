# harbor/rewardhackbench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/harbor_rewardhackbench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import harbor_rewardhackbench

eval(harbor_rewardhackbench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [harbor/rewardhackbench](https://hub.harborframework.com/datasets/harbor/rewardhackbench/latest) |
| Inspect task | `harbor_rewardhackbench` |
| Latest digest | sha256:0dd16e1029495cba180809b7ecfbae375089881b11ff11e369bfbbf3c72a2fd8 |
| Samples | 846 |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
