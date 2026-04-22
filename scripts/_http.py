"""Shared HTTP helper for the generator and validator scripts.

We shell out to curl instead of using urllib because the Harbor registry
payload (~13MB) intermittently trips `http.client.IncompleteRead` when
fetched via urllib. curl's built-in retry/resume path handles that
cleanly.
"""

from __future__ import annotations

import subprocess
import sys


def curl_get(url: str, *, max_time: int = 120, retries: int = 5) -> bytes:
    """Fetch `url` with curl and return the response body as bytes.

    Raises:
        SystemExit: if curl is not on PATH, or if curl exits non-zero
            after all retries. Both paths are fatal for our scripts,
            so we exit with a clear message rather than propagating
            exceptions that callers would have to translate.
    """
    try:
        result = subprocess.run(
            [
                "curl",
                "--silent",
                "--show-error",
                "--location",
                "--fail",
                "--retry",
                str(retries),
                "--retry-delay",
                "2",
                "--max-time",
                str(max_time),
                url,
            ],
            capture_output=True,
            check=True,
        )
    except FileNotFoundError:
        sys.exit("error: curl is required but not installed on PATH")
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
        sys.exit(f"error: curl failed (exit {exc.returncode}) fetching {url}: {stderr}")
    return result.stdout
