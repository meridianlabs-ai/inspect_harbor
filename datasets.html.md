# Datasets – Inspect Harbor

Inspect Harbor provides one task function per dataset in the [Harbor registry](https://hub.harborframework.com/datasets). You can import and use them directly:

``` python
from inspect_harbor import (
    aider_polyglot,
    swe_bench_verified,
    terminal_bench_2,
    aime,
    gpqa_diamond,
    usaco,
    # ... and many more
)
```

For the complete list of available datasets, see the [Registry](./registry.html.md).

## Pinning

Each generated task accepts a `ref` parameter that selects which Harbor revision to load. The default is `"latest"`:

``` python
from inspect_harbor import aider_polyglot

# Uses the latest revision
eval(aider_polyglot(), model="openai/gpt-5-mini")

# Pins to a specific Harbor ref (digest, revision number, or tag) for reproducibility
eval(
    aider_polyglot(
        ref="sha256:01e28d85e46beae5b7e29a29f57cb49d882b5486583d52cec4ee5bf3540a1c84",
    ),
    model="openai/gpt-5-mini",
)
```

The exact `sha256:` digest of `latest` at generation time is recorded in each task’s docstring (`Latest digest:` line) and on its details page (linked from the [Registry](./registry.html.md)).

## Known Issues

These are upstream issues we’ve encountered while integrating Harbor datasets. Each of these tasks is currently unrunnable as-is:

| Dataset | Issue | Status |
|----|----|----|
| `xlang/ds-1000` | Multiple configuration issues preventing execution (`pull access denied for ds1000`) | [harbor-datasets#103](https://github.com/laude-institute/harbor-datasets/issues/103) |

## Volume mount limitations

Some multi-service tasks declare Docker `volumes:` that inspect_harbor doesn’t yet fully translate (single-service tasks are unaffected).

- **`${HOST_*}` `/logs` binds fail on local Docker** (`mounts denied`) but work on other providers (daytona/e2b). Affected: `kumo/*` (parity/1/easy/hard), `openai/swe-lancer-diamond-*` (all/ic/manager), `grafana/o11y-bench`, `sierra-research/tau3-bench`, `yanagiorigami/frontier-cs`.
- **Task-file binds aren’t delivered** — relative/host-path file mounts (`./setup.json`, `./AGENT.md`, `${CONTEXT_DIR}/../../shared/...`) aren’t mounted into the container. Affected: `grafana/o11y-bench`, `yanagiorigami/frontier-cs`, `scale-ai/hil-bench`.
