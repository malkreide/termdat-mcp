"""CORS muss die Header durchlassen, nach denen Spec 2026-07-28 routet.

Seit `2026-07-28` traegt jede Streamable-HTTP-Anfrage `Mcp-Method`, `Mcp-Name`
und `Mcp-Protocol-Version`; das SDK liest sie in `mcp.shared.inbound`. Die
Freigabeliste hier war fuer die aeltere Form geschrieben: sie nannte
`Mcp-Session-Id`, den Session-Header, der fuer sich genommen keine Anfrage routet.

Ein Browser darf einen nicht safelisteten Header gar nicht erst senden, wenn der
Server ihn nicht in `Access-Control-Allow-Headers` nennt. Der Preflight endete
mit 400, und zwar bevor ein einziges MCP-Byte floss. stdio- und Python-Clients
kennen keinen Preflight und liefen weiter — deshalb war die Suite gruen,
waehrend jeder Browser-Client ausgesperrt war.

Geprueft mit echten Anfragen gegen die zusammengebaute App. Ein Blick in
`CORS_ROUTING_HEADERS` waere kein Test: die Liste kann vollstaendig sein und
trotzdem nie an der Middleware ankommen.
`Mcp-Session-Id` gehoert dabei weiterhin auf die Liste. Eine fruehere Fassung
dieses Docstrings nannte ihn den Header einer Mechanik, die `2026-07-28`
abgeschafft habe — das stimmt nicht, und der Code hier hat es nie behauptet:
derselbe Server gibt den Header in `expose_headers` frei, damit ein
Browser-Client ihn lesen kann.

Nachgemessen statt aus Spec-Text geschlossen: `MCP_SESSION_ID_HEADER` steht
unveraendert in `mcp/server/streamable_http.py`, und ein echter `initialize`
durch den zusammengebauten ASGI-Stack bekommt eine Session-ID im
Antwort-Header zurueck. `mcp` 2.x bedient beide Protokoll-Aeren; die Session
gehoert zur Handshake-Aera, und die ist es, in der heutige Clients sprechen.
Die Freigabeliste war also nicht falsch besetzt, sondern unvollstaendig.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from starlette.testclient import TestClient

from termdat_mcp.__main__ import (
    CORS_METHODS,
    CORS_ROUTING_HEADERS,
    CORS_SESSION_HEADERS,
    STREAMABLE_HTTP_PATH,
    build_http_app,
    settings,
)
from termdat_mcp.server import mcp

ORIGIN = "https://client.example"
ENDPOINT = STREAMABLE_HTTP_PATH


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Mit Lifespan, nicht bloss zusammengebaut.

    Ein Preflight kommt nicht ueber die Middleware hinaus und laeuft auch ohne
    — eine echte Anfrage nicht: `StreamableHTTPSessionManager` legt seine
    Task-Gruppe im Lifespan an und antwortet sonst mit `RuntimeError`. Die
    Fixture ohne `with` liess also genau die Tests scheitern, die mehr pruefen
    als den Preflight.
    """
    monkeypatch.setattr(settings, "cors_allow_origins", [ORIGIN])
    with TestClient(build_http_app()) as c:
        yield c


def preflight(client: TestClient, announced: str, method: str = "POST"):
    """Ein Preflight, der `announced` als Wunschheader anmeldet.

    Der Header muss auf der Anfrage stehen, nicht nur in der Antwort gelesen
    werden: Starlette beantwortet einen Preflight, der einen nicht erlaubten
    Header nennt, mit 400 — das ist die Ablehnung, um die es geht.
    """
    return client.options(
        ENDPOINT,
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": announced,
        },
    )


@pytest.mark.parametrize("header", CORS_ROUTING_HEADERS)
def test_preflight_laesst_jeden_routing_header_durch(client: TestClient, header: str) -> None:
    """Einzeln geprueft: eine gemeinsame Anmeldung koennte durchgehen, obwohl
    nur einer der drei freigegeben ist."""
    resp = preflight(client, header)
    assert resp.status_code == 200, f"Preflight mit {header} wurde abgewiesen"
    assert header.lower() in resp.headers["access-control-allow-headers"].lower()


def test_preflight_laesst_die_routing_header_gemeinsam_durch(client: TestClient) -> None:
    """Was ein Browser tatsaechlich schickt: alle drei auf derselben Anfrage."""
    resp = preflight(client, ", ".join(h.lower() for h in CORS_ROUTING_HEADERS))
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == ORIGIN


def test_ein_nicht_freigegebener_header_wird_weiterhin_abgewiesen(client: TestClient) -> None:
    """Negativkontrolle. Ohne sie waeren die Tests oben auch gegen eine
    CORS-Schicht gruen, die jeden Header durchwinkt — ein anderer Fehler, keine
    Behebung."""
    assert preflight(client, "x-nicht-erlaubt").status_code == 400


def test_die_liste_nennt_die_header_die_das_sdk_liest() -> None:
    """Gegen die Konstanten des SDK gehalten statt gegen abgeschriebenen
    Spec-Text: `mcp.shared.inbound` ist, womit der Server die Anfrage
    tatsaechlich liest. Eine Umbenennung dort faellt hier auf, statt als
    Browser-Client, der ohne erkennbaren Grund nicht mehr verbindet."""
    from mcp.shared.inbound import (
        MCP_METHOD_HEADER,
        MCP_NAME_HEADER,
        MCP_PROTOCOL_VERSION_HEADER,
    )

    listed = {h.lower() for h in CORS_ROUTING_HEADERS}
    required = {MCP_METHOD_HEADER, MCP_NAME_HEADER, MCP_PROTOCOL_VERSION_HEADER}
    assert required <= listed, f"nicht freigegeben: {sorted(required - listed)}"


async def test_kein_tool_schema_verlangt_einen_mcp_param_header() -> None:
    """`Mcp-Param-*` traegt ein Tool-Argument als HTTP-Header, angemeldet ueber
    eine `x-mcp-header`-Annotation im Input-Schema. CORS kennt keinen
    Praefix-Wildcard, das erste Tool mit so einer Annotation muss den konkreten
    Header einzeln freigeben. Bisher tut es keines — dieser Test ist die
    Erinnerung an dem Tag, an dem sich das aendert."""
    offenders = [t.name for t in await mcp.list_tools() if "x-mcp-header" in str(t.input_schema)]
    assert not offenders, f"{offenders} brauchen einen Mcp-Param-*-Eintrag in der Freigabeliste"


@pytest.mark.parametrize("header", CORS_SESSION_HEADERS)
def test_die_session_header_sind_weiterhin_freigegeben(client: TestClient, header: str) -> None:
    """Haelt die Aussage im Docstring oben, statt sie nur zu behaupten.

    Eine fruehere Fassung nannte `Mcp-Session-Id` den Header einer Mechanik,
    die `2026-07-28` abgeschafft habe. Das SDK sagt etwas anderes, und dieser
    Test sagt es mit: die Konstante existiert, und der Preflight laesst den
    Header durch. `Last-Event-ID` gehoert seit dem Wechsel auf Streamable HTTP
    dazu — er nimmt einen abgerissenen Stream wieder auf, und ohne Freigabe
    beginnt ein Browser-Client nach jedem Abriss von vorn.

    Faellt er, ist eines von beidem passiert — die Mechanik ist tatsaechlich
    weg, oder jemand hat den Header aus der Freigabeliste genommen. Beides ist
    eine bewusste Entscheidung und keine, die still passieren darf.
    """
    resp = preflight(client, header)
    assert resp.status_code == 200, f"{header} wird am Preflight abgewiesen"
    assert header.lower() in resp.headers["access-control-allow-headers"].lower()


def test_die_session_header_heissen_wie_im_sdk() -> None:
    """Gegen die Konstanten gehalten, nicht gegen abgeschriebenen Spec-Text."""
    from mcp.server.streamable_http import LAST_EVENT_ID_HEADER, MCP_SESSION_ID_HEADER

    listed = {h.lower() for h in CORS_SESSION_HEADERS}
    assert {MCP_SESSION_ID_HEADER, LAST_EVENT_ID_HEADER} <= listed


@pytest.mark.parametrize("method", CORS_METHODS)
def test_der_preflight_laesst_jede_methode_des_endpunkts_durch(client: TestClient, method: str) -> None:
    """Streamable HTTP beantwortet GET, POST und DELETE — das SDK sagt es
    selbst im `Allow`-Header seiner 405-Antwort.

    `DELETE` beendet eine Session ausdruecklich und fehlte in der Freigabeliste,
    solange nur SSE bedient wurde: dort gibt es keine Session zum Beenden. Ohne
    Freigabe laesst ein Browser die Session stattdessen auslaufen.
    """
    resp = preflight(client, "content-type", method=method)
    assert resp.status_code == 200, f"Preflight fuer {method} wurde abgewiesen"
    assert method.lower() in resp.headers["access-control-allow-methods"].lower()


def test_die_methodenliste_deckt_ab_was_der_endpunkt_annimmt(client: TestClient) -> None:
    """Der Test, der die Liste nicht bloss sich selbst vorhaelt.

    Der parametrierte Test darueber zieht seine Faelle aus `CORS_METHODS` — wer
    dort `DELETE` streicht, streicht damit auch den Fall, der es geprueft
    haette. Genau so verschwand `DELETE` unbemerkt, als nur SSE bedient wurde.
    Diese Zusicherung fragt stattdessen den Endpunkt selbst: das SDK nennt im
    `Allow`-Header seiner 405-Antwort, was es annimmt.
    """
    allow = client.put(ENDPOINT, headers={"Host": "127.0.0.1:8000"})
    assert allow.status_code == 405

    accepted = {m.strip().upper() for m in allow.headers["allow"].split(",")}
    assert accepted <= {m.upper() for m in CORS_METHODS}, (
        f"der Endpunkt nimmt {sorted(accepted)} an, CORS gibt nur {sorted(CORS_METHODS)} frei"
    )


def test_eine_nicht_freigegebene_methode_wird_abgewiesen(client: TestClient) -> None:
    """Negativkontrolle zur Methodenliste: ohne sie waere der Test oben auch
    gegen eine Schicht gruen, die jede Methode durchwinkt."""
    assert preflight(client, "content-type", method="PATCH").status_code == 400


def test_die_session_id_bleibt_fuer_den_browser_lesbar(client: TestClient) -> None:
    """`expose_headers` ist die andere Richtung: ohne sie darf JavaScript den
    Antwortheader nicht lesen, obwohl der Server ihn schickt — und der Client
    haette keine Session, mit der er weitermachen koennte."""
    resp = client.options(
        ENDPOINT,
        headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST"},
    )
    assert resp.status_code == 200
    from mcp.server.streamable_http import MCP_SESSION_ID_HEADER

    post = client.post(
        ENDPOINT,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "termdat-mcp-tests", "version": "0"},
            },
        },
        headers={
            "Origin": ORIGIN,
            "Host": "127.0.0.1:8000",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    assert post.headers.get(MCP_SESSION_ID_HEADER)
    assert MCP_SESSION_ID_HEADER in post.headers["access-control-expose-headers"].lower()
