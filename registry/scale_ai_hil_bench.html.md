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
| Latest digest | sha256:a308c71edf51736003412b8353cfb25f0cdfd58065535e18e2e8937fe6f7ac42 |
| Samples | 600 |
| Paper | [arxiv](https://arxiv.org/abs/2604.09408) |
| Source | <https://github.com/hilbenchauthors/hil-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
