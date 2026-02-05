"""Solvers for Harbor tasks in Inspect AI."""

from pathlib import Path

from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import sandbox

from inspect_harbor._sandbox_utils import (
    cleanup_sandbox_directories,
    copy_directory_to_sandbox,
)


@solver
def oracle() -> Solver:
    """Solver that runs the reference solution script instead of using an LLM."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:  # noqa: ARG001
        solution_dir = state.metadata.get("solution_dir", "")
        solve_path = state.metadata.get("solve_path", "")
        harbor_config = state.metadata.get("harbor_config", {})
        solution_env = harbor_config.get("solution", {}).get("env", {})

        await copy_directory_to_sandbox(solution_dir, "/solution")

        # Calculate relative path for solve script
        solve_path_obj = Path(solve_path)
        solution_dir_obj = Path(solution_dir)
        relative_solve = solve_path_obj.relative_to(solution_dir_obj)
        container_solve_path = f"/solution/{relative_solve}".replace("\\", "/")

        await sandbox().exec(
            ["bash", "-l", container_solve_path],
            env=solution_env if solution_env else None,
        )

        await cleanup_sandbox_directories("/solution")

        return state

    return solve
