# scale-ai/swe-bench-pro – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/scale_ai_swe_bench_pro --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import scale_ai_swe_bench_pro

eval(scale_ai_swe_bench_pro(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [scale-ai/swe-bench-pro](https://hub.harborframework.com/datasets/scale-ai/swe-bench-pro/latest) |
| Inspect task | `scale_ai_swe_bench_pro` |
| Latest digest | sha256:88411d32ff27e53a4c1a7e29f0c2aeba180c8e5d60f221cab5ed56325f33549d |
| Samples | 731 |
| Paper | [arxiv](https://arxiv.org/abs/2509.16941) |
| Source | <https://github.com/scaleapi/SWE-bench_Pro-os> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
