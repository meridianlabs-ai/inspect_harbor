# bird-bench@parity – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/bird_bench_parity --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import bird_bench_parity

eval(bird_bench_parity(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [bird-bench@parity](https://registry.harborframework.com/datasets?q=bird-bench) |
| Inspect task | `bird_bench_parity` |
| Version | parity |
| Samples | 150 |
| Paper | [arxiv](https://arxiv.org/abs/2305.03111) |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
