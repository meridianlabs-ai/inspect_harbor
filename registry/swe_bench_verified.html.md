# swe-bench/swe-bench-verified – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/swe_bench_verified --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import swe_bench_verified

eval(swe_bench_verified(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [swe-bench/swe-bench-verified](https://hub.harborframework.com/datasets/swe-bench/swe-bench-verified/latest) |
| Inspect task | `swe_bench_verified` |
| Latest digest | sha256:235d6032d549851a936db3b5fe08807c4d385c12ee10e7be9c9786a1ff60563c |
| Samples | 500 |
| Paper | [arxiv](https://arxiv.org/abs/2310.06770) |
| Source | <https://github.com/SWE-bench/SWE-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
