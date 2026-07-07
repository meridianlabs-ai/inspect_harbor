# swe-rebench/swe-rebench-leaderboard – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/swe_rebench_leaderboard --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import swe_rebench_leaderboard

eval(swe_rebench_leaderboard(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [swe-rebench/swe-rebench-leaderboard](https://hub.harborframework.com/datasets/swe-rebench/swe-rebench-leaderboard/latest) |
| Inspect task | `swe_rebench_leaderboard` |
| Latest digest | sha256:ebe7444e313a0d8db94fa541139826eaebe2b0abcd4900c6f73e750494910dca |
| Samples | 860 |
| Paper | [arxiv](https://arxiv.org/abs/2505.20411) |
| Source | <https://huggingface.co/datasets/nebius/SWE-rebench-leaderboard> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
