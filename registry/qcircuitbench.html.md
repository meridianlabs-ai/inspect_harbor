# qcircuitbench/qcircuitbench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/qcircuitbench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import qcircuitbench

eval(qcircuitbench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [qcircuitbench/qcircuitbench](https://hub.harborframework.com/datasets/qcircuitbench/qcircuitbench/latest) |
| Inspect task | `qcircuitbench` |
| Latest digest | sha256:c9b9e8bb0b6d9c7701f5fd4bed4ea210a8c4b416e960ddbcfce510584ca6047b |
| Samples | 28 |
| Paper | [arxiv](https://arxiv.org/abs/2410.07961) |
| Source | <https://github.com/EstelYang/QCircuitBench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
