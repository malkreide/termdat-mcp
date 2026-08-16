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

# `/Search` hat zwei Abfrageformen, nicht eine. `ReturnType` entscheidet, ob die
# Quelle `languageDetails` mitschickt — also ob ein Treffer eine Benennung traegt
# oder nicht. Zugeordnet wird deshalb nach dem *Parameter*, nicht nach dem Pfad:
# nach Pfad bekam eine Summary-Abfrage die Detail-Antwort, und der Unterschied,
# um den es hier geht, war unsichtbar.
SUCHFORMEN = {
    "Detail": "search_detail.json",
    "Summary": "search_summary.json",
}


def mount(path: str, name: str) -> None:
    """Serviert Fixture `name` unter `path`. Aufgezeichnet wurde durchweg 200."""
    respx.get(f"{BASE_URL}{path}").mock(return_value=httpx.Response(200, json=fixture_json(name)))


def mount_suche() -> None:
    """Serviert `/Search` nach `ReturnType` — Detail und Summary je aus ihrer Aufzeichnung.

    Eine Anfrage mit unbekanntem `ReturnType` faellt laut auf, statt still eine
    fremde Aufzeichnung zu bekommen.
    """

    def antwort(request: httpx.Request) -> httpx.Response:
        art = request.url.params.get("ReturnType")
        name = SUCHFORMEN.get(art)
        if name is None:
            raise AssertionError(
                f"keine Aufzeichnung fuer ReturnType={art!r} — "
                "neu aufzeichnen mit `python scripts/record_fixtures.py`."
            )
        return httpx.Response(200, json=fixture_json(name))

    respx.get(f"{BASE_URL}/Search").mock(side_effect=antwort)


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
    mount_suche()
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
async def test_eine_summary_suche_liefert_treffer_ohne_jede_benennung():
    """`detail=False` streicht genau das, wofuer dieses Werkzeug da ist.

    Die Quelle schickt bei `ReturnType=Summary` kein `languageDetails`, und
    `flatten_entry` macht daraus `variants: []`. Die Treffer behalten ID, URL,
    Status und Klassifikation — aber keine einzige Benennung. Fuer einen
    Terminologie-Server ist das ein Eintrag ohne Begriff.

    Diese Zusicherung haelt den Stand fest, nicht ein Wunschverhalten: solange
    `detail` als Parameter am Werkzeug haengt, soll wenigstens belegt sein, was
    er anrichtet. Sie faellt, wenn die Quelle anfaengt, auch im Summary
    Benennungen zu liefern — dann gehoert der Warnsatz im Docstring gestrichen.
    """
    mount("/Classification", "classification_de.json")
    mount_suche()
    client = TermdatClient()
    try:
        entries, _ = await client.search("Sonderpädagogik", detail=False)
    finally:
        await client.aclose()
    assert entries, "die Summary-Suche liefert ueberhaupt Treffer"
    assert all(e["entry_id"] for e in entries), "jeder Treffer traegt eine ID"
    assert not any(e["variants"] for e in entries), (
        "Summary liefert jetzt doch Benennungen — der Warnsatz im Docstring von "
        "`termdat_search` ist damit falsch und gehoert gestrichen"
    )


def test_die_beiden_suchformen_sind_wirklich_verschieden():
    """Sonst belegte die zweite Aufzeichnung nichts.

    Waeren Detail und Summary gleich, waere die Trennung im Dispatcher Zierde
    und der Warnsatz im Docstring erfunden. Der Unterschied liegt in genau einem
    Feld, und das ist das, aus dem die Benennungen kommen.
    """
    detail = fixture_json("search_detail.json")
    summary = fixture_json("search_summary.json")
    assert detail and summary, "beide Aufzeichnungen tragen Treffer"
    assert "languageDetails" in detail[0], "Detail fuehrt `languageDetails` nicht mehr"
    assert "languageDetails" not in summary[0], "Summary fuehrt jetzt `languageDetails`"


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


# --------------------------------------------------------------------------
# Der Nachweis, nachgerechnet
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", sorted(n for n in recorded_names() if n != "PROVENANCE.md"))
def test_die_pruefsumme_im_nachweis_stimmt(name):
    """Eine Pruefsumme, die niemand nachrechnet, ist Zierde.

    Sie steht im Nachweis, um genau einen Fall zu fangen: eine Aufzeichnung,
    die nach dem Lauf von Hand nachgebessert wurde. Eine korrigierte Antwort
    ist wieder eine erfundene — und von aussen ist ihr das nicht anzusehen.
    Ohne diesen Test faengt die Summe nichts.

    Gerechnet wird ueber die Bytes auf der Platte, nicht ueber den Loader:
    genau die hat der Recorder gehasht, und ein Loader, der unterwegs dekodiert
    oder normalisiert, wuerde die Pruefung gegen sich selbst fuehren.
    """
    import hashlib
    import re
    from pathlib import Path

    teile = provenance().split(f"## `{name}`", 1)
    assert len(teile) == 2, f"{name} hat keinen Block in PROVENANCE.md"
    treffer = re.search(r"\*\*SHA-256:\*\*\s*`([0-9a-f]{64})`", teile[1].split("## ", 1)[0])
    assert treffer, f"{name} steht ohne Pruefsumme im Nachweis"
    roh = (Path(__file__).resolve().parent / "fixtures" / name).read_bytes()
    assert hashlib.sha256(roh).hexdigest() == treffer.group(1), (
        f"{name} weicht vom Nachweis ab — von Hand nachgebessert? Neu aufzeichnen."
    )
