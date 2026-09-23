# AGENTS.md

## Pull Requests

- Title PRs as Conventional Commits (`<type>: <description>`)—we squash-merge, so the PR title becomes the commit message that drives releases; `pr-title-lint` enforces it
- `feat:`/`fix:` are for user-facing changes only: they headline the release notes and bump the version. `perf:`/`revert:` also appear in the notes (no bump); `docs:`, `refactor:`, `chore:`, `build:`, `ci:`, `test:`, `style:` are hidden
- Body lines starting with `<type>:` are parsed as extra changelog entries—don't begin description lines with a conventional-commit prefix unless that's intended
- Never edit `CHANGELOG.md`, version numbers, or `.release-please-manifest.json`—Release Please owns them
- See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines

## Harbor adapter (`src/inspect_harbor/_harbor/`)

inspect_harbor does not depend on the `harbor` package. It reads Harbor's task format itself and runs tasks on Inspect. Keep the two authorities apart:

- **Harbor is the spec for the task format**: `task.toml` (`models.py`), task directories (`task_dir.py`, `paths.py`), dataset filters (`local.py`), `reward.txt`/`reward.json` semantics (`scorer.py`), and the hub and registry protocols (`hub.py`, `registry.py`). When Harbor's behaviour here differs from ours, honour Harbor unless the design notes in the module docstring say otherwise—check the Harbor source at the release we track (`SUPPORTED_SCHEMA_VERSION` in `models.py` names the task.toml schema; the parity test docstring names the Harbor version)
- **Inspect is the runtime**: use `sandbox().exec/read_file/write_file`, `Sample` metadata, Python `logging` (Inspect surfaces it in the console and eval logs), and `run_coroutine` for async work at task-construction time. Do not copy Harbor's execution mechanics (login shells, output files, root user switches) when Inspect has a native equivalent
- **Never assume the Docker sandbox.** Tasks must run on any Inspect sandbox provider. `exec(user=...)` costs `sudo` or `su` in the image on remote providers, so only switch user when the task requires it. Test changes to the scorer or converter on Docker plus at least one remote provider (`inspect_sandboxes`, `-T sandbox_env_name=modal|daytona`, `--model mockllm/model`, and `--solver inspect_harbor/oracle` to prove a 1.0 score)
- **Do not add `harbor` (or anything that pulls in LiteLLM) as a dependency.** That is the constraint this adapter exists to remove (#166)
- **Parity is tested, not assumed.** `tests/manual/test_harbor_parity.py` loads every cached hub task with both our loader and the real `harbor` package; its docstring has the venv recipe. Run it after touching `models.py` or `task_dir.py`. Unknown `task.toml` keys are logged as warnings on purpose: they are the drift signal
- **Module layout**: classes first, then public functions, then private helpers; Google docstrings; lenient models (`extra="allow"`) with strict types on the fields we read
- **Tests**: few and meaningful, parametrised where cases are siblings, real fixtures (a git repo, `httpx.MockTransport`, tar archives) over mocks of our own functions
- **Environment variables**: `INSPECT_HARBOR_CACHE_DIR` (task cache root), `INSPECT_HARBOR_NO_TELEMETRY=1` (skip hub download counters; set it in stress tests), `HARBOR_SUPABASE_URL` / `HARBOR_SUPABASE_PUBLISHABLE_KEY` (hub backend, same names as Harbor)
