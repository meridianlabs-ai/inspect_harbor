# mercor/apex-agents-1-1 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/mercor_apex_agents_1_1 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import mercor_apex_agents_1_1

eval(mercor_apex_agents_1_1(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [mercor/apex-agents-1-1](https://hub.harborframework.com/datasets/mercor/apex-agents-1-1/latest) |
| Inspect task | `mercor_apex_agents_1_1` |
| Latest digest | sha256:fb4139368bf0fb2bd233745273d11d02e70229d18b611d0d854d651d539e79fa |
| Samples | 240 |
| Paper | [arxiv](https://arxiv.org/abs/2601.14242) |
| Source | <https://github.com/Mercor-Intelligence/apex_loop_truncated_tools_agent> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
