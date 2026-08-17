# hwe-bench/hwe-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/hwe_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import hwe_bench

eval(hwe_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [hwe-bench/hwe-bench](https://hub.harborframework.com/datasets/hwe-bench/hwe-bench/latest) |
| Inspect task | `hwe_bench` |
| Latest digest | sha256:c65139ef5b04e1951e0896b42c10ea24e8aa2a7fd28ab76c12b3944b9bea9abc |
| Samples | 77 |
| Source | <https://github.com/svd-ai-lab/hwe-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
