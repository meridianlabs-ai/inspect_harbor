# replicationbench/replicationbench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/replicationbench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import replicationbench

eval(replicationbench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [replicationbench/replicationbench](https://hub.harborframework.com/datasets/replicationbench/replicationbench/latest) |
| Inspect task | `replicationbench` |
| Latest digest | sha256:323a161d95ba985abfe8895fd6ca00bfb4233dad8a08adb6658e696bb2174f53 |
| Samples | 90 |
| Paper | [arxiv](https://arxiv.org/abs/2510.24591) |
| Source | <https://github.com/Christine8888/replicationbench-release> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
