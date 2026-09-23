"""Tests for the task.toml models."""

import operator
import warnings
from pathlib import Path
from typing import Any

import pytest
from inspect_harbor._harbor.models import (
    NetworkMode,
    TaskConfig,
    TaskOS,
    VerifierEnvironmentMode,
)
from pydantic import ValidationError

FIXTURE_TOML = (
    Path(__file__).parent / "fixtures" / "simple_task" / "task.toml"
).read_text()

KNOWN_FIELDS_TOML = "\n".join(
    [
        "[environment]",
        'docker_image = "x"',
        "cpus = 1",
        "memory_mb = 1024",
        "storage_mb = 1024",
        "gpus = 1",
        'gpu_types = ["H100"]',
        'skills_dir = "skills"',
        'workdir = "/app"',
        "[environment.env]",
        'FOO = "bar"',
        "[environment.healthcheck]",
        'command = "true"',
        "[[environment.mcp_servers]]",
        'name = "srv"',
        'url = "http://x"',
        "[verifier]",
        "timeout_sec = 1",
        'user = "root"',
        "[verifier.env]",
        'A = "b"',
        "[agent]",
        "user = 1000",
        "[solution.env]",
        'S = "t"',
        "[metadata]",
        'anything = "goes"',
    ]
)


def test_defaults_mirror_harbor() -> None:
    """An empty task.toml, and a bare healthcheck, yield Harbor's defaults."""
    config = TaskConfig.from_toml("")
    assert config.task is None
    assert config.schema_version == "1.4"
    assert config.environment.os is TaskOS.LINUX
    assert config.environment.network_mode is NetworkMode.PUBLIC
    assert config.environment.cpus is None
    assert config.environment.env == {}
    assert config.verifier.timeout_sec == 600.0
    assert config.verifier.user is None
    assert config.agent.user is None
    assert config.solution.env == {}

    hc = TaskConfig.from_toml(
        '[environment.healthcheck]\ncommand = "x"\n'
    ).environment.healthcheck
    assert hc is not None
    assert (hc.interval_sec, hc.timeout_sec, hc.start_period_sec) == (5.0, 30.0, 0.0)
    assert (hc.start_interval_sec, hc.retries) == (5.0, 3)


@pytest.mark.parametrize(
    "toml,attr,expected",
    [
        (
            "[environment]\nallow_internet = false\n",
            "environment.network_mode",
            NetworkMode.NO_NETWORK,
        ),
        (
            "[environment]\nallow_internet = true\n",
            "environment.network_mode",
            NetworkMode.PUBLIC,
        ),
        (
            '[environment]\nnetwork_mode = "public"\nallow_internet = false\n',
            "environment.network_mode",
            NetworkMode.PUBLIC,
        ),
        (
            "[verifier.environment]\nallow_internet = false\n",
            "verifier.environment.network_mode",
            NetworkMode.NO_NETWORK,
        ),
        ('[environment]\nmemory = "8G"\n', "environment.memory_mb", 8192),
        ('[environment]\nmemory = "512M"\n', "environment.memory_mb", 512),
        ('[environment]\nmemory = "1.5g"\n', "environment.memory_mb", 1536),
        ('[environment]\nmemory = "2048K"\n', "environment.memory_mb", 2),
        ('[environment]\nstorage = "10G"\n', "environment.storage_mb", 10240),
        ('[environment]\nos = "Windows"\n', "environment.os", TaskOS.WINDOWS),
        ('version = "1.2"\n', "schema_version", "1.2"),
        (
            '[environment]\nnetwork_mode = "allowlist"\nallowed_hosts = ["a.com"]\n',
            "environment.allowed_hosts",
            ["a.com"],
        ),
    ],
)
def test_values_migrate_silently(toml: str, attr: str, expected: Any) -> None:
    """Legacy and alternate spellings map to Harbor's current fields, without warnings."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        config = TaskConfig.from_toml(toml)
    assert operator.attrgetter(attr)(config) == expected
    dumped = config.model_dump()
    for legacy in ("allow_internet", "memory", "storage"):
        assert legacy not in dumped["environment"]
    assert "version" not in dumped


@pytest.mark.parametrize(
    "toml,match",
    [
        ('[environment]\nmemory = "1G"\nmemory_mb = 512\n', "Conflicting"),
        ('[environment]\nmemory = "1024"\n', "Invalid size format"),
        ('[environment]\ncpus = "two"\n', "cpus"),
        ('[environment]\nallowed_hosts = ["a.com"]\n', "allowlist"),
        ("[agent]\nallowed_hosts = []\n", "allowlist"),
        (
            '[verifier]\nnetwork_mode = "no-network"\nallowed_hosts = ["a"]\n',
            "allowlist",
        ),
        (
            '[verifier]\nenvironment_mode = "shared"\n[verifier.environment]\ndocker_image = "x"\n',
            "incompatible",
        ),
        ('[[steps]]\nname = "Step"\n[[steps]]\nname = "step"\n', "unique"),
        ('[task]\nname = "bad"\n', "org/name"),
        ('[task]\nname = "a/../b"\n', "org/name"),
        ('[[verifier.collect]]\ncommand = "x"\nservice = "  "\n', "service"),
        ('[[verifier.collect]]\ncommand = "x"\nservice = "a/b"\n', "service"),
    ],
)
def test_invalid_configs_are_rejected(toml: str, match: str) -> None:
    """Type, size, network-policy, step, package-name and hook rules match Harbor's."""
    with pytest.raises(ValidationError, match=match):
        TaskConfig.from_toml(toml)


@pytest.mark.parametrize(
    "toml,match",
    [
        ('schema_version = "9.0"\n', "schema_version"),
        ("[environment]\nfrobnicate = 1\n", r"\[environment\].*frobnicate"),
        ("[mystery]\nx = 1\n", "top level.*mystery"),
        ('schema_version = "dev"\n', None),
        (FIXTURE_TOML, None),
        (KNOWN_FIELDS_TOML, None),
    ],
)
def test_schema_drift_warnings(toml: str, match: str | None) -> None:
    """Unknown keys and newer schemas warn; known keys and odd versions are silent."""
    if match is None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            TaskConfig.from_toml(toml)
        return
    with pytest.warns(UserWarning, match=match):
        config = TaskConfig.from_toml(toml)
    if "frobnicate" in toml:
        # Unknown keys are kept, so sample metadata carries the full task.toml.
        assert config.model_dump()["environment"]["frobnicate"] == 1


def test_package_info_parses() -> None:
    """``[task]`` fields round-trip and ``org``/``short_name`` split the slug."""
    config = TaskConfig.from_toml(
        "\n".join(
            [
                "[task]",
                'name = "Some-Org/some.name_1"',
                'version = "1.0.0"',
                'keywords = ["a", "b"]',
                "[[task.authors]]",
                'name = "Ann"',
                'email = "ann@example.com"',
            ]
        )
    )
    assert config.task is not None
    assert (config.task.org, config.task.short_name) == ("Some-Org", "some.name_1")
    assert (config.task.version, config.task.keywords) == ("1.0.0", ["a", "b"])
    assert [a.model_dump() for a in config.task.authors] == [
        {"name": "Ann", "email": "ann@example.com"}
    ]


def test_verifier_runs_separately() -> None:
    """Separate-verifier detection follows Harbor's inference rules."""
    assert TaskConfig.from_toml("").verifier_runs_separately() is False
    assert (
        TaskConfig.from_toml(
            '[verifier]\nenvironment_mode = "separate"\n'
        ).verifier_runs_separately()
        is True
    )
    assert (
        TaskConfig.from_toml(
            '[verifier.environment]\ndocker_image = "x"\n'
        ).verifier_runs_separately()
        is True
    )
    config = TaskConfig.from_toml('[verifier]\nenvironment_mode = "shared"\n')
    assert config.verifier.environment_mode is VerifierEnvironmentMode.SHARED
    assert config.verifier_runs_separately() is False


def test_verifier_collect_hooks() -> None:
    """``[[verifier.collect]]`` hooks parse with Harbor's defaults and round-trip."""
    config = TaskConfig.from_toml(
        "\n".join(
            [
                "[[verifier.collect]]",
                'command = "pg_dump > /logs/artifacts/db.sql"',
                "[[verifier.collect]]",
                'command = "echo hi"',
                'service = "sidecar"',
                "timeout_sec = 5",
                "user = 1000",
            ]
        )
    )
    first, second = config.verifier.collect
    assert (first.service, first.timeout_sec, first.user) == ("main", 60.0, None)
    assert (second.service, second.timeout_sec, second.user) == ("sidecar", 5, 1000)
    # The metadata round trip the scorer relies on.
    assert TaskConfig.model_validate(config.model_dump()).verifier.collect == [
        first,
        second,
    ]
