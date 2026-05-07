# bigcode/bigcodebench-hard-complete – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/bigcode_bigcodebench_hard_complete --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import bigcode_bigcodebench_hard_complete

eval(bigcode_bigcodebench_hard_complete(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [bigcode/bigcodebench-hard-complete](https://hub.harborframework.com/datasets/bigcode/bigcodebench-hard-complete/latest) |
| Inspect task | `bigcode_bigcodebench_hard_complete` |
| Latest digest | sha256:4c881f46251c98f6af182ec8eedbacc2c144db0761fcbbd789a60d7e69c30f69 |
| Samples | 145 |
| Paper | [arxiv](https://arxiv.org/abs/2406.15877) |
| Source | <https://github.com/bigcode-project/bigcodebench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
