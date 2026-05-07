# bigcode/humanevalfix – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/bigcode_humanevalfix --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import bigcode_humanevalfix

eval(bigcode_humanevalfix(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [bigcode/humanevalfix](https://hub.harborframework.com/datasets/bigcode/humanevalfix/latest) |
| Inspect task | `bigcode_humanevalfix` |
| Latest digest | sha256:f3188245370b2ea142c6442591299c955202cfdf822371b4c6e9e5baf7dafe32 |
| Samples | 164 |
| Paper | [arxiv](https://arxiv.org/abs/2308.07124) |
| Source | <https://github.com/bigcode-project/octopack> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
