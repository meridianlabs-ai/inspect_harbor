"""Tests for the task.toml models."""

import tomllib
import warnings
from pathlib import Path

import pytest
from inspect_harbor._harbor.models import (
    MAIN_SERVICE_NAME,
    NetworkMode,
    PackageInfo,
    TaskConfig,
    TaskOS,
    VerifierEnvironmentMode,
)
from pydantic import ValidationError

FIXTURE_TOML = (
    Path(__file__).parent / "fixtures" / "simple_task" / "task.toml"
).read_text()


def test_fixture_parses() -> None:
    """The integration fixture parses with the values it declares."""
    config = TaskConfig.from_toml(FIXTURE_TOML)
    assert config.task is not None
    assert config.task.name == "harbor-test/simple-task"
    assert config.environment.docker_image == "python:3.11-slim"
    assert config.environment.network_mode is NetworkMode.NO_NETWORK
    assert config.environment.cpus is None
    assert config.environment.memory_mb is None
    assert config.environment.gpus is None
    assert config.verifier.timeout_sec == 60
    assert config.agent.timeout_sec == 120
    assert config.steps is None


def test_defaults_when_sections_absent() -> None:
    """An empty task.toml yields Harbor's defaults."""
    config = TaskConfig.from_toml("")
    assert config.task is None
    assert config.environment.os is TaskOS.LINUX
    assert config.environment.network_mode is NetworkMode.PUBLIC
    assert config.environment.env == {}
    assert config.verifier.timeout_sec == 600.0
    assert config.verifier.env == {}
    assert config.verifier.user is None
    assert config.agent.user is None
    assert config.solution.env == {}
    assert config.schema_version == "1.4"


def test_allow_internet_false_migrates_to_no_network(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Legacy ``allow_internet = false`` becomes ``network_mode = no-network``.

    The deprecation is a task-author concern, so it is logged at debug rather
    than warned at the evaluator.
    """
    with caplog.at_level("DEBUG", logger="inspect_harbor._harbor.models"):
        config = TaskConfig.from_toml("[environment]\nallow_internet = false\n")
    assert "deprecated 'allow_internet'" in caplog.text
    assert config.environment.network_mode is NetworkMode.NO_NETWORK
    assert config.environment.allow_internet is None
    assert "allow_internet" not in config.model_dump()["environment"]


def test_allow_internet_true_migrates_to_public() -> None:
    """Legacy ``allow_internet = true`` becomes ``network_mode = public``."""
    config = TaskConfig.from_toml("[environment]\nallow_internet = true\n")
    assert config.environment.network_mode is NetworkMode.PUBLIC


def test_explicit_network_mode_beats_allow_internet() -> None:
    """An explicit ``network_mode`` wins over the deprecated boolean."""
    config = TaskConfig.from_toml(
        '[environment]\nnetwork_mode = "public"\nallow_internet = false\n'
    )
    assert config.environment.network_mode is NetworkMode.PUBLIC


def test_verifier_environment_allow_internet_migrates() -> None:
    """The migration also applies to a separate verifier environment."""
    config = TaskConfig.from_toml("[verifier.environment]\nallow_internet = false\n")
    assert config.verifier.environment is not None
    assert config.verifier.environment.network_mode is NetworkMode.NO_NETWORK
    assert config.verifier.environment.allow_internet is None


@pytest.mark.parametrize(
    "memory,expected_mb",
    [("8G", 8192), ("512M", 512), ("1.5g", 1536), ("2048K", 2)],
)
def test_legacy_memory_string_migrates(memory: str, expected_mb: int) -> None:
    """Legacy ``memory`` size strings are converted to ``memory_mb``."""
    config = TaskConfig.from_toml(f'[environment]\nmemory = "{memory}"\n')
    assert config.environment.memory_mb == expected_mb
    assert "memory" not in config.model_dump()["environment"]


def test_legacy_storage_string_migrates() -> None:
    """Legacy ``storage`` size strings are converted to ``storage_mb``."""
    config = TaskConfig.from_toml('[environment]\nstorage = "10G"\n')
    assert config.environment.storage_mb == 10240


@pytest.mark.parametrize(
    "toml,match",
    [
        ('[environment]\nmemory = "1G"\nmemory_mb = 512\n', "Conflicting"),
        ('[environment]\nmemory = "1024"\n', "Invalid size format"),
    ],
)
def test_bad_legacy_sizes_raise(toml: str, match: str) -> None:
    """Conflicting or unit-less legacy sizes are rejected."""
    with pytest.raises(ValidationError, match=match):
        TaskConfig.from_toml(toml)


def test_os_is_case_insensitive() -> None:
    """``os`` accepts any casing."""
    config = TaskConfig.from_toml('[environment]\nos = "Windows"\n')
    assert config.environment.os is TaskOS.WINDOWS


def test_top_level_version_renamed_to_schema_version() -> None:
    """The pre-1.x ``version`` key is treated as ``schema_version``."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        config = TaskConfig.from_toml('version = "1.2"\n')
    assert config.schema_version == "1.2"


def test_newer_schema_version_warns() -> None:
    """A task.toml newer than we know how to read warns but still loads."""
    with pytest.warns(UserWarning, match="schema_version"):
        config = TaskConfig.from_toml('schema_version = "9.0"\n')
    assert config.schema_version == "9.0"


def test_unparseable_schema_version_does_not_warn() -> None:
    """A non-numeric schema version is left alone."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        TaskConfig.from_toml('schema_version = "dev"\n')


def test_unknown_environment_key_warns_and_is_kept() -> None:
    """Unknown keys are reported once and preserved in ``model_dump``."""
    with pytest.warns(UserWarning, match=r"\[environment\].*frobnicate"):
        config = TaskConfig.from_toml("[environment]\nfrobnicate = 1\n")
    assert config.model_dump()["environment"]["frobnicate"] == 1


def test_unknown_top_level_table_warns() -> None:
    """Unknown top-level tables are reported."""
    with pytest.warns(UserWarning, match="top level.*mystery"):
        TaskConfig.from_toml("[mystery]\nx = 1\n")


def test_known_fields_do_not_warn() -> None:
    """A task.toml using only known keys is silent."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        TaskConfig.from_toml(FIXTURE_TOML)
        TaskConfig.from_toml(
            "\n".join(
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
        )


def test_package_info_name_validation() -> None:
    """Package names must be ``org/name``."""
    with pytest.raises(ValidationError, match="org/name"):
        PackageInfo(name="bad")
    with pytest.raises(ValidationError, match="org/name"):
        PackageInfo(name="a/../b")
    info = PackageInfo(name="Some-Org/some.name_1")
    assert info.org == "Some-Org"
    assert info.short_name == "some.name_1"


def test_package_info_fields() -> None:
    """Authors and keywords round-trip."""
    config = TaskConfig.from_toml(
        "\n".join(
            [
                "[task]",
                'name = "org/thing"',
                'version = "1.0.0"',
                'description = "desc"',
                'keywords = ["a", "b"]',
                "[[task.authors]]",
                'name = "Ann"',
                'email = "ann@example.com"',
            ]
        )
    )
    assert config.task is not None
    assert config.task.version == "1.0.0"
    assert config.task.keywords == ["a", "b"]
    assert [a.model_dump() for a in config.task.authors] == [
        {"name": "Ann", "email": "ann@example.com"}
    ]


def test_healthcheck_defaults() -> None:
    """Healthcheck timing defaults mirror Harbor's."""
    config = TaskConfig.from_toml(
        '[environment.healthcheck]\ncommand = "curl -f localhost"\n'
    )
    hc = config.environment.healthcheck
    assert hc is not None
    assert hc.command == "curl -f localhost"
    assert hc.interval_sec == 5.0
    assert hc.timeout_sec == 30.0
    assert hc.start_period_sec == 0.0
    assert hc.start_interval_sec == 5.0
    assert hc.retries == 3


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


def test_shared_mode_with_environment_raises() -> None:
    """``environment_mode = shared`` conflicts with a verifier environment."""
    with pytest.raises(ValidationError, match="incompatible"):
        TaskConfig.from_toml(
            '[verifier]\nenvironment_mode = "shared"\n'
            '[verifier.environment]\ndocker_image = "x"\n'
        )


@pytest.mark.parametrize(
    "toml,match",
    [
        ('[environment]\nallowed_hosts = ["a.com"]\n', "allowlist"),
        (
            '[environment]\nnetwork_mode = "public"\nallowed_hosts = ["a.com"]\n',
            "allowlist",
        ),
        ("[agent]\nallowed_hosts = []\n", "allowlist"),
        (
            '[verifier]\nnetwork_mode = "no-network"\nallowed_hosts = ["a"]\n',
            "allowlist",
        ),
        ('[[steps]]\nname = "a"\n[[steps]]\nname = "a"\n', "unique"),
        ('[[steps]]\nname = "Step"\n[[steps]]\nname = "step"\n', "unique"),
    ],
)
def test_configs_harbor_rejects_are_rejected(toml: str, match: str) -> None:
    """Network-policy and step-name rules match Harbor's validators."""
    with pytest.raises(ValidationError, match=match):
        TaskConfig.from_toml(toml)


def test_allowlist_with_hosts_is_accepted() -> None:
    """``allowlist`` is the one mode where ``allowed_hosts`` is valid."""
    config = TaskConfig.from_toml(
        '[environment]\nnetwork_mode = "allowlist"\nallowed_hosts = ["a.com"]\n'
    )
    assert config.environment.allowed_hosts == ["a.com"]


def test_steps_detected() -> None:
    """``[[steps]]`` entries are parsed by name."""
    config = TaskConfig.from_toml('[[steps]]\nname = "one"\n[[steps]]\nname = "two"\n')
    assert config.steps is not None
    assert [s.name for s in config.steps] == ["one", "two"]


def test_invalid_toml_raises() -> None:
    """Syntax errors surface as ``TOMLDecodeError``."""
    with pytest.raises(tomllib.TOMLDecodeError):
        TaskConfig.from_toml("[environment\n")


def test_wrong_type_raises() -> None:
    """Type errors on fields we read surface as ``ValidationError``."""
    with pytest.raises(ValidationError):
        TaskConfig.from_toml('[environment]\ncpus = "two"\n')


def test_model_dump_is_json_friendly() -> None:
    """``model_dump`` (used for sample metadata) contains plain values."""
    dumped = TaskConfig.from_toml(FIXTURE_TOML).model_dump()
    assert dumped["environment"]["network_mode"] == "no-network"
    assert dumped["environment"]["os"] == "linux"


def test_verifier_collect_hooks() -> None:
    """``[[verifier.collect]]`` hooks parse with Harbor's defaults and validation."""
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
    assert first.command == "pg_dump > /logs/artifacts/db.sql"
    assert first.service == MAIN_SERVICE_NAME == "main"
    assert first.timeout_sec == 60.0
    assert first.user is None
    assert second.service == "sidecar"
    assert second.timeout_sec == 5
    assert second.user == 1000
    # The metadata round trip the scorer relies on.
    assert TaskConfig.model_validate(config.model_dump()).verifier.collect == [
        first,
        second,
    ]


@pytest.mark.parametrize("service", ["", "  ", "-bad", "has space", "a/b"])
def test_verifier_collect_rejects_bad_service_names(service: str) -> None:
    """Service names follow compose rules and must not be empty."""
    with pytest.raises(ValidationError, match="service"):
        TaskConfig.from_toml(
            f'[[verifier.collect]]\ncommand = "x"\nservice = "{service}"\n'
        )
