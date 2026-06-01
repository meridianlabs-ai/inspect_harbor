# lcb/longswebench-32k – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/lcb_longswebench_32k --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import lcb_longswebench_32k

eval(lcb_longswebench_32k(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [lcb/longswebench-32k](https://hub.harborframework.com/datasets/lcb/longswebench-32k/latest) |
| Inspect task | `lcb_longswebench_32k` |
| Latest digest | sha256:dde4db0e62775d1ad50bfc6590214ad4e4bd601b313fdbd1a7437c4cd5f4d8fd |
| Samples | 3 |
| Paper | [arxiv](https://arxiv.org/abs/2505.07897) |
| Source | <https://github.com/Zteefano/long-code-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
