# openai/mmmlu – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/openai_mmmlu --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import openai_mmmlu

eval(openai_mmmlu(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [openai/mmmlu](https://hub.harborframework.com/datasets/openai/mmmlu/latest) |
| Inspect task | `openai_mmmlu` |
| Latest digest | sha256:5db8efae92fcb2df5fb3c76647394410badcd08cec58a3cdfd3c602f7d9b38d1 |
| Samples | 150 |
| Paper | [arxiv](https://arxiv.org/abs/2503.10497) |
| Source | <https://huggingface.co/datasets/openai/MMMLU> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
