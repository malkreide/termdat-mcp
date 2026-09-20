"""`serverInfo` traegt Version, Zweck und Herkunft — gemessen, nicht gelesen.

Befund vom 20.09.2026, gegen das Railway-Deployment per `initialize` erhoben
und hier offline nachgestellt: `serverInfo` war
`{"name": "termdat-mcp", "version": ""}`. `MCPServer` deckt `version` mit `""`
vor, `server.py` uebergab nichts, und das SDK setzt nichts Eigenes ein.
`version` ist in `Implementation` ein Pflichtfeld — der leere String erfuellt
es der Form nach und sagt nichts.

Warum das mehr ist als ein Schoenheitsfehler: In der modernen Aera
(`2026-07-28`) gibt es kein Handshake-Ergebnis. Der `_meta`-Stempel auf jeder
Antwort ist dort die einzige Stelle, an der ein Client erfaehrt, mit welcher
Fassung er spricht. Ein leeres Feld macht jede Fehlermeldung aus dem Betrieb
unzuordenbar.

Gemessen wird durch den zusammengebauten ASGI-Stack, nicht am
`MCPServer`-Objekt: Ein Blick auf ein Konstruktor-Argument zeigt, was
uebergeben wurde, nicht, was beim Client ankommt. Genau diese Unterscheidung
hatte im selben Repo schon einmal eine ganze Protokoll-Aera verdeckt (siehe
`tests/test_streamable_http.py`).

Die Erwartung kommt aus `importlib.metadata`, direkt aus den Metadaten der
installierten Distribution — **nicht** aus `termdat_mcp.__version__`. Gegen
`__version__` geprueft waeren beide Seiten derselbe Code, und der Test bliebe
gruen, waehrend die Aufloesung dahinter kaputt ist. Ein Literal scheidet
ohnehin aus: `scripts/check_version_sync.py` verbietet genau das.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as distribution_version
from typing import Any

import pytest
from mcp.types.version import LATEST_HANDSHAKE_VERSION, LATEST_MODERN_VERSION
from mcp_types import CLIENT_CAPABILITIES_META_KEY, PROTOCOL_VERSION_META_KEY, SERVER_INFO_META_KEY
from starlette.testclient import TestClient

from termdat_mcp.__main__ import STREAMABLE_HTTP_PATH, build_http_app
from termdat_mcp._version import DISTRIBUTION

# Wie in `tests/test_streamable_http.py`: der Host muss in der Allow-Liste
# stehen, die `build_transport_security()` aus dem Loopback-Default ableitet,
# sonst antwortet die Transport-Schicht mit 421 — auf jede Anfrage gleich.
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


def payload(text: str) -> dict[str, Any]:
    """Antwortkoerper lesen, gleich ob JSON oder SSE-gerahmt.

    Die Handshake-Aera antwortet SSE-gerahmt, die moderne mit nacktem JSON.
    Wer nur `response.json()` nimmt, misst die Rahmung statt der Antwort.
    """
    for line in text.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    return json.loads(text)


def handshake_server_info(client: TestClient) -> dict[str, Any]:
    """`serverInfo` aus dem `initialize`-Ergebnis — der Weg, auf dem der Befund
    gegen das Deployment erhoben wurde."""
    response = client.post(
        STREAMABLE_HTTP_PATH,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": LATEST_HANDSHAKE_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "termdat-mcp-tests", "version": "0"},
            },
        },
        headers=HEADERS,
    )
    assert response.status_code == 200, response.text
    return payload(response.text)["result"]["serverInfo"]


def modern_server_info(client: TestClient, method: str = "tools/list") -> dict[str, Any]:
    """Der `_meta`-Stempel der modernen Aera. Kein Handshake, der Envelope traegt alles."""
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": {
            "_meta": {
                PROTOCOL_VERSION_META_KEY: LATEST_MODERN_VERSION,
                CLIENT_CAPABILITIES_META_KEY: {},
            }
        },
    }
    response = client.post(
        STREAMABLE_HTTP_PATH,
        json=body,
        headers={**HEADERS, "MCP-Protocol-Version": LATEST_MODERN_VERSION, "Mcp-Method": method},
    )
    assert response.status_code == 200, response.text
    return payload(response.text)["result"]["_meta"][SERVER_INFO_META_KEY]


def installed_version() -> str:
    """Die Version der installierten Distribution, unabhaengig vom Paketcode gelesen.

    Ohne Installation (blosser Checkout mit `PYTHONPATH=src`) gibt es keine
    Metadaten. Der Test faellt dann nicht und behauptet auch nichts: er prueft
    den Fallback, den `_version` fuer genau diesen Fall fuehrt. Die CI
    installiert per `pip install -e ".[dev]"`, dort greift der strenge Zweig.
    """
    try:
        return distribution_version(DISTRIBUTION)
    except PackageNotFoundError:
        return "0.0.0+source"


def test_der_handshake_nennt_eine_version(client: TestClient) -> None:
    """Der Befund selbst: `initialize` lieferte `version: ""`."""
    info = handshake_server_info(client)
    assert info["name"] == "termdat-mcp"
    assert info["version"] == installed_version()
    assert info["version"] != ""


def test_der_stempel_der_modernen_aera_nennt_dieselbe_version(client: TestClient) -> None:
    """Dieselbe Zusicherung auf dem Weg, auf dem sie am meisten traegt.

    Hier gibt es kein `initialize`, dessen Ergebnis ein Client aufheben
    koennte — der Stempel ist der einzige Identitaetskanal. Eine Fassung, die
    nur den Handshake bedient, waere gruen und im Betrieb trotzdem stumm.
    """
    info = modern_server_info(client)
    assert info["name"] == "termdat-mcp"
    assert info["version"] == installed_version()
    assert info["version"] != ""


def test_beide_aeren_nennen_dieselbe_identitaet(client: TestClient) -> None:
    """Zwei Aeren mit verschiedener Identitaet waeren zwei Server unter einer
    Adresse. Die Gleichheit hier ist billiger zu pruefen als zu debuggen."""
    assert handshake_server_info(client) == modern_server_info(client)


def test_der_stempel_nennt_den_zweck(client: TestClient) -> None:
    """`description` ist das Feld, an dem ein Client ohne Werkzeugliste
    erkennt, worum es hier geht.

    Getrennt von `websiteUrl` geprueft, und das ist kein Formalismus: Eine
    erste Fassung pruefte beide in einer Zusicherung, und die Gegenprobe zeigte
    prompt, dass sie damit nicht unterscheiden kann, welches der beiden
    Argumente fehlt. Drei Argumente, drei Zusicherungen.
    """
    assert "TERMDAT" in modern_server_info(client)["description"]


def test_der_stempel_nennt_die_herkunft(client: TestClient) -> None:
    """`websiteUrl` — dieselbe Adresse, die `server.json` als `websiteUrl`
    fuehrt, hier aber aus den Paket-Metadaten statt aus einem zweiten Literal."""
    assert modern_server_info(client)["websiteUrl"].startswith("https://")


def test_die_angaben_stammen_aus_den_distributionsmetadaten() -> None:
    """Die Gegenprobe zur Quelle, nicht zum Transport.

    Die Tests oben blieben gruen, wenn jemand die drei Werte als Literale nach
    `server.py` schriebe — genau die Drift, gegen die `check_version_sync.py`
    existiert, und die es im Portfolio schon gegeben hat. Diese Zusicherung
    haelt die Werte gegen `importlib.metadata`, also gegen das, was
    `pyproject.toml` beim Bauen hinterlegt hat.

    Uebersprungen statt vakuum-gruen, wenn die Distribution nicht installiert
    ist: ohne Metadaten gibt es nichts zu vergleichen, und eine stillschweigend
    erfuellte Zusicherung waere schlechter als ein sichtbares Skip.
    """
    from importlib.metadata import metadata

    try:
        meta = metadata(DISTRIBUTION)
    except PackageNotFoundError:
        pytest.skip(f"{DISTRIBUTION} ist nicht installiert — keine Metadaten zum Vergleich")

    from termdat_mcp._version import __homepage__, __summary__

    assert __summary__ == meta["Summary"]
    homepage = next(
        url.strip()
        for label, _, url in (e.partition(",") for e in meta.get_all("Project-URL") or ())
        if label.strip().lower() == "homepage"
    )
    assert __homepage__ == homepage
