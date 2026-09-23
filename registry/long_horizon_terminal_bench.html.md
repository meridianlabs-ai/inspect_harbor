# long-horizon-terminal-bench/lhtb – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/long_horizon_terminal_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import long_horizon_terminal_bench

eval(long_horizon_terminal_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [long-horizon-terminal-bench/lhtb](https://hub.harborframework.com/datasets/long-horizon-terminal-bench/lhtb/latest) |
| Inspect task | `long_horizon_terminal_bench` |
| Latest digest | sha256:5ad11c23718b34c647c756c6a565fbff234982bbb95feda4fb45e8479d8e845d |
| Samples | 46 |
| Paper | [arxiv](https://arxiv.org/abs/2607.08964) |
| Source | <https://github.com/zli12321/LHTB> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
