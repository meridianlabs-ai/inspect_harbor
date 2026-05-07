# tencent/autocodebench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/tencent_autocodebench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import tencent_autocodebench

eval(tencent_autocodebench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [tencent/autocodebench](https://hub.harborframework.com/datasets/tencent/autocodebench/latest) |
| Inspect task | `tencent_autocodebench` |
| Latest digest | sha256:da30a5e97eeccc2d024a2ff947fb99966ea88bed5b7077ee451d2ae72e645caf |
| Samples | 200 |
| Paper | [arxiv](https://arxiv.org/abs/2508.09101) |
| Source | <https://github.com/Tencent-Hunyuan/AutoCodeBenchmark> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
