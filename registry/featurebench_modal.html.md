# featurebench/featurebench-modal – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/featurebench_modal --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import featurebench_modal

eval(featurebench_modal(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [featurebench/featurebench-modal](https://hub.harborframework.com/datasets/featurebench/featurebench-modal/latest) |
| Inspect task | `featurebench_modal` |
| Latest digest | sha256:a73b18b72e135c18de4477805e55fa3e87708f020bd5c875b64f86965f174e41 |
| Samples | 200 |
| Paper | [arxiv](https://arxiv.org/abs/2602.10975) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
