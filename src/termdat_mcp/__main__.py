"""Entry point. Dual transport: stdio for Claude Desktop, SSE for cloud hosting."""

from __future__ import annotations

import os
import sys

from .server import mcp


def _warn_on_public_binding(host: str) -> None:
    """Warn (on stderr) when binding to all interfaces outside a container.

    Binding to 0.0.0.0 on a dev machine exposes the server to the local network
    (NeighborJack). It is only appropriate inside a container, where the network
    namespace is isolated and the operator opts in explicitly via HOST.
    """
    if host not in ("0.0.0.0", "::"):
        return
    in_container = (
        os.path.exists("/.dockerenv")
        or bool(os.environ.get("KUBERNETES_SERVICE_HOST"))
        or bool(os.environ.get("RAILWAY_PROJECT_ID"))
        or bool(os.environ.get("RENDER"))
    )
    if not in_container:
        sys.stderr.write(
            f"WARNING: binding termdat-mcp to {host} outside a container exposes it to "
            "the local network. Use HOST=127.0.0.1 for local development.\n"
        )


def main() -> None:
    transport = os.environ.get("TERMDAT_MCP_TRANSPORT", "stdio").lower()
    if transport in ("sse", "streamable-http", "http"):
        # Default to loopback: 0.0.0.0 must be an explicit, deliberate opt-in
        # (set HOST=0.0.0.0 in the container). See SEC-016 / SECURITY.md.
        host = os.environ.get("HOST", "127.0.0.1")
        _warn_on_public_binding(host)
        mcp.settings.host = host
        mcp.settings.port = int(os.environ.get("PORT", "8000"))
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
