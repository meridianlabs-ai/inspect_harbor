# swebench-verified@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/swebench_verified_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import swebench_verified_1_0

eval(swebench_verified_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [swebench-verified@1.0](https://registry.harborframework.com/datasets?q=swebench-verified) |
| Inspect task | `swebench_verified_1_0` |
| Version | 1.0 |
| Samples | 500 |
| Paper | [arxiv](https://arxiv.org/abs/2310.06770) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
