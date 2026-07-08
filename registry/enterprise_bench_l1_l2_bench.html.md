# Enterprise-Bench/l1-l2-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/enterprise_bench_l1_l2_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import enterprise_bench_l1_l2_bench

eval(enterprise_bench_l1_l2_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [Enterprise-Bench/l1-l2-bench](https://hub.harborframework.com/datasets/Enterprise-Bench/l1-l2-bench/latest) |
| Inspect task | `enterprise_bench_l1_l2_bench` |
| Latest digest | sha256:b863bb97dc625f6d06cdc03c09751a4506ca4f6cebe41035f3ee9d0fd48f93e1 |
| Samples | 14 |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
