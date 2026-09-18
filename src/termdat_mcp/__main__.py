"""Entry point. Dual transport: stdio for Claude Desktop, Streamable HTTP for cloud hosting.

Beide Transporte bedienen beide Protokoll-Aeren, `2026-07-28` eingeschlossen —
das ist neu und war der Grund fuer den Wechsel. Gemessen am 18.09.2026 gegen
`mcp` 2.2.0, nicht aus dem Namen der Transporte geschlossen:

| Aufbau | `tools/list` mit `2026-07-28`-Envelope |
| --- | --- |
| stdio (`python -m termdat_mcp`) | HTTP-frei, Antwort `200`-aequivalent mit `resultType` |
| `sse_app()` (bis hierher) | `/sse` → 405, `/mcp` → 404, `/messages/` → 400 |
| `streamable_http_app()` | `/mcp` → 200, Ergebnis traegt `resultType` und `cacheScope` |

Die moderne Aera haengt an einer Weiche in
`StreamableHTTPSessionManager._handle_request`: traegt eine Anfrage einen
`MCP-Protocol-Version`-Header, der nicht zu den Handshake-Revisionen gehoert,
geht sie an `handle_modern_request`. In `mcp/server/sse.py` gibt es diese
Weiche nicht — kein Zweig, kein Import, keine Erwaehnung. Der SSE-Transport
konnte `2026-07-28` also nicht bloss schlecht, sondern gar nicht, und dieser
Server erreichte ueber das Netz nur die Handshake-Aera.

Das blieb unbemerkt, weil die Suite die moderne Aera nur ueber SDK-Konstanten
pruefte (`tests/test_protocol_version.py`) und stdio sie tatsaechlich bedient.
Eine Konstante, die `2026-07-28` sagt, sagt nichts darueber, ob eine Anfrage
dort ankommt. `tests/test_streamable_http.py` schickt jetzt beides durch den
zusammengebauten ASGI-Stack.

Nebenwirkung, die genauso zaehlt: `CACHE_HINTS` in `server.py` (SEP-2549)
erreichte ueber das Netz nie eine Leitung — `cacheScope` steht erst in der
Antwort der modernen Aera.
"""

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
    """Host/Origin allow-list for the HTTP transport (SEC-005, inbound half).

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


# Die Header, nach denen Spec 2026-07-28 eine Anfrage routet — in der
# Schreibweise des SDK (`mcp.shared.inbound`). Ein Browser darf einen nicht
# safelisteten Header gar nicht erst senden, wenn der Server ihn nicht in
# `Access-Control-Allow-Headers` nennt: ohne sie stirbt jede Cross-Origin-
# Anfrage am Preflight, vor dem ersten MCP-Byte. stdio- und Python-Clients
# kennen keinen Preflight und merken davon nichts — deshalb fiel es nicht auf.
CORS_ROUTING_HEADERS = ["Mcp-Method", "Mcp-Name", "Mcp-Protocol-Version"]

# Die Header der Handshake-Aera, die auf demselben Endpunkt weiterlebt.
# `Mcp-Session-Id` traegt die Session, `Last-Event-ID` nimmt einen
# abgerissenen SSE-Stream an der Stelle wieder auf, an der er abriss — beides
# Namen aus `mcp/server/streamable_http.py`, nicht aus dem Spec-Text
# abgeschrieben.
CORS_SESSION_HEADERS = ["Mcp-Session-Id", "Last-Event-ID"]

# GET oeffnet den Standalone-Stream, POST traegt die Anfrage, DELETE beendet
# die Session ausdruecklich. Das SDK antwortet auf alles andere mit
# `Allow: GET, POST, DELETE` — die Liste hier ist von dort abgelesen. DELETE
# fehlte, solange nur SSE bedient wurde: dort gibt es keine Session zum
# Beenden.
CORS_METHODS = ["GET", "POST", "DELETE"]

# Der Endpunkt der Streamable-HTTP-Spec. Der Default des SDK, hier benannt,
# weil die Tests und die READMEs denselben Pfad nennen muessen.
STREAMABLE_HTTP_PATH = "/mcp"


def build_http_app():
    """Baue die Streamable-HTTP-App samt CORS, ohne einen Socket zu binden.

    Herausgezogen aus `_run_http`, damit die CORS-Schicht pruefbar ist: solange
    Aufbau und `uvicorn.run` in derselben Funktion standen, liess sich die
    Freigabeliste nur lesen, nicht ausprobieren — und eine gelesene Liste kann
    vollstaendig aussehen und trotzdem nie an der Middleware ankommen. Dieselbe
    Trennung fahren die Schwester-Server im Portfolio.

    Bis zum 18.09.2026 baute diese Funktion `mcp.sse_app()`. Der SSE-Transport
    kennt die Weiche in die moderne Protokoll-Aera nicht (siehe Modul-Docstring),
    ueber das Netz war `2026-07-28` also unerreichbar. `streamable_http_app()`
    bedient beide Aeren auf demselben Pfad.
    """
    from starlette.middleware.cors import CORSMiddleware

    security = build_transport_security()
    if security is None:
        log.warning(
            "termdat_mcp.dns_rebinding_protection_off",
            host=settings.host,
            hint="Set TERMDAT_MCP_ALLOWED_HOSTS to the hostnames this server is "
            "reachable under; without it the Host header is not checked at all.",
        )
    # mcp 2.x: transport_security is a per-app kwarg, not a mutable setting.
    app = mcp.streamable_http_app(
        streamable_http_path=STREAMABLE_HTTP_PATH,
        transport_security=security,
        host=settings.host,
    )
    # Default-deny CORS: no browser origin is allowed unless TERMDAT_MCP_CORS_ORIGINS
    # lists it explicitly (never a wildcard in production).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=CORS_METHODS,
        allow_headers=["Content-Type", "Accept", *CORS_SESSION_HEADERS, *CORS_ROUTING_HEADERS],
        expose_headers=["Mcp-Session-Id"],
    )
    return app


def _warn_on_sse_alias(transport: str) -> None:
    """`TERMDAT_MCP_TRANSPORT=sse` bedient jetzt Streamable HTTP unter `/mcp`.

    Die Einstellung bleibt gueltig, der Pfad aendert sich — und eine Aenderung,
    die ein Deployment erst am toten Client bemerkt, gehoert laut ausgesprochen.
    Auf stderr **und** ins Log: wer den Container betreibt, liest oft nur eines
    von beidem.
    """
    if transport.lower() != "sse":
        return
    log.warning("termdat_mcp.sse_alias", path=STREAMABLE_HTTP_PATH)
    sys.stderr.write(
        "WARNING: TERMDAT_MCP_TRANSPORT=sse now serves Streamable HTTP on "
        f"{STREAMABLE_HTTP_PATH}, not SSE on /sse. The SSE transport could not "
        "carry MCP protocol revision 2026-07-28 at all. Point clients at "
        f"{STREAMABLE_HTTP_PATH} and set TERMDAT_MCP_TRANSPORT=streamable-http.\n"
    )


def _run_http() -> None:
    """Run the Streamable HTTP transport with explicit CORS for the routing headers (SDK-004)."""
    import uvicorn

    _warn_on_public_binding(settings.host)
    _warn_on_sse_alias(settings.transport)
    app = build_http_app()
    uvicorn.run(app, host=settings.host, port=settings.port, log_level=settings.log_level.lower())


def main() -> None:
    configure_logging(settings.log_level)
    if settings.is_network_transport:
        _run_http()
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
