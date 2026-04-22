# quixbugs@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/quixbugs_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import quixbugs_1_0

eval(quixbugs_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [quixbugs@1.0](https://registry.harborframework.com/datasets/quixbugs/quixbugs/latest) |
| Inspect task | `quixbugs_1_0` |
| Version | 1.0 |
| Samples | 80 |
| Source | <https://github.com/jkoppel/QuixBugs> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
