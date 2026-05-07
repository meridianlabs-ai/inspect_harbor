# cais/swebenchpro – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/cais_swebenchpro --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import cais_swebenchpro

eval(cais_swebenchpro(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [cais/swebenchpro](https://hub.harborframework.com/datasets/cais/swebenchpro/latest) |
| Inspect task | `cais_swebenchpro` |
| Latest digest | sha256:0684038ce8eae92d435a27307d1c5843e291152898f429af130062e8df110768 |
| Samples | 731 |
| Paper | [arxiv](https://arxiv.org/abs/2509.16941) |
| Source | <https://github.com/scaleapi/SWE-bench_Pro-os> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
