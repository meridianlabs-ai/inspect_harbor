# webgen-bench/webgen-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/webgen_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import webgen_bench

eval(webgen_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [webgen-bench/webgen-bench](https://hub.harborframework.com/datasets/webgen-bench/webgen-bench/latest) |
| Inspect task | `webgen_bench` |
| Latest digest | sha256:e593e93b325f9942ccae818c2a5d4adedbd837ac2aad96c6c3e3fe623be29374 |
| Samples | 101 |
| Paper | [arxiv](https://arxiv.org/abs/2505.03733) |
| Source | <https://github.com/mnluzimu/WebGen-Bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
