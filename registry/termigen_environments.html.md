# termigen/termigen-environments – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/termigen_environments --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import termigen_environments

eval(termigen_environments(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [termigen/termigen-environments](https://hub.harborframework.com/datasets/termigen/termigen-environments/latest) |
| Inspect task | `termigen_environments` |
| Latest digest | sha256:492c3b4c051b304b3887ca4a94a3081094c177b1227f0a609123da236359d5f0 |
| Samples | 1000 |
| Paper | [arxiv](https://arxiv.org/abs/2602.07274) |
| Source | <https://github.com/ucsb-mlsec/terminal-bench-env> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
