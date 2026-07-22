# rsi-index/post-training – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/rsi_index_post_training --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import rsi_index_post_training

eval(rsi_index_post_training(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [rsi-index/post-training](https://hub.harborframework.com/datasets/rsi-index/post-training/latest) |
| Inspect task | `rsi_index_post_training` |
| Latest digest | sha256:46e29b6a00e487dbf4ab88c40c1a525941df5f3d7ce6956b42c35d5432031bfb |
| Samples | 1 |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
