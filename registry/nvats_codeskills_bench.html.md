# nvats/codeskills-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/nvats_codeskills_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import nvats_codeskills_bench

eval(nvats_codeskills_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [nvats/codeskills-bench](https://hub.harborframework.com/datasets/nvats/codeskills-bench/latest) |
| Inspect task | `nvats_codeskills_bench` |
| Latest digest | sha256:eeeb856e813c7c3a27a65ca459eff6e254b081560cf9d45f53503a14db527156 |
| Samples | 23 |
| Source | <https://github.com/namanvats/codeskills-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
