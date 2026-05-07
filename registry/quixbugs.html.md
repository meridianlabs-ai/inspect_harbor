# quixbugs/quixbugs – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/quixbugs --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import quixbugs

eval(quixbugs(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [quixbugs/quixbugs](https://hub.harborframework.com/datasets/quixbugs/quixbugs/latest) |
| Inspect task | `quixbugs` |
| Latest digest | sha256:ca0bfa8d0092da50f9421e94e2c77c34be92bd2b2e50e562c6547d92edb896d1 |
| Samples | 80 |
| Source | <https://github.com/jkoppel/QuixBugs> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
