# terminal-bench/terminal-bench-2-1 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/terminal_bench_2_1 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import terminal_bench_2_1

eval(terminal_bench_2_1(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [terminal-bench/terminal-bench-2-1](https://hub.harborframework.com/datasets/terminal-bench/terminal-bench-2-1/latest) |
| Inspect task | `terminal_bench_2_1` |
| Latest digest | sha256:7d7bdc1cbedad549fc1140404bd4dc45e5fd0ea7c4186773687d177ad3a0699a |
| Samples | 89 |
| Paper | [arxiv](https://arxiv.org/abs/2601.11868) |
| Source | <https://github.com/laude-institute/terminal-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
