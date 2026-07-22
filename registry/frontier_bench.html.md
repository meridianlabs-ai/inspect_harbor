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
| Latest digest | sha256:97fd2ba3aabdda16823a1a8ea695a3875e50e800caa60b450686deedc7171763 |
| Samples | 74 |
| Source | <https://github.com/harbor-framework/frontier-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
