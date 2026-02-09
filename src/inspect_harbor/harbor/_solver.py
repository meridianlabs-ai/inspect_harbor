"""Solvers for Harbor tasks in Inspect AI."""

from pathlib import Path

from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import sandbox

from inspect_harbor.harbor._sandbox_utils import (
    cleanup_sandbox_env_vars,
    copy_directory_to_sandbox,
    resolve_env_vars,
)


class CopySolutionDirError(Exception):
    """Raised when failing to copy the solution directory to the sandbox."""


@solver
def oracle() -> Solver:
    """Solver that runs the reference solution script instead of using an LLM."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:  # noqa: ARG001
        solution_dir = state.metadata.get("solution_dir")
        solve_path = state.metadata.get("solve_path")

        if not solution_dir:
            raise CopySolutionDirError("solution_dir not found in metadata")
        if not solve_path:
            raise CopySolutionDirError("solve_path not found in metadata")

        solution_dir = Path(solution_dir)
        solve_path = Path(solve_path)

        solution_env_raw = state.metadata.get("solution_env", {})
        solution_env = resolve_env_vars(solution_env_raw) if solution_env_raw else None

        if not solution_dir.exists():
            raise CopySolutionDirError(f"Solution directory not found: {solution_dir}")

        try:
            await copy_directory_to_sandbox(solution_dir, "/solution")
        except Exception as e:
            raise CopySolutionDirError(
                f"Failed to copy solution to sandbox: {e}"
            ) from e

        try:
            relative_solve = solve_path.relative_to(solution_dir)
            container_solve_path = f"/solution/{relative_solve}".replace("\\", "/")
        except ValueError as e:
            raise CopySolutionDirError(
                f"Solve path {solve_path} is not relative to solution directory {solution_dir}"
            ) from e

        await sandbox().exec(
            ["bash", "-l", container_solve_path],
            env=solution_env,
        )

        # We don't cleanup /solution directory: some tasks require the scorer to access
        # files written by the oracle to this directory (e.g., harbor-datasets/ds1000).
        # Reference: https://github.com/laude-institute/harbor-datasets/blob/2f82ff5/datasets/ds1000/0/solution/solve.sh
        if solution_env:
            await cleanup_sandbox_env_vars(list(solution_env.keys()))

        return state

    return solve
