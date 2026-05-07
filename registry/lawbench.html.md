# lawbench/lawbench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/lawbench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import lawbench

eval(lawbench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [lawbench/lawbench](https://hub.harborframework.com/datasets/lawbench/lawbench/latest) |
| Inspect task | `lawbench` |
| Latest digest | sha256:99d2f97d515a3820a657745112aa01a8e2b2e8bf7602d78d3ef53b4bc1c64636 |
| Samples | 1000 |
| Paper | [arxiv](https://arxiv.org/abs/2309.16289) |
| Source | <https://github.com/open-compass/LawBench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
