# biopharma-bench/biopharma-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/biopharma_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import biopharma_bench

eval(biopharma_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [biopharma-bench/biopharma-bench](https://hub.harborframework.com/datasets/biopharma-bench/biopharma-bench/latest) |
| Inspect task | `biopharma_bench` |
| Latest digest | sha256:8975dab9154ee4fdc053650f6ae498ade4e80fcd1f669c4ab2d048bb990faf7c |
| Samples | 10 |
| Source | <https://huggingface.co/datasets/raycasterai/biopharma-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
