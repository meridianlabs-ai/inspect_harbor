# minnesotanlp/aar – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/minnesotanlp_aar --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import minnesotanlp_aar

eval(minnesotanlp_aar(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [minnesotanlp/aar](https://hub.harborframework.com/datasets/minnesotanlp/aar/latest) |
| Inspect task | `minnesotanlp_aar` |
| Latest digest | sha256:d93938542f547046aa37d7c62f8ef0e4ec690cc18860615d72ef03e142bb5403 |
| Samples | 1000 |
| Paper | [arxiv](https://arxiv.org/abs/2604.10261) |
| Source | <https://github.com/minnesotanlp/the-amazing-agent-race> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
