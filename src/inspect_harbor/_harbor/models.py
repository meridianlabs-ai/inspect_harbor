"""Pydantic models for Harbor's ``task.toml``.

These mirror the parts of Harbor's ``TaskConfig`` that inspect_harbor reads.
Parsing is deliberately lenient: every model accepts unknown keys (they are
kept and surface in ``model_dump()``, which feeds sample metadata) but the
fields we act on are typed strictly. Unknown keys in the sections we care
about, and a ``schema_version`` newer than we were written against, are
logged as warnings (Inspect surfaces Python logging in the console and in
eval logs) so schema drift is visible without breaking task loading.
Deprecated fields that Harbor still accepts are migrated silently and noted
at debug level: they are the task author's concern, not the evaluator's.
Re-validating a config that already loaded, as the scorer does from sample
metadata, passes ``context={"quiet": True}`` so nothing is logged twice.

Written against Harbor's task.toml schema 1.4.
"""

import logging
import re
import tomllib
import unicodedata
from enum import Enum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

logger = logging.getLogger(__name__)

SUPPORTED_SCHEMA_VERSION = "1.4"

ORG_NAME_PATTERN = r"^[a-zA-Z0-9][a-zA-Z0-9._-]*/[a-zA-Z0-9][a-zA-Z0-9._-]*$"
# Compose service that runs the agent; collect hooks target it by default.
MAIN_SERVICE_NAME = "main"
_COMPOSE_SERVICE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
_LEGACY_ENVIRONMENT_KEYS = {"memory", "storage"}


class NetworkMode(str, Enum):
    """Network access policy for the task environment."""

    NO_NETWORK = "no-network"
    PUBLIC = "public"
    ALLOWLIST = "allowlist"


class TaskOS(str, Enum):
    """Target operating system for a task's container."""

    LINUX = "linux"
    WINDOWS = "windows"


class VerifierEnvironmentMode(str, Enum):
    """Whether the verifier runs in the agent's environment or its own."""

    SHARED = "shared"
    SEPARATE = "separate"


class Author(BaseModel):
    """Author entry under ``[task]``."""

    model_config = ConfigDict(extra="allow")

    name: str
    email: str | None = None


class PackageInfo(BaseModel):
    """The ``[task]`` section: package identity on the Harbor hub."""

    model_config = ConfigDict(extra="allow")

    name: str
    version: str | None = Field(default=None, min_length=1)
    description: str = ""
    authors: list[Author] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _warn_unknown(cls, data: Any, info: ValidationInfo) -> Any:
        if isinstance(data, dict):
            _warn_unknown_keys("[task]", data, set(cls.model_fields), info)
        return data

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        if not re.match(ORG_NAME_PATTERN, v) or ".." in v:
            raise ValueError(
                "Package name must be in 'org/name' format with alphanumeric "
                "characters, hyphens, underscores, and dots. Cannot start with a "
                f"dot or contain '..'. Got: {v}"
            )
        return v

    @property
    def org(self) -> str:
        """Organisation part of ``org/name``."""
        return self.name.split("/")[0]

    @property
    def short_name(self) -> str:
        """Name part of ``org/name``."""
        return self.name.split("/")[1]


class HealthcheckConfig(BaseModel):
    """``[environment.healthcheck]``, mirroring Docker HEALTHCHECK options."""

    model_config = ConfigDict(extra="allow")

    command: str
    interval_sec: float = 5.0
    timeout_sec: float = 30.0
    start_period_sec: float = 0.0
    start_interval_sec: float = 5.0
    retries: int = 3


class EnvironmentConfig(BaseModel):
    """The ``[environment]`` section."""

    model_config = ConfigDict(extra="allow")

    build_timeout_sec: float = 600.0
    docker_image: str | None = None
    os: TaskOS = TaskOS.LINUX
    cpus: int | None = None
    memory_mb: int | None = None
    storage_mb: int | None = None
    gpus: int | None = None
    gpu_types: list[str] | None = None
    tpu: dict[str, Any] | None = None
    mcp_servers: list[dict[str, Any]] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    skills_dir: str | None = None
    healthcheck: HealthcheckConfig | None = None
    workdir: str | None = None
    network_mode: NetworkMode = NetworkMode.PUBLIC
    allowed_hosts: list[str] | None = None
    # Deprecated alias for ``network_mode``; migrated and cleared by TaskConfig.
    allow_internet: bool | None = Field(default=None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def _migrate_and_warn(cls, data: Any, info: ValidationInfo) -> Any:
        if not isinstance(data, dict):
            return data
        _warn_unknown_keys(
            "[environment]",
            data,
            set(cls.model_fields) | _LEGACY_ENVIRONMENT_KEYS,
            info,
        )
        if data.get("allow_internet") is not None:
            logger.debug(
                "task.toml uses the deprecated 'allow_internet' field; "
                "use [environment].network_mode instead."
            )
        if isinstance(data.get("os"), str):
            data["os"] = data["os"].lower()
        _migrate_legacy_size(data, "memory", "memory_mb")
        _migrate_legacy_size(data, "storage", "storage_mb")
        return data

    @model_validator(mode="after")
    def _validate_network_policy(self) -> "EnvironmentConfig":
        _validate_allowed_hosts(self.network_mode, self.allowed_hosts)
        return self


class VerifierCollectConfig(BaseModel):
    """A ``[[verifier.collect]]`` hook: a command run after the agent phase.

    Hooks snapshot runtime state into files before verification. Only hooks
    targeting the main service can run in inspect_harbor's single sandbox.
    """

    model_config = ConfigDict(extra="allow")

    command: str
    service: str = MAIN_SERVICE_NAME
    timeout_sec: float = 60.0
    user: str | int | None = None

    @field_validator("service")
    @classmethod
    def _validate_service(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Collect hook service must not be empty.")
        if not _COMPOSE_SERVICE_NAME_PATTERN.match(value):
            raise ValueError(
                f"Invalid Docker Compose service name: {value!r}. Service names "
                "must start with an alphanumeric character and contain only "
                "alphanumeric characters, hyphens, underscores, and dots."
            )
        return value


class VerifierConfig(BaseModel):
    """The ``[verifier]`` section."""

    model_config = ConfigDict(extra="allow")

    timeout_sec: float = 600.0
    env: dict[str, str] = Field(default_factory=dict)
    user: str | int | None = None
    environment_mode: VerifierEnvironmentMode | None = None
    environment: EnvironmentConfig | None = None
    collect: list[VerifierCollectConfig] = Field(default_factory=list)
    network_mode: NetworkMode | None = None
    allowed_hosts: list[str] | None = None

    @model_validator(mode="before")
    @classmethod
    def _warn_unknown(cls, data: Any, info: ValidationInfo) -> Any:
        if isinstance(data, dict):
            _warn_unknown_keys("[verifier]", data, set(cls.model_fields), info)
        return data

    @model_validator(mode="after")
    def _validate(self) -> "VerifierConfig":
        if (
            self.environment_mode is VerifierEnvironmentMode.SHARED
            and self.environment is not None
        ):
            raise ValueError(
                "[verifier].environment_mode='shared' is incompatible with "
                "[verifier.environment]; either omit the environment or set "
                "environment_mode='separate'."
            )
        _validate_allowed_hosts(self.network_mode, self.allowed_hosts)
        return self

    def runs_separately(self) -> bool:
        """Whether the verifier runs in its own container rather than the agent's."""
        if self.environment_mode is not None:
            return self.environment_mode is VerifierEnvironmentMode.SEPARATE
        return self.environment is not None


class AgentConfig(BaseModel):
    """The ``[agent]`` section."""

    model_config = ConfigDict(extra="allow")

    timeout_sec: float | None = None
    user: str | int | None = None
    network_mode: NetworkMode | None = None
    allowed_hosts: list[str] | None = None

    @model_validator(mode="before")
    @classmethod
    def _warn_unknown(cls, data: Any, info: ValidationInfo) -> Any:
        if isinstance(data, dict):
            _warn_unknown_keys("[agent]", data, set(cls.model_fields), info)
        return data

    @model_validator(mode="after")
    def _validate_network_policy(self) -> "AgentConfig":
        _validate_allowed_hosts(self.network_mode, self.allowed_hosts)
        return self


class SolutionConfig(BaseModel):
    """The ``[solution]`` section."""

    model_config = ConfigDict(extra="allow")

    env: dict[str, str] = Field(default_factory=dict)


class StepConfig(BaseModel):
    """One ``[[steps]]`` entry of a multi-step task.

    inspect_harbor does not run multi-step tasks; we only need the names to
    detect and refuse them, and to validate the task directory like Harbor.
    """

    model_config = ConfigDict(extra="allow")

    name: str


class TaskConfig(BaseModel):
    """A parsed ``task.toml``."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = SUPPORTED_SCHEMA_VERSION
    task: PackageInfo | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    verifier: VerifierConfig = Field(default_factory=VerifierConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    solution: SolutionConfig = Field(default_factory=SolutionConfig)
    source: str | None = None
    multi_step_reward_strategy: str | None = None
    steps: list[StepConfig] | None = None
    artifacts: list[Any] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _rename_and_warn(cls, data: Any, info: ValidationInfo) -> Any:
        if not isinstance(data, dict):
            return data
        if "version" in data:
            data.setdefault("schema_version", data.pop("version"))
        _warn_unknown_keys("top level", data, set(cls.model_fields), info)
        declared = data.get("schema_version")
        if isinstance(declared, str) and not _quiet(info):
            got = _schema_version_tuple(declared)
            supported = _schema_version_tuple(SUPPORTED_SCHEMA_VERSION)
            if got is not None and supported is not None and got > supported:
                logger.warning(
                    "task.toml declares schema_version %r, newer than the %s "
                    "inspect_harbor was written against; loading anyway.",
                    declared,
                    SUPPORTED_SCHEMA_VERSION,
                )
        return data

    @model_validator(mode="after")
    def _validate(self) -> "TaskConfig":
        for env in (self.environment, self.verifier.environment):
            if env is None or env.allow_internet is None:
                continue
            if "network_mode" not in env.model_fields_set and env.allowed_hosts is None:
                env.network_mode = (
                    NetworkMode.PUBLIC if env.allow_internet else NetworkMode.NO_NETWORK
                )
            env.allow_internet = None
        if self.steps is not None:
            # Collisions on case-insensitive, Unicode-normalising filesystems.
            keys = [unicodedata.normalize("NFC", s.name).casefold() for s in self.steps]
            if len(set(keys)) != len(keys):
                raise ValueError(
                    "Step names must be unique, including case and Unicode "
                    f"normalisation variants: {[s.name for s in self.steps]}"
                )
        return self

    @classmethod
    def from_toml(cls, text: str) -> "TaskConfig":
        """Parse the text of a ``task.toml``.

        Raises:
            tomllib.TOMLDecodeError: On TOML syntax errors.
            pydantic.ValidationError: On values of the wrong type.
        """
        return cls.model_validate(tomllib.loads(text))

    @classmethod
    def from_metadata(cls, data: dict[str, Any]) -> "TaskConfig":
        """Rebuild a config from a ``model_dump()`` (e.g. sample metadata).

        The config already logged any drift when the task loaded, so this
        path is quiet.
        """
        return cls.model_validate(data, context={"quiet": True})

    def verifier_runs_separately(self) -> bool:
        """Whether the verifier runs in its own container (see ``VerifierConfig``)."""
        return self.verifier.runs_separately()


def _quiet(info: ValidationInfo) -> bool:
    return bool(info.context and info.context.get("quiet"))


def _warn_unknown_keys(
    section: str, data: dict[str, Any], known: set[str], info: ValidationInfo
) -> None:
    unknown = sorted(k for k in data if k not in known)
    if unknown and not _quiet(info):
        logger.warning(
            "task.toml %s declares keys inspect_harbor does not know: %s. They are "
            "kept in sample metadata but have no effect; check Harbor's changelog "
            "for new task.toml semantics.",
            section,
            unknown,
        )


def _validate_allowed_hosts(
    network_mode: NetworkMode | None, allowed_hosts: list[str] | None
) -> None:
    """Mirror Harbor's rule: ``allowed_hosts`` only goes with ``allowlist``."""
    if network_mode is None:
        if allowed_hosts is not None:
            raise ValueError(
                "allowed_hosts is only valid when network_mode='allowlist'."
            )
        return
    if network_mode is not NetworkMode.ALLOWLIST and allowed_hosts:
        raise ValueError("allowed_hosts is only valid when network_mode='allowlist'.")


def _parse_size_to_mb(size_str: str) -> int:
    size_str = size_str.strip().upper()
    if size_str.endswith("G"):
        return int(float(size_str[:-1]) * 1024)
    if size_str.endswith("M"):
        return int(float(size_str[:-1]))
    if size_str.endswith("K"):
        return int(float(size_str[:-1]) / 1024)
    raise ValueError(
        f"Invalid size format: {size_str}. Expected format like '1G', '512M', etc."
    )


def _migrate_legacy_size(data: dict[str, Any], legacy: str, current: str) -> None:
    if legacy not in data:
        return
    logger.debug(
        "task.toml uses the deprecated '%s' field; use '%s' instead.", legacy, current
    )
    value = data.pop(legacy)
    if isinstance(value, str):
        mb = _parse_size_to_mb(value)
        if current in data and data[current] != mb:
            raise ValueError(
                f"Conflicting '{legacy}' and '{current}' values: "
                f"{legacy}={value!r} ({mb} MB) != {current}={data[current]!r}."
            )
        data.setdefault(current, mb)


def _schema_version_tuple(version: str) -> tuple[int, ...] | None:
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return None
