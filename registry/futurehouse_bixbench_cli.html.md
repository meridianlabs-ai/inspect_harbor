# futurehouse/bixbench-cli – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/futurehouse_bixbench_cli --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import futurehouse_bixbench_cli

eval(futurehouse_bixbench_cli(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [futurehouse/bixbench-cli](https://hub.harborframework.com/datasets/futurehouse/bixbench-cli/latest) |
| Inspect task | `futurehouse_bixbench_cli` |
| Latest digest | sha256:a856307be0c75e7403e9113e65c986d897dead9dbe416f588cfc60a15f1b14c2 |
| Samples | 205 |
| Paper | [arxiv](https://arxiv.org/abs/2503.00096) |
| Source | <https://github.com/Future-House/BixBench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
