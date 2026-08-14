"""Jeder externe Endpunkt, gefahren aus einer aufgezeichneten Antwort.

Die handgeschriebenen Stubs im Rest der Suite pruefen die *Fehler*-Pfade — ein
404, ein Timeout, ein maskierter 4xx —, die sich nicht auf Zuruf aufzeichnen
lassen und als Erfindung in Ordnung sind. Was sie nicht koennen: die Form einer
Erfolgs-Antwort belegen. Sie stimmen mit dem ueberein, was ihr Autor annahm.
Diese Tests spielen echte Antworten ab, damit ein umbenanntes Feld hier
auffaellt statt in Produktion.

Herkunft, Datum, Auswahlregel und SHA-256 je Datei stehen in
`tests/fixtures/PROVENANCE.md`; neu aufzeichnen mit
`python scripts/record_fixtures.py`.
"""

from __future__ import annotations

import datetime as dt
import re

import httpx
import pytest
import respx
from fixture_data import fixture_json, provenance, recorded_names

from termdat_mcp.client import BASE_URL, TermdatClient, flatten_entry

# Jeder externe Endpunkt dieses Servers und die Fixture dazu. Ein Endpunkt ohne
# Aufzeichnung faellt in `test_jeder_endpunkt_hat_eine_aufzeichnung`.
ENDPOINTS = {
    "/Classification": "classification_de.json",
    "/Collection": "collection_de.json",
    "/Search": "search_detail.json",
    "/Entry": "entry.json",
}


def mount(path: str, name: str) -> None:
    """Serviert Fixture `name` unter `path`. Aufgezeichnet wurde durchweg 200."""
    respx.get(f"{BASE_URL}{path}").mock(return_value=httpx.Response(200, json=fixture_json(name)))


# --------------------------------------------------------------------------
# Herkunft
# --------------------------------------------------------------------------


def test_provenance_nennt_ein_brauchbares_aufnahmedatum():
    """Eine Aufzeichnung ohne Datum ist eine undatierte Behauptung ueber die Quelle."""
    match = re.search(r"Aufgezeichnet am \*\*(\d{4}-\d{2}-\d{2})\*\*", provenance())
    assert match, "PROVENANCE.md nennt kein Aufnahmedatum im erwarteten Format"
    when = dt.date.fromisoformat(match.group(1))
    assert when <= dt.datetime.now(dt.timezone.utc).date(), "Aufnahmedatum liegt in der Zukunft"


def test_jede_fixture_steht_in_der_provenance():
    """Sonst waechst der Ordner und der Nachweis bleibt zurueck."""
    text = provenance()
    fehlend = [n for n in recorded_names() if f"## `{n}`" not in text]
    assert not fehlend, f"ohne Eintrag in PROVENANCE.md: {fehlend}"


def test_jeder_endpunkt_hat_eine_aufzeichnung():
    """Bewacht die Regel selbst: eine aufgezeichnete Antwort je externem Endpunkt."""
    fehlend = sorted(set(ENDPOINTS.values()) - set(recorded_names()))
    assert not fehlend, f"Endpunkte ohne Aufzeichnung: {fehlend}"


# --------------------------------------------------------------------------
# Vokabulare
# --------------------------------------------------------------------------


@respx.mock
async def test_classification_wird_aus_der_aufzeichnung_gelesen():
    rows = fixture_json("classification_de.json")
    mount("/Classification", "classification_de.json")
    client = TermdatClient()
    try:
        values, _, _ = await client.vocabulary("Classification", "DE")
    finally:
        await client.aclose()
    assert len(values) == len(rows)
    assert all(v.get("code") for v in values), "jede Klassifikation traegt einen Code"
    assert all(v.get("text") for v in values), "jede Klassifikation traegt einen Text"


@respx.mock
async def test_collection_wird_aus_der_aufzeichnung_gelesen():
    rows = fixture_json("collection_de.json")
    mount("/Collection", "collection_de.json")
    client = TermdatClient()
    try:
        values, _, _ = await client.vocabulary("Collection", "DE")
    finally:
        await client.aclose()
    assert len(values) == len(rows)
    assert all(v.get("code") for v in values)


# --------------------------------------------------------------------------
# Suche und Einzeleintrag
# --------------------------------------------------------------------------


@respx.mock
async def test_search_bildet_die_aufgezeichneten_treffer_ab():
    hits = fixture_json("search_detail.json")
    mount("/Classification", "classification_de.json")
    mount("/Search", "search_detail.json")
    client = TermdatClient()
    try:
        entries, _ = await client.search("Sonderpädagogik", detail=True)
    finally:
        await client.aclose()
    assert len(entries) == len(hits)
    assert all(e["entry_id"] for e in entries), "jeder Treffer traegt eine ID"
    assert all(e["url"] for e in entries), "jeder Treffer traegt eine URL"
    assert any(e["variants"] for e in entries), "Sprachvarianten stehen in `languageDetails`"


@respx.mock
async def test_entry_bildet_den_aufgezeichneten_eintrag_ab():
    raw = fixture_json("entry.json")
    entry_id = raw[0]["id"]
    mount("/Entry", "entry.json")
    client = TermdatClient()
    try:
        entries, _ = await client.entries([entry_id])
    finally:
        await client.aclose()
    assert len(entries) == len(raw)
    assert entries[0]["entry_id"] == entry_id
    assert entries[0]["url"]


def test_flatten_entry_liest_die_aufgezeichnete_satzform():
    """Direkt am Mapper: die Feldnamen der Quelle, nicht die erwarteten.

    Faellt, sobald TERMDAT eines dieser Felder umbenennt — der Fall, den eine
    handgeschriebene Fixture per Konstruktion nicht bemerken kann.
    """
    raw = fixture_json("entry.json")[0]
    flat = flatten_entry(raw)
    assert flat["entry_id"] == raw["id"]
    assert flat["url"] == raw["url"]
    assert flat["status"] == raw["status"]["text"]
    assert flat["office"] == raw["office"]["text"]
    assert len(flat["variants"]) == len(raw["languageDetails"])
    assert flat["variants"][0]["language"] == raw["languageDetails"][0]["languageIsoCode"]


@pytest.mark.parametrize("name", sorted(ENDPOINTS.values()))
def test_jede_aufzeichnung_ist_nicht_leer(name):
    """Eine leere Aufzeichnung sieht aus wie eine gueltige und prueft nichts."""
    assert fixture_json(name), f"{name} ist leer — neu aufzeichnen"
