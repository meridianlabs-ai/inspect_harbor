"""Solvers for Harbor tasks in Inspect AI."""

from pathlib import Path

from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import sandbox

from inspect_harbor.harbor._sandbox_utils import (
    cleanup_sandbox_directories,
    copy_directory_to_sandbox,
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

        harbor_config = state.metadata.get("harbor_config", {})
        solution_env = harbor_config.get("solution", {}).get("env", {})

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
            env=solution_env if solution_env else None,
        )

        await cleanup_sandbox_directories("/solution")

        return state

    return solve
