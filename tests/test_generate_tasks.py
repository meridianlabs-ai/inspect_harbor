"""Tests for the Harbor registry task generator script."""

import sys
from pathlib import Path

import pytest

# Add scripts directory to path to allow importing generate_tasks
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from generate_tasks import (  # noqa: E402
    Dataset,
    FetchedDataset,
    _build_table_rows,
    _clean_registry_description,
    dataset_name_to_function_name,
    decorate_datasets,
    generate_registry_pages,
    generate_tasks_content,
    resolve_categories,
)


@pytest.fixture
def mock_fetched() -> list[FetchedDataset]:
    """Mock package datasets in ``fetch_package_datasets`` emission shape.

    One row per dataset, ``org/name`` slug.
    """
    return [
        {
            "name": "dbt-labs/ade-bench",
            "description": "ADE bench description",
            "samples": 20,
            "version": "sha256:ade",
        },
        {
            "name": "harbor/hello-world",
            "description": "A friendly greeting",
            "samples": 1,
            "version": "sha256:abc123",
        },
        {
            "name": "LiteCoder/LiteCoder-rl",
            "description": "LiteCoder RL environments",
            "samples": 602,
            "version": "sha256:def456",
        },
    ]


@pytest.fixture
def mock_registry(
    mock_fetched: list[FetchedDataset],
) -> list[Dataset]:
    """Decorated registry with no overrides (auto-derived function names)."""
    return decorate_datasets(mock_fetched, {})


def test_dataset_name_to_function_name_basic() -> None:
    """Plain hyphenated names map to lowercase underscore identifiers."""
    assert dataset_name_to_function_name("terminal-bench") == "terminal_bench"
    assert dataset_name_to_function_name("hello-world") == "hello_world"


def test_dataset_name_to_function_name_with_slash() -> None:
    """``org/name`` slugs lowercase the org and join with underscore."""
    assert (
        dataset_name_to_function_name("scale-ai/swe-atlas-qna")
        == "scale_ai_swe_atlas_qna"
    )
    assert dataset_name_to_function_name("harbor/hello-world") == "harbor_hello_world"


def test_dataset_name_to_function_name_lowercases_mixed_case() -> None:
    """Mixed-case orgs are lowercased to satisfy PEP 8 / CLI ergonomics."""
    assert (
        dataset_name_to_function_name("LiteCoder/LiteCoder-rl")
        == "litecoder_litecoder_rl"
    )
    assert (
        dataset_name_to_function_name("MichaelY310/devopsgym")
        == "michaely310_devopsgym"
    )


def test_generate_tasks_emits_one_function_per_dataset(
    mock_registry: list[Dataset],
) -> None:
    """One ``@task`` per dataset, named via the auto-derived identifier."""
    content = generate_tasks_content(mock_registry)

    assert "def dbt_labs_ade_bench(" in content
    assert "def harbor_hello_world(" in content
    assert "def litecoder_litecoder_rl(" in content
    assert content.count("@task\n") == 3


def test_generate_tasks_signature_uses_ref_default_latest(
    mock_registry: list[Dataset],
) -> None:
    """Every generated task takes ``ref: str = "latest"`` as its first parameter."""
    content = generate_tasks_content(mock_registry)
    assert 'ref: str = "latest"' in content
    # The legacy ``version`` parameter is gone.
    assert "version: str" not in content


def test_generate_tasks_body_forwards_package_name_and_ref(
    mock_registry: list[Dataset],
) -> None:
    """Function body forwards ``package_name`` + ``package_ref=ref`` to ``_harbor_base``."""
    content = generate_tasks_content(mock_registry)
    assert 'package_name="harbor/hello-world"' in content
    assert "package_ref=ref" in content


def test_generate_tasks_docstring_shows_slug_and_latest_digest(
    mock_registry: list[Dataset],
) -> None:
    """Docstring carries the slug and the resolved digest for the ``latest`` ref."""
    content = generate_tasks_content(mock_registry)
    assert "Slug: harbor/hello-world" in content
    assert "Latest digest: sha256:abc123" in content


def test_generate_tasks_includes_descriptions(
    mock_registry: list[Dataset],
) -> None:
    """Per-dataset descriptions surface in their docstrings."""
    content = generate_tasks_content(mock_registry)
    assert "ADE bench description" in content
    assert "A friendly greeting" in content


def test_generate_tasks_includes_required_imports(
    mock_registry: list[Dataset],
) -> None:
    """Generated module imports Inspect's @task decorator and our harbor base."""
    content = generate_tasks_content(mock_registry)
    assert "from inspect_ai import Task, task" in content
    assert "from inspect_harbor._harbor.task import harbor as _harbor_base" in content


def test_generate_tasks_includes_all_parameters(
    mock_registry: list[Dataset],
) -> None:
    """Generated functions include every parameter the public API takes."""
    content = generate_tasks_content(mock_registry)
    assert 'ref: str = "latest"' in content
    assert "dataset_task_names: list[str] | None = None" in content
    assert "dataset_exclude_task_names: list[str] | None = None" in content
    assert "n_tasks: int | None = None" in content
    assert "overwrite_cache: bool = False" in content
    assert "sandbox_env_name: str = " in content
    assert "override_cpus: int | None = None" in content
    assert "override_memory_mb: int | None = None" in content
    assert "override_gpus: int | None = None" in content


def test_generate_tasks_passes_parameters_to_base(
    mock_registry: list[Dataset],
) -> None:
    """Every parameter is forwarded to ``_harbor_base``."""
    content = generate_tasks_content(mock_registry)
    assert "dataset_task_names=dataset_task_names" in content
    assert "dataset_exclude_task_names=dataset_exclude_task_names" in content
    assert "n_tasks=n_tasks" in content
    assert "overwrite_cache=overwrite_cache" in content
    assert "sandbox_env_name=sandbox_env_name" in content
    assert "override_cpus=override_cpus" in content
    assert "override_memory_mb=override_memory_mb" in content
    assert "override_gpus=override_gpus" in content


def test_generate_tasks_collision_check_raises() -> None:
    """If two datasets ever map to the same function name the run fails loudly."""
    fetched: list[FetchedDataset] = [
        {
            "name": "foo/bar",
            "description": "x",
            "samples": 1,
            "version": "sha256:x",
        },
    ]
    # Two distinct datasets, both forced to the same function name via override.
    overrides: dict[str, dict[str, object]] = {
        "foo/bar": {"function_name": "shared_name"},
    }
    decorated = decorate_datasets(fetched, overrides)
    decorated.append(
        Dataset(
            name="foo/baz",
            description="y",
            samples=1,
            version="sha256:y",
            func_name="shared_name",  # forced collision
            harbor_url="https://hub.harborframework.com/datasets/foo/baz/latest",
            clean_description="y.",
        )
    )
    with pytest.raises(RuntimeError, match="Function-name collision"):
        generate_tasks_content(decorated)


def test_clean_registry_description_adds_trailing_period() -> None:
    """Plain descriptions get a trailing period if they don't already have one."""
    assert _clean_registry_description("Hello world") == "Hello world."
    assert _clean_registry_description("Hello world.") == "Hello world."


def test_clean_registry_description_flattens_newlines_and_whitespace() -> None:
    """Newlines collapse to spaces; runs of whitespace shrink to one."""
    assert _clean_registry_description("Hello\nworld") == "Hello world."
    assert _clean_registry_description("Foo  bar   baz") == "Foo bar baz."


def test_clean_registry_description_strips_named_url_footers() -> None:
    """Named URL footers (``Adapter:``, ``Source:`` etc.) are stripped.

    Covers ``Original benchmark:``, ``Adapter:``, ``Source:``, ``Website:``
    and ``Adapter details:``.
    """
    assert (
        _clean_registry_description("Hello. Original benchmark: https://example.com")
        == "Hello."
    )
    assert (
        _clean_registry_description("Hello. Adapter: https://example.com/foo")
        == "Hello."
    )
    assert _clean_registry_description("Hello. Source: https://example.com") == "Hello."
    assert (
        _clean_registry_description("Hello. Website: https://example.com") == "Hello."
    )
    # ``Adapter details`` must match before the shorter ``Adapter`` alternative.
    assert (
        _clean_registry_description("Hello. Adapter details: https://example.com/x")
        == "Hello."
    )


def test_clean_registry_description_strips_inline_urls() -> None:
    """Bare URLs and URLs in parens are removed, with surrounding whitespace eaten."""
    assert _clean_registry_description("Hello (https://example.com).") == "Hello."
    assert _clean_registry_description("Hello https://example.com") == "Hello."


def test_clean_registry_description_empty() -> None:
    """Empty / whitespace-only descriptions return an empty string (no lone ``.``)."""
    assert _clean_registry_description("") == ""
    assert _clean_registry_description("   ") == ""


def test_decorate_datasets_attaches_all_derived_fields() -> None:
    """All three derived fields land on each dataset, with original keys kept.

    Verifies ``func_name``, ``harbor_url``, and ``clean_description`` are
    populated correctly.
    """
    fetched: list[FetchedDataset] = [
        {
            "name": "acme/foo-bench",
            "description": "Foo. Original benchmark: https://x.com/y",
            "samples": 5,
            "version": "sha256:abc",
        }
    ]
    decorated = decorate_datasets(fetched, {})

    assert len(decorated) == 1
    d = decorated[0]
    assert d["func_name"] == "acme_foo_bench"
    # URL is constructed deterministically from the slug.
    assert (
        d["harbor_url"]
        == "https://hub.harborframework.com/datasets/acme/foo-bench/latest"
    )
    # ``Original benchmark: …`` footer is stripped.
    assert d["clean_description"] == "Foo."
    # Original FetchedDataset fields are preserved.
    assert d["name"] == "acme/foo-bench"
    assert d["version"] == "sha256:abc"


def test_decorate_datasets_honors_function_name_override() -> None:
    """``function_name:`` in overrides shortens the auto-derived identifier."""
    fetched: list[FetchedDataset] = [
        {
            "name": "swe-bench/swe-bench-verified",
            "description": "x",
            "samples": 1,
            "version": "sha256:x",
        }
    ]
    overrides = {
        "swe-bench/swe-bench-verified": {"function_name": "swe_bench_verified"}
    }
    decorated = decorate_datasets(fetched, overrides)
    assert decorated[0]["func_name"] == "swe_bench_verified"


def test_decorate_datasets_rejects_invalid_function_name_override() -> None:
    """Non-identifier ``function_name`` overrides raise a clear error."""
    fetched: list[FetchedDataset] = [
        {
            "name": "foo/bar",
            "description": "x",
            "samples": 1,
            "version": "sha256:x",
        }
    ]
    overrides = {"foo/bar": {"function_name": "not a valid identifier!"}}
    with pytest.raises(RuntimeError, match="Invalid function_name override"):
        decorate_datasets(fetched, overrides)


def test_decorate_datasets_honors_desc_override() -> None:
    """``desc:`` in overrides replaces the Harbor description.

    The override flows through to ``description`` (used in @task docstrings)
    and ``clean_description`` (used in listing/.qmd pages).
    """
    fetched: list[FetchedDataset] = [
        {
            "name": "foo/bar",
            "description": "Harbor's brief description.",
            "samples": 1,
            "version": "sha256:x",
        }
    ]
    overrides = {"foo/bar": {"desc": "A much richer hand-written description."}}
    decorated = decorate_datasets(fetched, overrides)
    assert decorated[0]["description"] == "A much richer hand-written description."
    assert (
        decorated[0]["clean_description"] == "A much richer hand-written description."
    )


def test_decorate_datasets_ignores_empty_desc_override() -> None:
    """Empty / whitespace-only ``desc`` falls through to the Harbor default."""
    fetched: list[FetchedDataset] = [
        {
            "name": "foo/bar",
            "description": "Harbor's description.",
            "samples": 1,
            "version": "sha256:x",
        }
    ]
    overrides = {"foo/bar": {"desc": "   "}}
    decorated = decorate_datasets(fetched, overrides)
    assert decorated[0]["description"] == "Harbor's description."


def test_decorate_datasets_rejects_non_string_desc_override() -> None:
    """Non-string ``desc`` overrides raise a clear error."""
    fetched: list[FetchedDataset] = [
        {
            "name": "foo/bar",
            "description": "x",
            "samples": 1,
            "version": "sha256:x",
        }
    ]
    overrides: dict[str, dict[str, object]] = {"foo/bar": {"desc": 42}}
    with pytest.raises(RuntimeError, match="Invalid desc override"):
        decorate_datasets(fetched, overrides)


def test_resolve_categories_groups_overrides_and_stubs_missing(
    mock_registry: list[Dataset],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resolve_categories: groups overrides, stubs missing, leaves blank stubs.

    Overrides with non-empty ``categories`` populate the map; missing
    entries are auto-stubbed into ``overrides.yml``; entries that exist
    with empty categories are left alone (not re-stubbed).
    """
    # Pre-existing overrides file — append_stub_entries needs it to exist.
    overrides_file = tmp_path / "overrides.yml"
    overrides_file.write_text("# header\n")
    monkeypatch.setattr("generate_tasks.OVERRIDES_FILE", overrides_file)

    overrides: dict[str, dict[str, object]] = {
        "dbt-labs/ade-bench": {"categories": ["agentic", "coding"]},
        # ``harbor/hello-world`` exists with empty categories — a blank
        # stub waiting on a human. resolve_categories must NOT re-stub it.
        "harbor/hello-world": {"categories": []},
        # ``LiteCoder/LiteCoder-rl`` is missing entirely → should be auto-stubbed.
    }

    categories_map, new_names = resolve_categories(mock_registry, overrides)

    # Both "valid" and "empty-stub" overrides land in the map (empty lists
    # are kept verbatim — the listing just shows no category chip).
    assert categories_map == {
        "dbt-labs/ade-bench": ["agentic", "coding"],
        "harbor/hello-world": [],
    }
    # Only the truly-missing dataset is stubbed — present-but-empty stays put.
    assert new_names == ["LiteCoder/LiteCoder-rl"]
    # The stub was appended to the overrides file.
    assert "LiteCoder/LiteCoder-rl:" in overrides_file.read_text()
    assert "categories: []" in overrides_file.read_text()


def test_resolve_categories_skips_non_string_category_lists(
    mock_registry: list[Dataset],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed ``categories`` values are silently dropped from the map.

    Covers ``null``, non-list, and list-with-non-strings. The dataset is
    not re-stubbed because the override entry itself exists.
    """
    overrides_file = tmp_path / "overrides.yml"
    overrides_file.write_text("# header\n")
    monkeypatch.setattr("generate_tasks.OVERRIDES_FILE", overrides_file)

    overrides: dict[str, dict[str, object]] = {
        "dbt-labs/ade-bench": {"categories": None},  # malformed
        "harbor/hello-world": {"categories": "not-a-list"},  # malformed
        "LiteCoder/LiteCoder-rl": {"categories": ["valid"]},
    }
    categories_map, new_names = resolve_categories(mock_registry, overrides)
    assert categories_map == {"LiteCoder/LiteCoder-rl": ["valid"]}
    assert new_names == []


def test_build_table_rows_shows_latest_digest_and_samples(
    mock_registry: list[Dataset],
) -> None:
    """The table rows surface the latest digest, sample count, and the func name."""
    pkg = next(d for d in mock_registry if d["name"] == "harbor/hello-world")
    rows = _build_table_rows(pkg, {})
    assert "| Latest digest   | sha256:abc123 |" in rows
    assert "| Inspect task    | `harbor_hello_world` |" in rows
    assert "| Samples         | 1 |" in rows


def test_build_table_rows_includes_arxiv_and_repo_overrides(
    mock_registry: list[Dataset],
) -> None:
    """``arxiv`` and ``repo`` keys from overrides become Paper / Source rows."""
    pkg = next(d for d in mock_registry if d["name"] == "dbt-labs/ade-bench")
    override = {
        "arxiv": "https://arxiv.org/abs/1234.5678",
        "repo": "https://github.com/acme/foo",
    }
    rows = _build_table_rows(pkg, override)
    assert "| Paper           | [arxiv](https://arxiv.org/abs/1234.5678) |" in rows
    assert (
        "| Source          | [https://github.com/acme/foo](https://github.com/acme/foo) |"
        in rows
    )


def test_build_table_rows_omits_paper_and_source_when_overrides_empty(
    mock_registry: list[Dataset],
) -> None:
    """Without ``arxiv``/``repo`` in overrides, Paper / Source rows are absent."""
    pkg = next(d for d in mock_registry if d["name"] == "dbt-labs/ade-bench")
    rows = _build_table_rows(pkg, {})
    assert "Paper" not in rows
    assert "Source" not in rows


def test_generate_registry_pages_writes_one_qmd_per_dataset(
    mock_registry: list[Dataset],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One ``.qmd`` is written per dataset under ``REGISTRY_PAGES_DIR``."""
    monkeypatch.setattr("generate_tasks.REGISTRY_PAGES_DIR", tmp_path)
    written = generate_registry_pages(mock_registry, {}, {})
    assert written == 3
    assert (tmp_path / "dbt_labs_ade_bench.qmd").exists()
    assert (tmp_path / "harbor_hello_world.qmd").exists()
    assert (tmp_path / "litecoder_litecoder_rl.qmd").exists()


def test_generate_registry_pages_deletes_orphans(
    mock_registry: list[Dataset],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stale ``.qmd`` files (datasets removed/renamed since last run) are deleted."""
    monkeypatch.setattr("generate_tasks.REGISTRY_PAGES_DIR", tmp_path)
    # Leftover from a previous run — dataset no longer in the registry.
    stale = tmp_path / "removed_dataset.qmd"
    stale.write_text("---\ntitle: gone\n---\n")
    # An unrelated file (not .qmd) should NOT be touched.
    unrelated = tmp_path / "notes.md"
    unrelated.write_text("keep me")

    generate_registry_pages(mock_registry, {}, {})

    assert not stale.exists()
    assert unrelated.exists()
