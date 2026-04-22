# dabstep@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/dabstep_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import dabstep_1_0

eval(dabstep_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [dabstep@1.0](https://registry.harborframework.com/datasets/adyen/dabstep/latest) |
| Inspect task | `dabstep_1_0` |
| Version | 1.0 |
| Samples | 450 |
| Paper | [arxiv](https://arxiv.org/abs/2506.23719) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
