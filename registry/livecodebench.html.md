# livecodebench/livecodebench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/livecodebench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import livecodebench

eval(livecodebench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [livecodebench/livecodebench](https://hub.harborframework.com/datasets/livecodebench/livecodebench/latest) |
| Inspect task | `livecodebench` |
| Latest digest | sha256:4dbb3336efa78b7c4d98061d4bdb57af31a2cd52a938b44463e8351ad73b160b |
| Samples | 100 |
| Paper | [arxiv](https://arxiv.org/abs/2403.07974) |
| Source | <https://github.com/LiveCodeBench/LiveCodeBench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
