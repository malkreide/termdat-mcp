"""Entry point. Dual transport: stdio for Claude Desktop, SSE for cloud hosting."""

from __future__ import annotations

import os
import sys

from .logging_config import configure_logging, log
from .server import mcp, settings


def _warn_on_public_binding(host: str) -> None:
    """Warn (on stderr) when binding to all interfaces outside a container (SEC-016).

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
        log.warning("termdat_mcp.public_binding", host=host)
        sys.stderr.write(
            f"WARNING: binding termdat-mcp to {host} outside a container exposes it to "
            "the local network. Use HOST=127.0.0.1 for local development.\n"
        )


def _run_sse() -> None:
    """Run the SSE transport with explicit CORS for the MCP session header (SDK-004)."""
    import uvicorn
    from starlette.middleware.cors import CORSMiddleware

    _warn_on_public_binding(settings.host)
    app = mcp.sse_app()
    # Default-deny CORS: no browser origin is allowed unless TERMDAT_MCP_CORS_ORIGINS
    # lists it explicitly (never a wildcard in production). The MCP session header is
    # exposed and accepted so browser clients can round-trip it.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Mcp-Session-Id", "Content-Type"],
        expose_headers=["Mcp-Session-Id"],
    )
    uvicorn.run(app, host=settings.host, port=settings.port, log_level=settings.log_level.lower())


def main() -> None:
    configure_logging(settings.log_level)
    if settings.is_network_transport:
        _run_sse()
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
