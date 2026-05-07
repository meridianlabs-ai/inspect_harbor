# terminal-bench/terminal-bench-2 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/terminal_bench_2 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import terminal_bench_2

eval(terminal_bench_2(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [terminal-bench/terminal-bench-2](https://hub.harborframework.com/datasets/terminal-bench/terminal-bench-2/latest) |
| Inspect task | `terminal_bench_2` |
| Latest digest | sha256:c6fc2e2382c1dbae99b2d5ecd2f4f4a60c3c01e0d84642d69b4afd92e99d078b |
| Samples | 89 |
| Paper | [arxiv](https://arxiv.org/abs/2601.11868) |
| Source | <https://github.com/laude-institute/terminal-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
