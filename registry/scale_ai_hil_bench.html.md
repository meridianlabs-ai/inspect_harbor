# scale-ai/hil-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/scale_ai_hil_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import scale_ai_hil_bench

eval(scale_ai_hil_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [scale-ai/hil-bench](https://hub.harborframework.com/datasets/scale-ai/hil-bench/latest) |
| Inspect task | `scale_ai_hil_bench` |
| Latest digest | sha256:119b6d1a394e6efdec8a729ea4324c21f75e2c8f5d1f9e6218c11cd48e6ae740 |
| Samples | 600 |
| Paper | [arxiv](https://arxiv.org/abs/2604.09408) |
| Source | <https://github.com/hilbenchauthors/hil-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
