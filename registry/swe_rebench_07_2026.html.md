# ibragim-badertdinov/swe-rebench-07-2026 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/swe_rebench_07_2026 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import swe_rebench_07_2026

eval(swe_rebench_07_2026(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [ibragim-badertdinov/swe-rebench-07-2026](https://hub.harborframework.com/datasets/ibragim-badertdinov/swe-rebench-07-2026/latest) |
| Inspect task | `swe_rebench_07_2026` |
| Latest digest | sha256:e2e357045bf03e4900d2506c36562f6eaff7acd37f63780600967ea3aecdcd79 |
| Samples | 111 |
| Paper | [arxiv](https://arxiv.org/abs/2505.20411) |
| Source | <https://huggingface.co/datasets/nebius/SWE-rebench-leaderboard> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
