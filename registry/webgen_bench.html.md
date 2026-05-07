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
| Latest digest | sha256:d0cdb3a983e5b307d4d46c789bf8a4f926939aa3c4f66ea187e22965cf3e834f |
| Samples | 101 |
| Paper | [arxiv](https://arxiv.org/abs/2505.03733) |
| Source | <https://github.com/mnluzimu/WebGen-Bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
