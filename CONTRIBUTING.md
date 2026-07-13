# Contributing to Inspect Harbor

Thanks for your interest in contributing to Inspect Harbor — this guide covers how to set up your environment, run the checks, and get changes released.

## Development setup

Inspect Harbor requires Python 3.12+ and uses [uv](https://docs.astral.sh/uv/) for dependency management.

Clone the repository and install development dependencies:

```bash
git clone https://github.com/meridianlabs-ai/inspect_harbor.git
cd inspect_harbor
make install  # Installs dependencies (uv sync) and sets up pre-commit hooks
```

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

## Commit messages and releases

We use [Conventional Commits](https://www.conventionalcommits.org/). Because we
squash-merge, **the PR title becomes the commit message** — so the title is what
matters. Format it as `<type>: <description>`.

Releases are automated with [Release Please](https://github.com/googleapis/release-please):
**don't edit `CHANGELOG.md` or bump the version by hand.** Release Please reads the
merged commit types, opens a release PR that updates the changelog and version, and
merging that PR tags and publishes the release.

Choose the type deliberately — only `feat:` and `fix:` appear in the release notes
and drive the version bump:

| Type | Use for |
| --- | --- |
| `feat:` | a user-facing feature |
| `fix:` | a user-facing bug fix |
| `docs:`, `refactor:`, `perf:`, `test:`, `build:`, `chore:`, `ci:` | everything else — excluded from the release notes |

Anything that isn't a user-facing feature or fix should avoid `feat:`/`fix:` so it
stays out of the release notes.

## Reporting issues

Found a bug or have a feature request? Please open an issue on the
[GitHub issue tracker](https://github.com/meridianlabs-ai/inspect_harbor/issues).
