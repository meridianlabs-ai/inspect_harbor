# sureshraghu/smdd-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/sureshraghu_smdd_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import sureshraghu_smdd_bench

eval(sureshraghu_smdd_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [sureshraghu/smdd-bench](https://hub.harborframework.com/datasets/sureshraghu/smdd-bench/latest) |
| Inspect task | `sureshraghu_smdd_bench` |
| Latest digest | sha256:624b36d0ee1b389fe82f1150bea7db09958b2b314663fae839baae1b5f3ac081 |
| Samples | 502 |
| Paper | [arxiv](https://arxiv.org/abs/2605.21740) |
| Source | <https://github.com/t7rs/SMDD-Bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
