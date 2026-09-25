"""stdio -> HTTP MCP bridge, run inside a Harbor sandbox service.

Harbor tasks declare ``[[environment.mcp_servers]]`` that are reachable only on the compose network (for
example ``http://tau3-runtime:8000/mcp``). Inspect's ``mcp_server_sandbox()`` can only speak stdio to a
process it spawns in a sandbox, so this module is started there with ``python3 -c <source> <url>`` and
proxies every tool of the HTTP server over stdio. It needs the ``fastmcp`` package (>= 4) inside the
container, which is what Harbor MCP sidecars are built with.
"""

from __future__ import annotations

import sys


def main(url: str) -> None:
    """Serve every tool of the MCP server at ``url`` over stdio."""
    # Only available inside the sandbox image, never in the inspect_harbor environment.
    from fastmcp import Client, FastMCP  # pyright: ignore[reportMissingImports]
    from fastmcp.server.providers.proxy import (  # pyright: ignore[reportMissingImports]
        ProxyProvider,
    )

    server = FastMCP(
        "harbor-mcp-bridge",
        providers=[ProxyProvider(lambda: Client(url))],
    )
    server.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main(sys.argv[1])
