# cooperbench@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/cooperbench_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import cooperbench_1_0

eval(cooperbench_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [cooperbench@1.0](https://registry.harborframework.com/datasets?q=cooperbench) |
| Inspect task | `cooperbench_1_0` |
| Version | 1.0 |
| Samples | 652 |
| Paper | [arxiv](https://arxiv.org/abs/2601.13295) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
