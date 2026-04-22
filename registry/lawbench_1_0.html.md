# lawbench@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/lawbench_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import lawbench_1_0

eval(lawbench_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [lawbench@1.0](https://registry.harborframework.com/datasets/lawbench/lawbench/latest) |
| Inspect task | `lawbench_1_0` |
| Version | 1.0 |
| Samples | 1000 |
| Paper | [arxiv](https://arxiv.org/abs/2309.16289) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
