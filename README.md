# Inspect Harbor

Inspect Harbor provides an interface to run [Harbor](https://harborframework.com/) tasks using [Inspect AI](https://inspect.aisi.org.uk/).

```bash
pip install inspect-harbor
```

Then in Python:

```python
from inspect_ai import eval
from inspect_harbor import hello_world

eval(hello_world(), model="openai/gpt-5-mini")
```

For full documentation, see <https://meridianlabs-ai.github.io/inspect_harbor>. The docs site covers installation, the Harbor task model, the default agent scaffold, task parameters, the generic `harbor()` interface for custom registries and local/git tasks, and a complete catalog of available datasets.

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Development

Clone the repository and install development dependencies:

```bash
git clone https://github.com/meridianlabs-ai/inspect_harbor.git
cd inspect_harbor
make install  # Installs dependencies and sets up pre-commit hooks
```

Run tests and checks:

```bash
make check    # Run linting (ruff check + format) and type checking (pyright)
make test     # Run tests
make cov      # Run tests with coverage report
```

Clean up build artifacts:

```bash
make clean    # Remove cache and build artifacts
```

## Credits

This work is based on contributions by [@iphan](https://github.com/iphan) and [@anthonyduong9](https://github.com/anthonyduong9) from the `inspect_evals` repository:

- [@iphan](https://github.com/iphan)'s [Terminal Bench implementation](https://github.com/UKGovernmentBEIS/inspect_evals/pull/791)
- [@anthonyduong9](https://github.com/anthonyduong9)'s [Harbor task implementation](https://github.com/UKGovernmentBEIS/inspect_evals/pull/945)

ATIF test fixtures under `tests/atif/fixtures/` are copied verbatim from [harbor's golden tests](https://github.com/harbor-framework/harbor/tree/main/tests/golden) (MIT licensed).
