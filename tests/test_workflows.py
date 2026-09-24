"""Tests for Build's permissions and the agent stubs' tier-2 opt-in.

An agent may land build and dependency configuration (pyproject.toml, uv.lock:
the tier-2 opt-in, meridianlabs-ai/agents design/executed-paths-residual.md),
and Build runs it on every same-repository pull request. So no Build job that
runs anything from the checkout may hold a write permission or leave the job
token in .git/config; the coverage writes run where nothing from the checkout
does.

With that in place the agent stubs opt in: every call of the reusable
workflows that land agent commits passes `allow_build_config: true`.
"""

from pathlib import Path
from typing import Any

import yaml

WORKFLOWS = Path(__file__).parent.parent / ".github" / "workflows"
BUILD = WORKFLOWS / "build.yaml"

# The `main` ruleset's required status checks.
REQUIRED_CHECKS = {
    f"{job} ({python})"
    for job in ("py-build", "py-lint", "py-test", "py-type")
    for python in ("3.12", "3.13")
}


def _load(path: Path) -> dict[Any, Any]:
    return yaml.safe_load(path.read_text())


def _runs_checkout_code(job: dict[str, Any]) -> bool:
    return any(
        "run" in step or step.get("uses", "").startswith("./")
        for step in job.get("steps", [])
    )


def _writes(permissions: dict[str, str]) -> set[str]:
    return {scope for scope, level in permissions.items() if level == "write"}


def test_build_jobs_that_run_the_checkout_hold_no_write_permission() -> None:
    """Jobs that run checkout code are read-only and persist no credentials."""
    workflow = _load(BUILD)
    assert workflow["permissions"] == {"contents": "read"}
    writers: dict[str, set[str]] = {}
    for name, job in workflow["jobs"].items():
        permissions = job.get("permissions", workflow["permissions"])
        checkouts = [
            s for s in job["steps"] if s.get("uses", "").startswith("actions/checkout@")
        ]
        if _runs_checkout_code(job):
            assert not _writes(permissions), name
            for checkout in checkouts:
                assert checkout["with"]["persist-credentials"] is False, name
        elif _writes(permissions):
            writers[name] = _writes(permissions)
    assert writers == {"coverage": {"contents"}}


def test_build_keeps_the_required_check_names() -> None:
    """The matrix jobs still produce exactly the ruleset's required checks."""
    workflow = _load(BUILD)
    checks = {
        f"{name} ({python})"
        for name, job in workflow["jobs"].items()
        for python in job.get("strategy", {})
        .get("matrix", {})
        .get("python-version", [])
    }
    assert checks == REQUIRED_CHECKS


def test_coverage_writes_run_nothing_from_the_pr() -> None:
    """The coverage comment and data branch are written outside checkout code.

    py-test computes the comment read-only and stores it; the workflow_run
    workflow posts it without a checkout, and main's data branch is written by
    a job that runs only the coverage action.
    """
    build = _load(BUILD)
    py_test = {s.get("id", s.get("name")): s for s in build["jobs"]["py-test"]["steps"]}
    assert py_test["coverage_comment"]["if"] == (
        "matrix.python-version == '3.12' && github.event_name == 'pull_request'"
    )
    stored = py_test["Store the coverage comment"]["with"]
    assert stored["name"] == "python-coverage-comment-action"
    assert stored["path"] == "python-coverage-comment-action.txt"

    coverage = build["jobs"]["coverage"]
    assert coverage["needs"] == "py-test"
    assert coverage["if"] == (
        "github.event_name == 'push' && github.ref == 'refs/heads/main'"
    )
    assert [s["uses"].split("@")[0] for s in coverage["steps"]] == [
        "actions/checkout",
        "actions/download-artifact",
        "py-cov-action/python-coverage-comment-action",
    ]
    assert (
        coverage["steps"][1]["with"]["name"]
        == py_test["Store the coverage data"]["with"]["name"]
    )

    comment = _load(WORKFLOWS / "coverage-comment.yml")
    # PyYAML reads the bare `on` key as True.
    assert comment[True]["workflow_run"]["workflows"] == [build["name"]]
    assert comment["permissions"] == {}
    (job,) = comment["jobs"].values()
    assert "head_repository.full_name == github.repository" in job["if"]
    assert _writes(job["permissions"]) == {"pull-requests"}
    (step,) = job["steps"]
    assert step["uses"].startswith("py-cov-action/python-coverage-comment-action@")
    assert step["with"]["GITHUB_PR_RUN_ID"] == "${{ github.event.workflow_run.id }}"


# The reusable workflows that declare `allow_build_config`; the reviewer
# (claude-review.yml) refuses bundles and takes no such input.
BUILD_CONFIG_WRITERS = {"claude.yml", "claude-auto.yml", "claude-auto-review.yml"}


def test_agent_stubs_opt_in_to_build_config() -> None:
    """Every writer call opts in to tier 2; the reviewer call passes nothing."""
    calls: dict[str, Any] = {}
    for stub in ("claude.yml", "claude-auto.yml", "claude-review.yml"):
        for name, job in _load(WORKFLOWS / stub)["jobs"].items():
            reusable = job["uses"].split("/")[-1].split("@")[0]
            calls[f"{stub}:{name}"] = (
                reusable,
                job.get("with", {}).get("allow_build_config"),
            )
    assert calls == {
        "claude.yml:claude": ("claude.yml", True),
        "claude.yml:claude-auto": ("claude.yml", True),
        "claude-auto.yml:ci-fix": ("claude-auto.yml", True),
        "claude-auto.yml:review-fix": ("claude-auto-review.yml", True),
        "claude-review.yml:review": ("claude-review.yml", None),
    }
    assert {reusable for reusable, opted in calls.values() if opted} == (
        BUILD_CONFIG_WRITERS
    )
