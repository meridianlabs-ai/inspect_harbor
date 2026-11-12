# Contributing to Inspect Harbor

Thanks for your interest in contributing to Inspect Harbor — this guide covers how to set up your environment, run the checks, and get changes released.

## Development setup

Inspect Harbor requires Python 3.12+ and uses [uv](https://docs.astral.sh/uv/) 0.13.4 or later for dependency management.

Clone the repository and install development dependencies:

```bash
git clone https://github.com/meridianlabs-ai/inspect_harbor.git
cd inspect_harbor
uv sync --locked
uv run --no-sync pre-commit install
```

`uv sync --locked` creates `.venv` with the exact versions in `uv.lock` and installs Inspect Harbor editable. It fails if `uv.lock` is out of date with `pyproject.toml`. `pre-commit install` sets up the pre-commit hooks. The dev tools are in the `dev` extra. The default `dev` dependency group includes that extra, so `uv sync` and `uv run` install them. `uv sync --extra dev` does the same, and works with `--no-default-groups` too.

### Dependencies

[DEPENDENCIES.md](https://github.com/meridianlabs-ai/actions/blob/main/DEPENDENCIES.md) in meridianlabs-ai/actions tells how the Inspect repositories install and change dependencies. It covers the lock file, the cooldown, Dependabot, the canaries, the release build tools, and the procedures to add or update a dependency. Follow it. It is the same for every Inspect repository, so this file does not repeat it.

For this repository:

- Inspect Harbor uses only released inspect_ai: `inspect-ai` comes from PyPI.
- The 6-hour packages are in `[tool.uv.exclude-newer-package]` in `pyproject.toml`.

## Checks and tests

```bash
make check    # Run linting (ruff check + format) and type checking (pyright)
make test     # Run tests
make cov      # Run tests with coverage report
```

Clean up cache and build artifacts:

```bash
make clean
```

## Docs

The docs tools (Quarto and its Python packages) are in the `doc` extra, which `uv sync` leaves out. Ask for it when you build the docs:

```bash
cd docs
uv run --extra doc quarto preview
```

## Commit messages and releases

We use [Conventional Commits](https://www.conventionalcommits.org/). Because we
squash-merge, **the PR title becomes the commit message** — so the title is what
matters. Format it as `<type>: <description>`.

Releases are automated with [Release Please](https://github.com/googleapis/release-please):
**don't edit `CHANGELOG.md` or bump the version by hand.** Release Please reads the
merged commit types, opens a release PR that updates the changelog and version, and
merging that PR tags the release; the publish then runs once a maintainer approves
the deployment.

Choose the type deliberately — `feat:` and `fix:` drive the version bump and
headline the release notes:

| Type | Effect |
| --- | --- |
| `feat:` | a user-facing feature — bumps the minor version |
| `fix:` | a user-facing bug fix — bumps the patch version |
| `perf:`, `revert:` | appear in the release notes (no bump on their own) |
| `docs:`, `refactor:`, `chore:`, `build:`, `ci:`, `test:`, `style:` | hidden from the release notes |

Anything that isn't a user-facing feature or fix should avoid `feat:`/`fix:` so it
stays out of the headline sections.

## Reporting issues

Found a bug or have a feature request? Please open an issue on the
[GitHub issue tracker](https://github.com/meridianlabs-ai/inspect_harbor/issues).
