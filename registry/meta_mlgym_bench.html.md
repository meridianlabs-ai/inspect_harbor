# meta/mlgym-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/meta_mlgym_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import meta_mlgym_bench

eval(meta_mlgym_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [meta/mlgym-bench](https://hub.harborframework.com/datasets/meta/mlgym-bench/latest) |
| Inspect task | `meta_mlgym_bench` |
| Latest digest | sha256:4637b4f2a71602911c17071a66a039dac70a8b8ce2c582b0e114c9d3adf4b412 |
| Samples | 12 |
| Paper | [arxiv](https://arxiv.org/abs/2502.14499) |
| Source | <https://github.com/facebookresearch/MLGym> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
