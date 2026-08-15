#!/usr/bin/env python3
"""Zeichnet echte TERMDAT-Antworten nach `tests/fixtures/` auf.

Warum: eine handgeschriebene Fixture kodiert die Annahme ihres Autors und kann
sie deshalb nicht widerlegen. In `i14y-mcp` blieb genau deshalb eine ganze Suite
gruen, waehrend drei Tools produktiv leere Titel lieferten — die Stubs hatten
einen Schluessel erfunden und stimmten dem Mapper zu statt der Quelle.

Herkunft, Datum, Auswahlregel und SHA-256 je Datei schreibt dieses Skript nach
`tests/fixtures/PROVENANCE.md`. Neu aufzeichnen:

    python scripts/record_fixtures.py

Braucht Netzzugang zu `api.termdat.bk.admin.ch`. Entwicklungswerkzeug; weder das
Paket noch die Testsuite importieren es.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://api.termdat.bk.admin.ch/v2"
FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

# Enger Suchbegriff mit Absicht: die Fixture soll die Satzform belegen, nicht
# den Bestand. Ein breiter Begriff erzeugt bei jedem Aufzeichnen einen anderen,
# unlesbaren Diff.
SEARCH_TERM = "Sonderpädagogik"
MAX_ENTRIES = 3

# Die Suchfelder, die der Client per Default setzt — hier wortgleich, damit die
# Aufzeichnung dieselbe Anfrage belegt, die der Server auch stellt.
FIELDS_ON = ("Terminus", "Name", "Abbreviation", "Phraseology", "Definition", "Note", "Source")
FIELDS_ALL = (
    "Terminus",
    "Name",
    "Abbreviation",
    "Phraseology",
    "Definition",
    "Note",
    "Context",
    "Source",
    "Metadata",
    "Country",
    "Comment",
)


def get(path: str, params: list[tuple[str, Any]] | None = None) -> tuple[str, Any, str]:
    url = f"{BASE}{path}"
    if params:
        url = f"{url}?{urlencode(params)}"
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "termdat-mcp-recorder"})
    with urlopen(req, timeout=90) as resp:
        raw = resp.read().decode("utf-8")
    return raw, json.loads(raw), url


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    recorded_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries: list[dict[str, Any]] = []
    print(f"Zeichne auf von {BASE}")

    def write(name: str, text: str, url: str, rule: str) -> None:
        text = json.dumps(json.loads(text), ensure_ascii=False, indent=2) + "\n"
        (FIXTURES / name).write_text(text, encoding="utf-8")
        blob = text.encode("utf-8")
        entries.append(
            {
                "name": name,
                "url": url,
                "rule": rule,
                "bytes": len(blob),
                "sha256": hashlib.sha256(blob).hexdigest(),
            }
        )
        print(f"  ok  {name:<26} {len(blob):>7} B")

    # --- Vokabulare ------------------------------------------------------
    raw, classifications, url = get("/Classification", [("languageCode", "DE")])
    write("classification_de.json", raw, url, "vollstaendig; alle Sachgebiete auf Deutsch")

    raw, _, url = get("/Collection", [("languageCode", "DE")])
    write("collection_de.json", raw, url, "vollstaendig; alle Sammlungen auf Deutsch")

    # --- Suche -----------------------------------------------------------
    # Ohne ClassificationIds sucht die API nur in einem Teil des Bestands; der
    # Client setzt sie deshalb aus dem Vokabular zusammen. Hier genauso.
    params: list[tuple[str, Any]] = [
        ("SearchTerm", SEARCH_TERM),
        ("InLanguageCode", "DE"),
        ("ReturnType", "Detail"),
        ("MaxEntryCount", MAX_ENTRIES),
    ]
    for field in FIELDS_ALL:
        params.append((f"Field.{field}", "true" if field in FIELDS_ON else "false"))
    for row in classifications:
        params.append(("ClassificationIds", row["id"]))

    raw, hits, url = get("/Search", params)
    write(
        "search_detail.json",
        raw,
        url,
        f"«{SEARCH_TERM}», ReturnType=Detail, {len(hits)} von hoechstens {MAX_ENTRIES}; "
        "Feld-Flags wie der Client sie sendet",
    )
    if not hits:
        print("!! Suche lieferte keine Treffer — Begriff pruefen")
        return 1

    # Dieselbe Suche mit ReturnType=Summary. Das ist eine eigene Abfrageform und
    # keine Spielart: die Quelle liefert dabei kein `languageDetails`, und
    # `flatten_entry` macht daraus Eintraege mit leerem `variants` — Treffer ohne
    # jede Benennung. Ohne diese Aufzeichnung bekam eine Summary-Abfrage im Test
    # die Detail-Antwort, und der Unterschied war unsichtbar.
    summary_params = [(k, v) for k, v in params if k != "ReturnType"]
    summary_params.append(("ReturnType", "Summary"))
    raw, summary_hits, url = get("/Search", summary_params)
    write(
        "search_summary.json",
        raw,
        url,
        f"«{SEARCH_TERM}», ReturnType=Summary, {len(summary_hits)} von hoechstens "
        f"{MAX_ENTRIES}; sonst gleiche Parameter wie search_detail",
    )

    # --- Einzeleintrag, ID aus der Suche oben ----------------------------
    entry_id = hits[0]["id"]
    raw, _, url = get("/Entry", [("EntryIds", entry_id), ("InLanguageCode", "DE")])
    write("entry.json", raw, url, f"ein Eintrag (ID {entry_id}), erster Treffer aus search_detail")

    _write_provenance(recorded_at, entries)
    print(f"\nPROVENANCE.md geschrieben, Aufzeichnungsdatum {recorded_at}")
    return 0


def _write_provenance(recorded_at: str, entries: list[dict[str, Any]]) -> None:
    lines = [
        "# Herkunft der Fixtures",
        "",
        "**Erzeugt von `scripts/record_fixtures.py`. Nicht von Hand pflegen.**",
        "",
        f"Aufgezeichnet am **{recorded_at}** von der einzigen Quelle dieses Servers:",
        f"`{BASE}`.",
        "",
        "Ohne Datum ist «aufgezeichnet» nach zwei Jahren von «ausgedacht» nicht",
        "mehr zu unterscheiden — die Datei sieht gleich aus.",
        "",
        "**Es sind Ausschnitte, keine Vollabzuege.** Die Auswahlregel steht je",
        "Datei dabei; Feldstruktur und Schluesselnamen sind unangetastet. Eine",
        "Fixture belegt damit die *Form* der Antwort und einen datierten",
        "Ausschnitt ihres Inhalts — nicht den Bestand. Aussagen ueber",
        "Vollstaendigkeit gehoeren in Live-Tests.",
        "",
        "**Die Suche sendet ihre Feld-Flags vollstaendig.** Ungesetzte Flags",
        "behalten den API-seitigen Default (Terminus/Name/Abbreviation/",
        "Phraseology = true), womit `fields` die Suche nur verbreitern, nie",
        "verengen koennte. Die Aufzeichnung belegt deshalb dieselbe Anfrage, die",
        "auch der Server stellt — samt aller elf Flags.",
        "",
        "Fehlerpfade — 404, Timeouts, maskierte 4xx — bleiben handgeschrieben.",
        "Die lassen sich nicht auf Zuruf aufzeichnen.",
        "",
    ]
    for e in entries:
        lines += [
            f"## `{e['name']}`",
            "",
            f"- **Quelle:** `{e['url']}`",
            f"- **Aufgezeichnet:** {recorded_at}",
            f"- **Auswahl:** {e['rule']}",
            f"- **Groesse:** {e['bytes']} B",
            f"- **SHA-256:** `{e['sha256']}`",
            "",
        ]
    (FIXTURES / "PROVENANCE.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
