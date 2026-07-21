# ale/rsi-post-training – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/ale_rsi_post_training --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import ale_rsi_post_training

eval(ale_rsi_post_training(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [ale/rsi-post-training](https://hub.harborframework.com/datasets/ale/rsi-post-training/latest) |
| Inspect task | `ale_rsi_post_training` |
| Latest digest | sha256:8f9485dd374141adf8bf8f6475eb6d107a59351ce585674586fb3175222bce4c |
| Samples | 6 |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
