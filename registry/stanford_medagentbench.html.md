# stanford/medagentbench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/stanford_medagentbench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import stanford_medagentbench

eval(stanford_medagentbench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [stanford/medagentbench](https://hub.harborframework.com/datasets/stanford/medagentbench/latest) |
| Inspect task | `stanford_medagentbench` |
| Latest digest | sha256:c52d82b3462fb26417707682095e43f224a31f8f785eb7da615c1ab6adc20bf0 |
| Samples | 300 |
| Paper | [arxiv](https://arxiv.org/abs/2501.14654) |
| Source | <https://github.com/stanfordmlgroup/MedAgentBench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
