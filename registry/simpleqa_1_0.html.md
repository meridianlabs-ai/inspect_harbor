# simpleqa@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/simpleqa_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import simpleqa_1_0

eval(simpleqa_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [simpleqa@1.0](https://registry.harborframework.com/datasets/openai/simpleqa/latest) |
| Inspect task | `simpleqa_1_0` |
| Version | 1.0 |
| Samples | 4326 |
| Paper | [arxiv](https://arxiv.org/abs/2411.04368) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
