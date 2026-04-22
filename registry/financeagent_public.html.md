# financeagent@public – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/financeagent_public --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import financeagent_public

eval(financeagent_public(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [financeagent@public](https://registry.harborframework.com/datasets/vals/financeagent/latest) |
| Inspect task | `financeagent_public` |
| Version | public |
| Samples | 50 |
| Paper | [arxiv](https://arxiv.org/abs/2508.00828) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
