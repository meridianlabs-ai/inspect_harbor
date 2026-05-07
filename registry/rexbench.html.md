# rexbench/rexbench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/rexbench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import rexbench

eval(rexbench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [rexbench/rexbench](https://hub.harborframework.com/datasets/rexbench/rexbench/latest) |
| Inspect task | `rexbench` |
| Latest digest | sha256:bc23e94793e8c74aceb8f6fdb3a268dc834b4699f71b1329db9222e83bb5ac4f |
| Samples | 2 |
| Paper | [arxiv](https://arxiv.org/abs/2506.22598) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
