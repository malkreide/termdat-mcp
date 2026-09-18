"""Beide Protokoll-Aeren, gemessen durch den zusammengebauten ASGI-Stack.

`tests/test_protocol_version.py` pinnt die Revisionen gegen SDK-Konstanten. Das
ist die schwaechere Form und war lange die einzige: eine Konstante, die
`2026-07-28` sagt, sagt nichts darueber, ob eine Anfrage dort ankommt. Genau
diese Luecke hatte den Befund verdeckt, aus dem dieses Modul entstand — ueber
das Netz bediente der Server nur die Handshake-Aera, weil `mcp.sse_app()` die
Weiche in die moderne Aera nicht kennt (`mcp/server/sse.py` erwaehnt sie
nirgends; sie steht in `StreamableHTTPSessionManager._handle_request`). stdio
bediente sie die ganze Zeit, die Suite war gruen, und niemand hatte eine
Anfrage durch den Netz-Transport geschickt.

Hier laeuft deshalb alles ueber echte HTTP-Anfragen gegen `build_http_app()`.

Was die Tests hier **nicht** hergeben: dass ein realer Client zufrieden ist.
`TestClient` spricht ASGI in-process, ohne Proxy, ohne Browser, ohne Netz. Der
Unterschied ist genau die Schicht, in der der CORS-Preflight sitzt — den prueft
`tests/test_cors.py`, ebenfalls gegen diese App.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import pytest
from mcp.types.version import LATEST_HANDSHAKE_VERSION, LATEST_MODERN_VERSION

# Die `_meta`-Schluessel des Pro-Request-Envelopes. Aus `mcp_types` gelesen
# statt abgeschrieben: eine Umbenennung dort faellt hier als ImportError auf,
# nicht als stiller Rung-1-Fehlschlag, der wie ein Serverfehler aussieht.
from mcp_types import CLIENT_CAPABILITIES_META_KEY, PROTOCOL_VERSION_META_KEY
from starlette.testclient import TestClient

from termdat_mcp.__main__ import STREAMABLE_HTTP_PATH, build_http_app

# Der Host muss in der Allow-Liste stehen, die `build_transport_security()` aus
# dem Loopback-Default ableitet — sonst antwortet die Transport-Schicht mit 421,
# und zwar auf jede Anfrage gleich. Das saehe wie ein Protokollbefund aus und
# waere keiner.
HOST = "127.0.0.1:8000"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "Host": HOST,
}


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(build_http_app()) as c:
        yield c


def envelope(
    version: str, method: str = "tools/list", params: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Eine Anfrage der modernen Aera: kein Handshake, der Envelope traegt alles."""
    body_params = dict(params or {})
    body_params["_meta"] = {
        PROTOCOL_VERSION_META_KEY: version,
        CLIENT_CAPABILITIES_META_KEY: {},
    }
    return {"jsonrpc": "2.0", "id": 1, "method": method, "params": body_params}


def post_modern(client: TestClient, body: dict[str, Any], **extra: str):
    """POST mit den Routing-Headern, die zum Body passen.

    Die Header muessen mit dem Body uebereinstimmen, sonst antwortet der
    Klassifikator mit `-32020` (HEADER_MISMATCH), bevor irgendetwas geprueft
    wird, was dieser Test meint.
    """
    version = body["params"]["_meta"][PROTOCOL_VERSION_META_KEY]
    headers = {**HEADERS, "MCP-Protocol-Version": version, "Mcp-Method": body["method"], **extra}
    return client.post(STREAMABLE_HTTP_PATH, json=body, headers=headers)


def sse_or_json(text: str) -> dict[str, Any]:
    """Antwortkoerper lesen, gleich ob JSON oder SSE-gerahmt.

    Die Handshake-Aera antwortet SSE-gerahmt (`json_response=False`), die
    moderne Aera mit nacktem JSON. Wer nur `response.json()` nimmt, misst die
    Rahmung und nicht die Antwort.
    """
    for line in text.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    return json.loads(text)


# --------------------------------------------------------------------------
# Moderne Aera: 2026-07-28
# --------------------------------------------------------------------------


def test_die_moderne_aera_wird_ueber_http_beantwortet(client: TestClient) -> None:
    """Der lasttragende Test dieses Moduls.

    Gegen `mcp.sse_app()` war dieselbe Anfrage 404 (`/mcp` existierte dort
    nicht) bzw. 405 (`/sse` nimmt kein POST). Faellt dieser Test, ist der
    Netz-Transport wieder einer, der `2026-07-28` nicht traegt.
    """
    resp = post_modern(client, envelope(LATEST_MODERN_VERSION))

    assert resp.status_code == 200, resp.text
    result = sse_or_json(resp.text)["result"]
    assert [t["name"] for t in result["tools"]], "die moderne Antwort traegt keine Werkzeuge"


def test_die_moderne_antwort_traegt_den_pflicht_resulttype(client: TestClient) -> None:
    """Spec 2026-07-28: `Result.resultType` ist Pflicht. Das trennt eine echte
    Antwort der modernen Aera von einer durchgereichten Legacy-Antwort."""
    result = sse_or_json(post_modern(client, envelope(LATEST_MODERN_VERSION)).text)["result"]

    assert result["resultType"] == "complete"


def test_der_cache_hinweis_erreicht_erst_hier_die_leitung(client: TestClient) -> None:
    """SEP-2549 kam ueber das Netz bisher nirgends an.

    `server.py` setzt `CACHE_HINTS` seit laengerem, und `tests/test_cache_hints.py`
    belegt den Hinweis ueber eine In-Process-`ClientSession`. Ueber HTTP war er
    trotzdem tot: Die Handshake-Aera siebt `ttlMs`/`cacheScope` aus dem Resultat
    (ihr Schema kennt die Felder nicht), und die moderne Aera war unerreichbar.
    Gemessen, nicht geschlossen — die Gegenprobe steht im Test darunter.
    """
    from termdat_mcp.server import LIST_CACHE_TTL_MS

    result = sse_or_json(post_modern(client, envelope(LATEST_MODERN_VERSION)).text)["result"]

    assert result["ttlMs"] == LIST_CACHE_TTL_MS
    assert result["cacheScope"] == "public"


def test_eine_unbekannte_moderne_revision_wird_benannt_abgewiesen(client: TestClient) -> None:
    """`-32022` ist der eine Code, von dem aushandelnde Clients *nicht*
    zurueckfallen — die Antwort muss deshalb sagen, was der Server kann."""
    resp = post_modern(client, envelope("2027-01-01"))

    assert resp.status_code == 400
    error = sse_or_json(resp.text)["error"]
    assert error["code"] == -32022
    assert error["data"]["supported"] == [LATEST_MODERN_VERSION]
    assert error["data"]["requested"] == "2027-01-01"


def test_ohne_envelope_ist_die_moderne_aera_nicht_erreichbar(client: TestClient) -> None:
    """Negativkontrolle zur ersten Zusicherung oben.

    Ohne sie waere `test_die_moderne_aera_wird_ueber_http_beantwortet` auch
    gegen einen Server gruen, der jeden POST irgendwie beantwortet. Der
    Envelope ist es, der die Aera oeffnet — fehlt er, kommt Rung 1 des
    Klassifikators.
    """
    resp = client.post(
        STREAMABLE_HTTP_PATH,
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        headers={**HEADERS, "MCP-Protocol-Version": LATEST_MODERN_VERSION, "Mcp-Method": "tools/list"},
    )

    assert resp.status_code == 400
    assert sse_or_json(resp.text)["error"]["code"] == -32602


def test_ein_header_der_dem_body_widerspricht_wird_abgewiesen(client: TestClient) -> None:
    """`Mcp-Method` ist kein Schmuck: nach ihm routet ein Proxy, ohne den Body
    zu lesen. Weicht er ab, ist die Anfrage mit sich selbst uneins."""
    resp = post_modern(client, envelope(LATEST_MODERN_VERSION), **{"Mcp-Method": "prompts/list"})

    assert resp.status_code == 400
    assert sse_or_json(resp.text)["error"]["code"] == -32020


# --------------------------------------------------------------------------
# Handshake-Aera: was heutige Clients sprechen
# --------------------------------------------------------------------------


def initialize(client: TestClient, asked: str):
    return client.post(
        STREAMABLE_HTTP_PATH,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": asked,
                "capabilities": {},
                "clientInfo": {"name": "termdat-mcp-tests", "version": "0"},
            },
        },
        headers=HEADERS,
    )


@pytest.mark.parametrize("asked", ["2024-11-05", "2025-03-26", "2025-06-18", LATEST_HANDSHAKE_VERSION])
def test_der_handshake_antwortet_mit_der_angefragten_revision(client: TestClient, asked: str) -> None:
    """Die READMEs nennen die Spanne `2024-11-05` … `2025-11-25`. Bisher stand
    diese Aussage nur dort; hier wird sie Feld fuer Feld nachgefahren."""
    resp = initialize(client, asked)

    assert resp.status_code == 200, resp.text
    assert sse_or_json(resp.text)["result"]["protocolVersion"] == asked


def test_eine_zu_neue_anfrage_bekommt_die_obergrenze(client: TestClient) -> None:
    """Der Fall, den die READMEs «oder mit der Obergrenze» nennen.

    Ein Client, der `2026-07-28` per `initialize` verlangt, landet hier — die
    moderne Aera erreicht man nicht ueber den Handshake, sondern ueber den
    Envelope. Ohne diesen Test liesse sich das nicht von «der Server kann die
    moderne Aera» unterscheiden.
    """
    resp = initialize(client, LATEST_MODERN_VERSION)

    assert sse_or_json(resp.text)["result"]["protocolVersion"] == LATEST_HANDSHAKE_VERSION


def test_der_handshake_vergibt_eine_session(client: TestClient) -> None:
    """Die Session gehoert zur Handshake-Aera und ist der Grund, warum
    `Mcp-Session-Id` weiterhin in der CORS-Freigabeliste steht."""
    assert initialize(client, LATEST_HANDSHAKE_VERSION).headers.get("mcp-session-id")


def test_die_handshake_aera_siebt_den_cache_hinweis_aus(client: TestClient) -> None:
    """Die Gegenprobe zu `test_der_cache_hinweis_erreicht_erst_hier_die_leitung`.

    Ohne sie liesse sich «der Hinweis steht in der modernen Antwort» nicht von
    «der Hinweis steht in jeder Antwort» unterscheiden — und damit nicht
    belegen, dass er ueber das Netz bisher nirgends ankam.
    """
    started = initialize(client, LATEST_HANDSHAKE_VERSION)
    session = {
        "mcp-session-id": started.headers["mcp-session-id"],
        "MCP-Protocol-Version": LATEST_HANDSHAKE_VERSION,
    }
    client.post(
        STREAMABLE_HTTP_PATH,
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        headers={**HEADERS, **session},
    )

    resp = client.post(
        STREAMABLE_HTTP_PATH,
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        headers={**HEADERS, **session},
    )
    result = sse_or_json(resp.text)["result"]

    assert "ttlMs" not in result
    assert "cacheScope" not in result
    assert result["tools"], "ohne Werkzeuge belegt die Abwesenheit der Felder nichts"


# --------------------------------------------------------------------------
# Der Wechsel selbst
# --------------------------------------------------------------------------


def test_der_alte_sse_pfad_ist_weg(client: TestClient) -> None:
    """Sagt, was das Deployment merkt. `/sse` und `/messages/` sind fort — dass
    das laut passiert, sichert `test_sse_alias_warnt` unten.

    POST, nicht GET: ein `GET /sse` gegen die alte App oeffnet einen Stream,
    der nicht endet. Die Gegenprobe zu diesem Modul (Implementierung auf
    `sse_app()` zurueckgedreht) haette damit nicht rot gemeldet, sondern
    gehangen — und ein haengender Test sagt niemandem, was fehlt.
    """
    for path in ("/sse", "/messages/"):
        assert client.post(path, json={}, headers=HEADERS).status_code == 404, path


def test_sse_alias_warnt(capsys: pytest.CaptureFixture[str]) -> None:
    """`TERMDAT_MCP_TRANSPORT=sse` laeuft weiter, bedient aber `/mcp`.

    Eine Einstellung, die bleibt, waehrend sich der Pfad darunter aendert, ist
    genau die Aenderung, die ein Betrieb erst am toten Client bemerkt.
    """
    from termdat_mcp.__main__ import _warn_on_sse_alias

    _warn_on_sse_alias("sse")
    warned = capsys.readouterr().err
    assert STREAMABLE_HTTP_PATH in warned
    assert "2026-07-28" in warned

    _warn_on_sse_alias("streamable-http")
    assert capsys.readouterr().err == "", "der Alias-Hinweis erscheint auch ohne Alias"
