# pgcodellm/rebench-v2-test – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/pgcodellm_rebench_v2_test --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import pgcodellm_rebench_v2_test

eval(pgcodellm_rebench_v2_test(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [pgcodellm/rebench-v2-test](https://hub.harborframework.com/datasets/pgcodellm/rebench-v2-test/latest) |
| Inspect task | `pgcodellm_rebench_v2_test` |
| Latest digest | sha256:69488f0f1f51c1fed4ca5271b92b63b96deb4b0f2252d8654285a8fea173deb0 |
| Samples | 20 |
| Paper | [arxiv](https://arxiv.org/abs/2602.23866) |
| Source | <https://github.com/SWE-rebench/SWE-rebench-V2> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
