# futurehouse/labbench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/futurehouse_labbench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import futurehouse_labbench

eval(futurehouse_labbench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [futurehouse/labbench](https://hub.harborframework.com/datasets/futurehouse/labbench/latest) |
| Inspect task | `futurehouse_labbench` |
| Latest digest | sha256:0d3d53621c4b583f515cc0b301b030c3835f2c980ca5b58dbdcb1ba42b53e9b7 |
| Samples | 181 |
| Paper | [arxiv](https://arxiv.org/abs/2407.10362) |
| Source | <https://github.com/Future-House/LAB-Bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
