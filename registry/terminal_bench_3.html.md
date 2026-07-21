# terminal-bench/terminal-bench-3 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/terminal_bench_3 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import terminal_bench_3

eval(terminal_bench_3(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [terminal-bench/terminal-bench-3](https://hub.harborframework.com/datasets/terminal-bench/terminal-bench-3/latest) |
| Inspect task | `terminal_bench_3` |
| Latest digest | sha256:88433fbcecd1a3f81f7a71bff4cc76c394d0edbefb7e028f90d4109b639fefba |
| Samples | 75 |
| Paper | [arxiv](https://arxiv.org/abs/2601.11868) |
| Source | <https://github.com/harbor-framework/terminal-bench-3> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
