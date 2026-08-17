# terminal-bench/terminal-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/terminal_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import terminal_bench

eval(terminal_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [terminal-bench/terminal-bench](https://hub.harborframework.com/datasets/terminal-bench/terminal-bench/latest) |
| Inspect task | `terminal_bench` |
| Latest digest | sha256:a32a61879ea94eb9dc16fa1fbeb398759f0c07ca633d9d1f6aec760207036da3 |
| Samples | 74 |
| Paper | [arxiv](https://arxiv.org/abs/2601.11868) |
| Source | <https://github.com/harbor-framework/terminal-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
