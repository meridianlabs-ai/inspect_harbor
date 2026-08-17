# android-bench/android-bench – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/android_bench --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import android_bench

eval(android_bench(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [android-bench/android-bench](https://hub.harborframework.com/datasets/android-bench/android-bench/latest) |
| Inspect task | `android_bench` |
| Latest digest | sha256:e9c64ac5470aa2323be3f8391a831c4cb7392317d2e921c08422b46851067dd5 |
| Samples | 100 |
| Source | <https://github.com/android-bench/android-bench> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
