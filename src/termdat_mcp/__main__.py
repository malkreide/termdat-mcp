"""Entry point. Dual transport: stdio for Claude Desktop, SSE for cloud hosting."""

from __future__ import annotations

import os

from .server import mcp


def main() -> None:
    transport = os.environ.get("TERMDAT_MCP_TRANSPORT", "stdio").lower()
    if transport in ("sse", "streamable-http", "http"):
        mcp.settings.host = os.environ.get("HOST", "0.0.0.0")
        mcp.settings.port = int(os.environ.get("PORT", "8000"))
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
