# futurehouse/bixbench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/futurehouse_bixbench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import futurehouse_bixbench

eval(futurehouse_bixbench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [futurehouse/bixbench](https://hub.harborframework.com/datasets/futurehouse/bixbench/latest) |
| Inspect task | `futurehouse_bixbench` |
| Latest digest | sha256:2bcaa794dfb1fac3df7b7a4be3e23a09bcec88e86443b843aab095017db2e9f3 |
| Samples | 205 |
| Paper | [arxiv](https://arxiv.org/abs/2503.00096) |
| Source | <https://github.com/Future-House/BixBench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
