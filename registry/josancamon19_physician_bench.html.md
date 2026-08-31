# josancamon19/physician-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/josancamon19_physician_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import josancamon19_physician_bench

eval(josancamon19_physician_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [josancamon19/physician-bench](https://hub.harborframework.com/datasets/josancamon19/physician-bench/latest) |
| Inspect task | `josancamon19_physician_bench` |
| Latest digest | sha256:665cad8a072424b2e0c02d2f0b5dbe8e9e53dcce82bb5b7ae2215553c673cf01 |
| Samples | 100 |
| Paper | [arxiv](https://arxiv.org/abs/2605.02240) |
| Source | <https://github.com/HealthRex/PhysicianBench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
