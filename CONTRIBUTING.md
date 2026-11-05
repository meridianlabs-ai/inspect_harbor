# Contributing to Inspect Harbor

Thanks for your interest in contributing to Inspect Harbor — this guide covers how to set up your environment, run the checks, and get changes released.

## Development setup

Inspect Harbor requires Python 3.12+ and uses [uv](https://docs.astral.sh/uv/) 0.13.4 or later for dependency management.

Clone the repository and install development dependencies:

```bash
git clone https://github.com/meridianlabs-ai/inspect_harbor.git
cd inspect_harbor
make install  # Installs dependencies (uv sync) and sets up pre-commit hooks
```

`uv sync` creates `.venv` with the exact versions in `uv.lock` and installs Inspect Harbor editable. The dev tools are in the `dev` extra. The default `dev` dependency group includes that extra, so `uv sync` and `uv run` install them. `uv sync --extra dev` does the same, and works with `--no-default-groups` too.

### Dependencies and the cooldown

`uv.lock` pins every Python dependency except the build toolchain. CI's lint, type-check, test and build jobs, and the nightly registry update, install their dependencies from it, and fail when `uv.lock` is out of date with `pyproject.toml`. CI's build job and the release build use the build toolchain (build, hatchling, hatch-vcs) pinned with hashes in `scripts/build-dist/requirements.txt`. Dependabot updates that file weekly, and `.github/workflows/publish.yaml` gives the command to update it by hand. When uv builds the project itself, for example for the editable install in `uv sync`, it resolves the build backend, still within the cooldown. When you change dependencies in `pyproject.toml`, run `uv lock` and commit both files.

`pyproject.toml` sets `exclude-newer = "7 days"` under `[tool.uv]`, so `uv lock`, `uv sync` and `uv pip` only pick releases that have been on PyPI for at least seven days. A compromised release is usually found and removed within that time, before it reaches `uv.lock`, CI or your machine. Only a direct dependency (a package in `dependencies` or the `dev` extra in `pyproject.toml`) that is a model provider SDK or an Inspect package can wait 6 hours instead, so Inspect Harbor can adopt a new release the day it ships. Today that is only `inspect-ai`, listed with `"6 hours"` in `[tool.uv.exclude-newer-package]`. No direct dependency is a provider SDK. Every other package keeps the seven-day cooldown. Dependabot's `uv` entry in `.github/dependabot.yml` repeats the cooldown and the list. When you add a `"6 hours"` entry, also add the package to `cooldown.exclude` and the `six-hour-cooldown` group there. `tests/test_dependency_cooldown.py` checks that each entry is a direct dependency, that dated entries (below) are less than seven days old, and that the two files match. Whether a package is a provider SDK or an Inspect package is up to review.

Dependabot proposes `uv.lock` updates daily, once a release has cleared its cooldown. To adopt a release sooner, run `uv lock --upgrade-package <package>` and commit `uv.lock`. A release still inside its cooldown can't be locked; wait for it rather than overriding `exclude-newer`, unless it's an emergency (below).

In an emergency, for example a security fix, you can adopt a release that is less than seven days old with a one-time dated entry:

1. Under `[tool.uv.exclude-newer-package]` in `pyproject.toml`, add `<package> = "<timestamp>"`. The package must be a direct dependency. Use an RFC 3339 timestamp just after the upload time of the fixed release. Don't add a dated entry to `.github/dependabot.yml`.
2. Run `uv lock --upgrade-package <package>` and commit both files.
3. Within seven days, once the normal cooldown includes the release, delete the entry, run `uv lock --upgrade-package <package>`, and commit both files. A plain `uv lock` doesn't reliably remove the entry from `uv.lock`, and CI then fails. A test fails when a dated entry is seven days old or older.

The nightly `Harbor parity` workflow is the one CI job that installs the newest releases: it compares the loader against the latest `harbor` release, in a separate environment. Testing against the newest release of every other dependency happens in the nightly canary in [meridianlabs-ai/canaries](https://github.com/meridianlabs-ai/canaries), so Inspect Harbor's own CI doesn't need to.

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

The docs tools (Quarto and its Python packages) are in the `doc` dependency group, which `uv sync` leaves out. Ask for it when you build the docs:

```bash
cd docs
uv run --group doc quarto preview
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
