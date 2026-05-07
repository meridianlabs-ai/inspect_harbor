# binary-audit/binary-audit – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/binary_audit --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import binary_audit

eval(binary_audit(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [binary-audit/binary-audit](https://hub.harborframework.com/datasets/binary-audit/binary-audit/latest) |
| Inspect task | `binary_audit` |
| Latest digest | sha256:b1ad968bbe8ad16a5c4463814d169cfbda30d08c179b9a5401e5db63953f6bc2 |
| Samples | 46 |
| Source | <https://github.com/QuesmaOrg/BinaryAudit> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
