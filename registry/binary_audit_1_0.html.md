# binary-audit@1.0 – Inspect Harbor

[← Back to Registry](../registry.html.md)

## Run this task

**CLI:**

``` bash
inspect eval inspect_harbor/binary_audit_1_0 --model openai/gpt-5
```

**Python:**

``` python
from inspect_ai import eval
from inspect_harbor import binary_audit_1_0

eval(binary_audit_1_0(), model="openai/gpt-5")
```

## Dataset information

|  |  |
|----|----|
| Harbor registry | [binary-audit@1.0](https://registry.harborframework.com/datasets/binary-audit/binary-audit/latest) |
| Inspect task | `binary_audit_1_0` |
| Version | 1.0 |
| Samples | 46 |
| Source | <https://github.com/QuesmaOrg/BinaryAudit> |

See [Task Parameters](../parameters.html.md) for the parameter set shared across all Harbor tasks.
