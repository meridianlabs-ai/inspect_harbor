"""stdio -> HTTP MCP bridge, run inside a Harbor sandbox service.

Harbor tasks declare ``[[environment.mcp_servers]]`` that are reachable only on the compose network (for
example ``http://tau3-runtime:8000/mcp``). Inspect's ``mcp_server_sandbox()`` can only speak stdio to a
process it spawns in a sandbox, so this module is started in the service that hosts the server with
``python3 -c <source> <url> <transport>`` and proxies every tool of the HTTP server over stdio. It needs
``python3`` and the ``fastmcp`` package (>= 3) inside that service's image, which is what Harbor MCP
sidecars are built with; servers reachable from the Inspect process itself use Inspect's native HTTP /
SSE clients instead of this bridge.
"""

from __future__ import annotations

import sys


def main(url: str, transport: str = "streamable-http") -> None:
    """Serve every tool of the MCP server at ``url`` over stdio.

    ``transport`` is the Harbor ``[[environment.mcp_servers]].transport`` value
    (``sse`` or ``streamable-http``); it is passed explicitly because fastmcp
    would otherwise guess from the URL path.
    """
    try:
        # Only available inside the sandbox image, never in the inspect_harbor environment.
        from fastmcp import Client, FastMCP  # pyright: ignore[reportMissingImports]
        from fastmcp.client.transports import (  # pyright: ignore[reportMissingImports]
            SSETransport,
            StreamableHttpTransport,
        )
        from fastmcp.server.providers.proxy import (  # pyright: ignore[reportMissingImports]
            ProxyProvider,
        )
    except ImportError as exc:
        sys.exit(
            f"inspect_harbor MCP bridge: {exc}. The service hosting an MCP server "
            "must provide python3 and fastmcp>=3 so Inspect can reach the server."
        )

    make_transport = SSETransport if transport == "sse" else StreamableHttpTransport
    server = FastMCP(
        "harbor-mcp-bridge",
        providers=[ProxyProvider(lambda: Client(make_transport(url)))],
    )
    server.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main(*sys.argv[1:3])
