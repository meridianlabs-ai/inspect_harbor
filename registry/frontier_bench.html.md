# frontier-bench/frontier-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/frontier_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import frontier_bench

eval(frontier_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [frontier-bench/frontier-bench](https://hub.harborframework.com/datasets/frontier-bench/frontier-bench/latest) |
| Inspect task | `frontier_bench` |
| Latest digest | sha256:63f363a191f0a0429fd1c5b318080616bab839473ce27e39f44868d327b03a89 |
| Samples | 74 |
| Source | <https://github.com/harbor-framework/frontier-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
