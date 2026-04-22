# swtbench-verified@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/swtbench_verified_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import swtbench_verified_1_0

eval(swtbench_verified_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [swtbench-verified@1.0](https://registry.harborframework.com/datasets?q=swtbench-verified) |
| Inspect task | `swtbench_verified_1_0` |
| Version | 1.0 |
| Samples | 433 |
| Paper | [arxiv](https://arxiv.org/abs/2406.12952) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
