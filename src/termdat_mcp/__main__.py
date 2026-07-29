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


def build_transport_security(cfg=None):
    """Host/Origin allow-list for the SSE transport (SEC-005, inbound half).

    The SDK leaves DNS-rebinding protection OFF while ``transport_security`` is
    unset — its own source says "If not specified, disable DNS rebinding
    protection by default for backwards compatibility". Unset therefore means
    no Host and no Origin validation at all.

    Returns ``None`` when no allow-list can be derived: a non-loopback bind with
    no ``TERMDAT_MCP_ALLOWED_HOSTS``. The server is then reached under a service
    or public DNS name this process does not know, and a guessed list would
    reject every real request with HTTP 421. The caller warns instead.
    """
    from mcp.server.transport_security import TransportSecuritySettings

    cfg = cfg if cfg is not None else settings
    port = cfg.port
    loopback = {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}
    if cfg.allowed_hosts:
        # Loopback stays reachable for container health checks and debugging.
        hosts = set(cfg.allowed_hosts) | loopback
    elif cfg.host in ("127.0.0.1", "localhost", "::1"):
        hosts = loopback | {f"{cfg.host}:{port}"}
    else:
        return None

    # CORS here is default-deny, so allowed_origins would normally be just the
    # derived loopback set. Any origin the operator did allow must also pass the
    # transport check, otherwise the server rejects exactly the browser clients
    # CORS permits. "*" is matched literally by the SDK (only a trailing ":*"
    # port wildcard exists), so it is not copied across.
    origins = {o for o in cfg.cors_allow_origins if o != "*"}
    origins |= {f"http://{h}" for h in hosts}
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=sorted(hosts),
        allowed_origins=sorted(origins),
    )


def _run_sse() -> None:
    """Run the SSE transport with explicit CORS for the MCP session header (SDK-004)."""
    import uvicorn
    from starlette.middleware.cors import CORSMiddleware

    _warn_on_public_binding(settings.host)
    security = build_transport_security()
    if security is None:
        log.warning(
            "termdat_mcp.dns_rebinding_protection_off",
            host=settings.host,
            hint="Set TERMDAT_MCP_ALLOWED_HOSTS to the hostnames this server is "
            "reachable under; without it the Host header is not checked at all.",
        )
    mcp.settings.transport_security = security
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
