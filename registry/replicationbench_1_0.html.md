# replicationbench@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/replicationbench_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import replicationbench_1_0

eval(replicationbench_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [replicationbench@1.0](https://registry.harborframework.com/datasets/replicationbench/replicationbench/latest) |
| Inspect task | `replicationbench_1_0` |
| Version | 1.0 |
| Samples | 90 |
| Paper | [arxiv](https://arxiv.org/abs/2510.24591) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
