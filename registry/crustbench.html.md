# crustbench/crustbench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/crustbench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import crustbench

eval(crustbench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [crustbench/crustbench](https://hub.harborframework.com/datasets/crustbench/crustbench/latest) |
| Inspect task | `crustbench` |
| Latest digest | sha256:a474b77ebbe183daf14e367e1b9d6e7aa148634a982bfb0e937944743f618243 |
| Samples | 100 |
| Paper | [arxiv](https://arxiv.org/abs/2504.15254) |
| Source | <https://github.com/anirudhkhatry/CRUST-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
