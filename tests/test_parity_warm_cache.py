"""Tests for the parity cache warm-up script."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from parity_warm_cache import main, registry_slugs  # noqa: E402


def test_registry_slugs_reads_titles_from_listing(tmp_path: Path) -> None:
    """The warm-up takes its ``org/name`` slugs from the generated listing."""
    listing = tmp_path / "registry-listing.yml"
    listing.write_text(
        "- title: acme/bench\n  path: registry/acme_bench.html\n"
        "- title: harbor/hello-world\n  path: registry/harbor_hello_world.html\n"
    )
    assert registry_slugs(listing) == ["acme/bench", "harbor/hello-world"]


def test_main_fails_when_nothing_loaded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty listing must not produce a green warm-up."""
    monkeypatch.setenv("INSPECT_HARBOR_CACHE_DIR", str(tmp_path / "cache"))
    listing = tmp_path / "registry-listing.yml"
    listing.write_text("")
    assert main(listing) == 1
