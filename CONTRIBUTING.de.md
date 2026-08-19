# Mitwirken

[🇬🇧 English Version](CONTRIBUTING.md)

Danke für dein Interesse an `termdat-mcp`. Dies ist ein Read-only-MCP-Server über
die öffentliche TERMDAT-API; Beiträge sollen das so belassen.

## Grundregeln

- **Read-only.** Jedes Tool bleibt mit `readOnlyHint: true` und
  `destructiveHint: false` annotiert. Keine Schreib-, Sende- oder
  Dateisystem-Fähigkeit.
- **Nur ein Egress-Host.** Anfragen gehen ausschliesslich an
  `api.termdat.bk.admin.ch` über die `ALLOWED_HOSTS`-Allow-List (siehe
  [`docs/network-egress.md`](docs/network-egress.md)).
- **Keine Secrets.** Die API ist unauthentifiziert; keine Credential-Verarbeitung
  hinzufügen.

## Entwicklung

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"

PYTHONPATH=src pytest tests/ -m "not live"   # offline, respx-gemockt
PYTHONPATH=src pytest tests/ -m live         # gegen die echte API
python scripts/check_ruff_pin.py
ruff check src/ tests/ scripts/
ruff format --check src/ tests/ scripts/
python scripts/check_version_sync.py
```

## Pull Requests

- Tests für nutzersichtbare Änderungen ergänzen; `ruff check` und die
  Offline-Suite grün halten.
- Einen `CHANGELOG.md`-Eintrag unter `[Unreleased]` hinzufügen.
- Bei Doku-Änderungen sowohl `README.md` als auch `README.de.md` aktualisieren.
- Für Release/Publishing siehe [`PUBLISHING.md`](PUBLISHING.md).

## Sicherheitsprobleme melden

Siehe [`SECURITY.md`](SECURITY.md) — bitte privat melden, keine öffentlichen Issues.

## Die Live-Suite: wann sie läuft, und wer ein rotes Ergebnis sieht

**Kadenz:** jeden Montag um 05:17 UTC, dazu jederzeit von Hand über *Actions → Live API tests → Run
workflow*. Siehe [`.github/workflows/live.yml`](.github/workflows/live.yml).

**Wer es sieht:** Ein roter Lauf öffnet ein Issue mit dem Label `upstream` und dem stabilen Titel «Live-Tests gegen api.termdat.bk.admin.ch rot (<Datum>)». Ein zweiter roter Lauf erkennt das offene Issue am Titelanfang und hängt sich an denselben Thread, statt ein zweites aufzumachen. Wird die Suite wieder grün, schliesst sich das Issue selbst.

**Drei Antworten, nicht zwei.** `scripts/classify_live_run.py` liest das JUnit-XML statt des
Exit-Codes und unterscheidet: `clear` (gelaufen, grün), `finding` (gelaufen,
etwas gefallen) und `unknown` (nicht gelaufen — Installation gescheitert, null
Tests eingesammelt, alle übersprungen). Ein `unknown` schliesst nie ein Issue:
Zuzumachen hiesse zu behaupten, der Vergleich sei gelaufen.

**Ein roter Live-Lauf heisst nicht zwingend «unser Fehler».** Er heisst: Der
Vertrag mit der Quelle hat sich geändert, oder die Quelle ist gerade aus. Beides
gehört gesehen, nur das Erste gehört gefixt. Bitte den Lauf lesen, bevor der Job
deaktiviert wird — so stirbt dieser Check, und er ist der einzige im Repo, der
einer falschen Grundannahme über api.termdat.bk.admin.ch widersprechen kann. Jeder andere Test
prüft gegen eine Fixture, und die Fixture ist aus derselben Annahme geschrieben
wie der Code.
