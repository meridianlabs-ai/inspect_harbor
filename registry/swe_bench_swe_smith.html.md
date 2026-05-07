# swe-bench/swe-smith – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/swe_bench_swe_smith --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import swe_bench_swe_smith

eval(swe_bench_swe_smith(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [swe-bench/swe-smith](https://hub.harborframework.com/datasets/swe-bench/swe-smith/latest) |
| Inspect task | `swe_bench_swe_smith` |
| Latest digest | sha256:e1ffe3cc3517754681749eda196485f51b38b4552340a48b12f4b6953b06aa86 |
| Samples | 100 |
| Paper | [arxiv](https://arxiv.org/abs/2504.21798) |
| Source | <https://github.com/SWE-bench/SWE-smith> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
