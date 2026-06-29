# orca-bench/ORCA-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/orca_bench_orca_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import orca_bench_orca_bench

eval(orca_bench_orca_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [orca-bench/ORCA-bench](https://hub.harborframework.com/datasets/orca-bench/ORCA-bench/latest) |
| Inspect task | `orca_bench_orca_bench` |
| Latest digest | sha256:fcd966f953a9fffd5b852767eee86ece9673d4e66b68aa9081700ba502c2adc6 |
| Samples | 1000 |
| Source | <https://orca-bench.github.io> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
