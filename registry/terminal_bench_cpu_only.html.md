# terminal-bench/terminal-bench-cpu-only – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/terminal_bench_cpu_only --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import terminal_bench_cpu_only

eval(terminal_bench_cpu_only(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [terminal-bench/terminal-bench-cpu-only](https://hub.harborframework.com/datasets/terminal-bench/terminal-bench-cpu-only/latest) |
| Inspect task | `terminal_bench_cpu_only` |
| Latest digest | sha256:b440941ff70a00335fa906e3b1a5407c3e72c20e975fa4d7d61b803bf80dd5b5 |
| Samples | 63 |
| Paper | [arxiv](https://arxiv.org/abs/2601.11868) |
| Source | <https://github.com/harbor-framework/terminal-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
