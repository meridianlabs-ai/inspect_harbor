"""Tests for Build's permissions and the agent stubs' tier-2 opt-in.

An agent may land build and dependency configuration (pyproject.toml, uv.lock:
the tier-2 opt-in, meridianlabs-ai/agents design/executed-paths-residual.md),
and Build runs it on every same-repository pull request. So no Build job that
checks out the branch may hold a write permission or leave the job token in
.git/config, and the coverage writes run where nothing from the branch does.
py-test computes main's coverage data read-only and hands the commit to the
`coverage` job as a git bundle; that handoff is run here against local
repositories with the workflow's own step scripts.

With that in place the agent stubs opt in: every call of the reusable
workflows that land agent commits passes `allow_build_config: true`.
"""

import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
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


def _actions(job: dict[str, Any]) -> list[str]:
    return [s["uses"].split("@")[0] for s in job["steps"] if "uses" in s]


def _writes(permissions: dict[str, str]) -> set[str]:
    return {scope for scope, level in permissions.items() if level == "write"}


def test_build_jobs_that_check_out_hold_no_write_permission() -> None:
    """Jobs that check out the branch are read-only and persist no credentials.

    The only writer checks nothing out and uses no action but
    download-artifact: it runs no code from the branch, directly or through
    an action (the coverage action, say, loads the project's coverage
    configuration and plugins).
    """
    workflow = _load(BUILD)
    assert workflow["permissions"] == {"contents": "read"}
    writers: dict[str, tuple[set[str], list[str]]] = {}
    for name, job in workflow["jobs"].items():
        permissions = job.get("permissions", workflow["permissions"])
        if "actions/checkout" in _actions(job):
            assert not _writes(permissions), name
            for step in job["steps"]:
                if step.get("uses", "").startswith("actions/checkout@"):
                    assert step["with"]["persist-credentials"] is False, name
        elif _writes(permissions):
            writers[name] = (_writes(permissions), _actions(job))
    assert writers == {"coverage": ({"contents"}, ["actions/download-artifact"])}


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


def _steps(job: str) -> dict[str, dict[str, Any]]:
    return {s.get("id", s.get("name")): s for s in _load(BUILD)["jobs"][job]["steps"]}


MAIN_PUSH = "github.event_name == 'push' && github.ref == 'refs/heads/main'"


def test_coverage_writes_run_nothing_from_the_pr() -> None:
    """The coverage comment and data branch are written outside branch code.

    py-test runs the coverage action read-only, on a PR for the comment and
    on main for the data branch; the workflow_run workflow posts the comment
    without a checkout, and the `coverage` job only pushes py-test's commit.
    """
    build = _load(BUILD)
    py_test = _steps("py-test")
    action = py_test["coverage_comment"]
    assert action["uses"].startswith("py-cov-action/python-coverage-comment-action@")
    assert " ".join(action["if"].split()) == (
        "matrix.python-version == '3.12' && (github.event_name == 'pull_request' "
        f"|| ({MAIN_PUSH}))"
    )
    stored = py_test["Store the coverage comment"]["with"]
    assert stored["name"] == "python-coverage-comment-action"
    assert stored["path"] == "python-coverage-comment-action.txt"

    main_only = f"matrix.python-version == '3.12' && {MAIN_PUSH}"
    names = list(py_test)
    handoff = [
        "Send the coverage data push to a local repository",
        "coverage_comment",
        "Store the coverage comment",
        "Bundle the coverage data commit",
        "Store the coverage data commit",
    ]
    assert names[names.index(handoff[0]) :] == handoff
    for name in (handoff[0], handoff[3], handoff[4]):
        assert py_test[name]["if"] == main_only, name
    branch = action["with"]["COVERAGE_DATA_BRANCH"]
    assert py_test[handoff[3]]["env"]["BRANCH"] == branch
    assert py_test[handoff[4]]["with"]["path"] == py_test[handoff[3]]["env"]["OUT"]

    coverage = build["jobs"]["coverage"]
    assert coverage["needs"] == "py-test"
    assert coverage["if"] == MAIN_PUSH
    download, push = coverage["steps"]
    assert download["with"] == {
        "name": py_test[handoff[4]]["with"]["name"],
        "path": "coverage-data",
    }
    assert push["env"]["BRANCH"] == branch

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


BRANCH = "python-coverage-comment-action-data"
GIT_ENV = {
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}

# A project-configured coverage plugin that would leave a marker if anything
# in the writer loaded the project's coverage configuration or its modules.
MARKER_PLUGIN = """import pathlib
pathlib.Path(__file__).with_name("PLUGIN-RAN").write_text("yes")
def coverage_init(reg, options):
    pass
"""


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        env={**os.environ, **GIT_ENV},
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _run_step(cwd: Path, job: str, name: str, env: dict[str, str]) -> None:
    subprocess.run(
        ["bash", "-euo", "pipefail", "-c", _steps(job)[name]["run"]],
        cwd=cwd,
        env={**os.environ, **GIT_ENV, **env},
        check=True,
    )


def _commit_files(repo: Path, files: dict[str, str], message: str) -> None:
    for path, content in files.items():
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(content)
        _git(repo, "add", path)
    _git(repo, "commit", "-q", "-m", message)


def _origin(tmp_path: Path, with_data_branch: bool) -> Path:
    seed = tmp_path / "seed"
    seed.mkdir()
    _git(seed, "init", "-q", "-b", "main")
    _commit_files(seed, {"README.md": "project\n"}, "main")
    if with_data_branch:
        _git(seed, "switch", "-q", "--orphan", BRANCH)
        _commit_files(seed, {"data.json": '{"coverage": 90}'}, "old data")
    origin = tmp_path / "origin.git"
    _git(tmp_path, "clone", "-q", "--bare", str(seed), str(origin))
    return origin


def _act_like_the_coverage_action(workspace: Path, change: str) -> None:
    """What the action's push mode does (storage.commit_operations, v3)."""
    if change == "new branch":
        _git(workspace, "switch", "-q", "--orphan", BRANCH)
    else:
        _git(workspace, "fetch", "-q", "origin", BRANCH)
        _git(workspace, "switch", "-q", BRANCH)
    if change != "unchanged":
        _commit_files(
            workspace,
            {
                "data.json": '{"coverage": 95}',
                "pyproject.toml": '[tool.coverage.run]\nplugins = ["marker"]\n',
                "marker.py": MARKER_PLUGIN,
            },
            "ci: Update coverage data",
        )
        _git(workspace, "push", "-q", "origin", BRANCH)
    _git(workspace, "switch", "-q", "main")


@pytest.mark.parametrize("change", ["changed", "unchanged", "new branch"])
def test_coverage_data_handoff_pushes_only_py_tests_commit(
    tmp_path: Path, change: str
) -> None:
    """py-test's commit reaches the data branch; the writer runs none of it."""
    origin = _origin(tmp_path, with_data_branch=change != "new branch")
    before = _git(
        origin, "for-each-ref", "--format=%(objectname)", f"refs/heads/{BRANCH}"
    )
    workspace = tmp_path / "workspace"
    _git(tmp_path, "clone", "-q", str(origin), str(workspace))
    runner_temp = tmp_path / "runner-temp"

    _run_step(
        workspace, "py-test", "Send the coverage data push to a local repository", {}
    )
    _act_like_the_coverage_action(workspace, change)
    _run_step(
        workspace,
        "py-test",
        "Bundle the coverage data commit",
        {"BRANCH": BRANCH, "OUT": str(runner_temp / "coverage-data")},
    )
    # The action pushed to the local repository, never to origin.
    assert (
        _git(origin, "for-each-ref", "--format=%(objectname)", f"refs/heads/{BRANCH}")
        == before
    )

    writer = tmp_path / "writer"
    writer.mkdir()
    subprocess.run(
        ["cp", "-R", str(runner_temp / "coverage-data"), str(writer)], check=True
    )
    _run_step(
        writer,
        "coverage",
        "Push the coverage data branch",
        {"BRANCH": BRANCH, "ORIGIN": str(origin), "GH_TOKEN": "not-a-token"},
    )

    after = _git(origin, "rev-parse", f"refs/heads/{BRANCH}")
    if change == "unchanged":
        assert after == before
    else:
        assert after == _git(workspace, "rev-parse", f"refs/heads/{BRANCH}")
        assert _git(origin, "show", f"{after}:data.json") == '{"coverage": 95}'
        if before:
            assert _git(origin, "rev-parse", f"{after}^") == before
    # Nothing was checked out in the writer, so nothing in the commit ran.
    assert sorted(p.name for p in writer.iterdir()) == (
        ["coverage-data"] if change == "unchanged" else ["coverage-data", "data.git"]
    )
    assert not list(tmp_path.rglob("PLUGIN-RAN"))


def test_coverage_data_push_is_fast_forward_only(tmp_path: Path) -> None:
    """A bundle that does not build on the data branch's tip is refused."""
    origin = _origin(tmp_path, with_data_branch=True)
    workspace = tmp_path / "workspace"
    _git(tmp_path, "clone", "-q", str(origin), str(workspace))
    _run_step(
        workspace, "py-test", "Send the coverage data push to a local repository", {}
    )
    _act_like_the_coverage_action(workspace, "changed")
    runner_temp = tmp_path / "runner-temp"
    _run_step(
        workspace,
        "py-test",
        "Bundle the coverage data commit",
        {"BRANCH": BRANCH, "OUT": str(runner_temp / "coverage-data")},
    )
    # Main moves the data branch on while this bundle waits.
    other = tmp_path / "other"
    _git(tmp_path, "clone", "-q", "--branch", BRANCH, str(origin), str(other))
    _commit_files(other, {"data.json": '{"coverage": 91}'}, "newer data")
    _git(other, "push", "-q", "origin", BRANCH)
    moved = _git(origin, "rev-parse", f"refs/heads/{BRANCH}")

    writer = tmp_path / "writer"
    writer.mkdir()
    subprocess.run(
        ["cp", "-R", str(runner_temp / "coverage-data"), str(writer)], check=True
    )
    with pytest.raises(subprocess.CalledProcessError):
        _run_step(
            writer,
            "coverage",
            "Push the coverage data branch",
            {"BRANCH": BRANCH, "ORIGIN": str(origin), "GH_TOKEN": "not-a-token"},
        )
    assert _git(origin, "rev-parse", f"refs/heads/{BRANCH}") == moved


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
