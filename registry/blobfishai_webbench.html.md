# blobfishai/webbench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/blobfishai_webbench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import blobfishai_webbench

eval(blobfishai_webbench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [blobfishai/webbench](https://hub.harborframework.com/datasets/blobfishai/webbench/latest) |
| Inspect task | `blobfishai_webbench` |
| Latest digest | sha256:e53cfd4c88bb9cb95281f009eed56b948b9399e0592418d8dde416765ec16e71 |
| Samples | 159 |
| Source | <https://blobfish.ai/benchmarks/webbench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
