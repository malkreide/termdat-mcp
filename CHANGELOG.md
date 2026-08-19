# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [SemVer](https://semver.org/).

## [Unreleased]

### Behoben

- **Die Dokumentation nannte ein schmaleres Lint-Gate als die CI faehrt.**
  `README.md`, `README.de.md`, `CONTRIBUTING.md` und `CONTRIBUTING.de.md`
  empfahlen `ruff check src tests`. Die CI faehrt fuenf Gates, darunter
  `scripts/` im Lint-Pfad, `ruff format --check` und die beiden Pruefskripte.
  Wer der Dokumentation folgte, bekam gruen und danach eine rote CI, deren
  Ursache nicht im Diff stand. Alle vier Stellen nennen jetzt die Gates
  woertlich aus `ci.yml`.

- **Die READMEs nannten einen `mcp`-Pin, den es nicht mehr gibt.** Dort stand
  `>=1.2.0`; `pyproject.toml` fordert seit dem 2.x-Bruch `>=2.0.0,<3`. Genau
  diese Untergrenze ist der Grund, warum ein frischer Install ueberhaupt
  laeuft — als `>=1.2.0` gelesen wirkt sie wie eine unverbindliche Notiz.

- **Die Pruefsummen im Fixture-Nachweis waren Zierde.** `PROVENANCE.md` fuehrt
  je Datei einen SHA-256 — um genau einen Fall zu fangen: eine Aufzeichnung,
  die nach dem Lauf von Hand nachgebessert wurde. Eine korrigierte Antwort ist
  wieder eine erfundene, und von aussen ist ihr das nicht anzusehen.
  Nachgerechnet hat sie kein Test. `test_die_pruefsumme_im_nachweis_stimmt`
  tut es jetzt, ueber die Bytes auf der Platte statt ueber den Loader — genau
  die hat der Recorder gehasht.

- **`detail=False` liefert Treffer ohne jede Benennung — und sagte es nicht.**
  Der Parameter hängt am Werkzeug `termdat_search`, war im Docstring aber mit
  keinem Wort erklärt. Er setzt `ReturnType=Summary`; die Quelle lässt dann
  `languageDetails` weg, und `flatten_entry` macht daraus `variants: []`. Die
  Treffer behalten ID, URL, Status und Klassifikation — aber keine einzige
  Benennung. Für einen Terminologie-Server ist das ein Eintrag ohne Begriff,
  und ein Modell, das den Parameter zum Token-Sparen setzt, bekommt Treffer, aus
  denen es nichts lesen kann.

  Der Docstring sagt es jetzt, mitsamt dem, wofür der Modus taugt (zählen,
  nach Klassifikation filtern) und wofür nicht.

- **Der Fixture-Dispatcher ordnete nach Pfad zu.** `/Search` bekam immer
  `search_detail.json` — auch für eine Summary-Abfrage. Der Unterschied, um den
  es hier geht, war damit im Test unsichtbar: eine Abfrageform ohne
  Aufzeichnung sah aus wie eine mit. Zugeordnet wird jetzt nach `ReturnType`,
  und ein unbekannter Wert fällt laut auf, statt still eine fremde Aufzeichnung
  zu bekommen.

### Hinzugefügt

- **`search_summary.json`** — die zweite Abfrageform von `/Search`, echt
  aufgezeichnet. `test_die_beiden_suchformen_sind_wirklich_verschieden` hält
  fest, dass sie sich in genau dem Feld unterscheiden, aus dem die Benennungen
  kommen; ohne diesen Nachweis belegte die zweite Datei nichts.
  `test_eine_summary_suche_liefert_treffer_ohne_jede_benennung` hält den Stand
  fest und fällt, wenn die Quelle im Summary doch Benennungen liefert — dann
  gehört der Warnsatz im Docstring gestrichen.

### Changed

- **Der Backoff-Schlaf wird ueber einen Modul-Alias gepatcht, nicht ueber
  `asyncio.sleep`.** Die Tests nullten die Wartezeit mit
  `monkeypatch.setattr(<modul>.asyncio, "sleep", ...)`. Das liest sich lokal,
  ersetzt `sleep` aber auf dem geteilten Modulobjekt — fuer httpx, respx,
  pytest-asyncio und jeden anderen Importeur im Prozess. Das Modul legt die
  Naht jetzt als `_sleep = asyncio.sleep` offen; gepatcht wird diese.
  `test_der_retry_geht_ueber_den_alias` haelt sie: umgeht der Retry den Alias,
  faellt der Test in Sekundenbruchteilen. Ohne ihn fiel gar nichts — die Suite
  wurde nur ein Vielfaches langsamer, und eine laengere Laufzeit ist kein
  Signal, das jemand liest.


### Behoben

- **Der 20-Sekunden-Deckel war keine Grenze.** Gedeckelt wurde *vor* dem
  Jittern, also wurde ein auf `MAX_DELAY_S` gedeckelter Wert anschliessend mit
  bis zu 1.5 multipliziert: exponentielle Wartezeiten bis 30 s,
  `Retry-After`-Wartezeiten bis 25 s. Neu wird nach dem Jittern gedeckelt.

- **Das Gesamtbudget war nicht garantiert.** `httpx` wendet sein Timeout pro
  Operation an, und das Read-Timeout beginnt mit jedem Chunk von vorn — eine
  langsam troepfelnde Antwort konnte das Budget ueberdauern, ohne dass ein
  einzelner Read ablief. Neu liegt eine `asyncio.wait_for`-Deadline um den
  Request. (`asyncio.timeout` laese sich besser, kam aber erst in 3.11; dieses
  Paket unterstuetzt weiterhin 3.10.)

  Beide Befunde stammen aus einem Codex-Review an `parlament-mcp#35`. Der Test
  zur Deadline musste die *echte* `asyncio.sleep` festhalten, bevor die
  autouse-`_no_sleep`-Fixture aus `conftest.py` sie ersetzt — sonst waere auch
  dieser Test gruen gewesen, ohne etwas zu pruefen.


### Added

- **Aufgezeichnete Fixtures, eine je externem Endpunkt, mit Nachweis.**
  `tests/fixtures/` haelt jetzt echte TERMDAT-Antworten fuer alle vier
  Endpunkte, die dieser Server aufruft — `/Search`, `/Entry`, `/Classification`
  und `/Collection` —, aufgezeichnet von `scripts/record_fixtures.py`. Herkunft,
  Datum, Auswahlregel und SHA-256 stehen je Datei in
  `tests/fixtures/PROVENANCE.md`, wie im uebrigen Portfolio.
  `tests/test_recorded_fixtures.py` spielt sie durch den echten Client.

  Handgeschriebene Stubs kodieren die Annahme ihres Autors und koennen sie nicht
  widerlegen: in `i14y-mcp` blieb genau deshalb die ganze Suite gruen, waehrend
  drei Tools produktiv leere Titel lieferten. Fehlerpfade bleiben
  handgeschrieben, die lassen sich nicht auf Zuruf aufzeichnen.

  Gegenprobe, jede Zusicherung einzeln neutralisiert: Aufnahmedatum entfernt ->
  Datums-Check faellt; Fixture ohne PROVENANCE-Eintrag -> Vollstaendigkeits-Check
  faellt; Aufzeichnung geloescht -> Abdeckungs-Waechter faellt; `languageIsoCode`
  umbenannt -> der Mapper-Test faellt.

- **`Retry-After` wird gelesen und schlaegt die eigene Backoff-Kurve** (ARCH-014).
  Bei 429 und 503 sagt TERMDAT im Header, wann es wieder mag — als Sekundenzahl
  oder HTTP-Datum; beide Formen kommen vor, beide werden gelesen
  (RFC 9110 §10.2.3). Wer stattdessen weiter seine Kurve faehrt, ignoriert eine
  ausdrueckliche Angabe. Ein unbrauchbarer Header fuehrt zurueck auf die Kurve
  statt zum Absturz — auf dem Fehlerpfad darf eine kaputte Kopfzeile nicht das
  Letzte sein, woran der Client stirbt.

- **Backoff ist gestreut (Jitter).** `2**attempt` war deterministisch: Faellt
  die API aus, waehrend mehrere Clients sie abfragen, retryen alle im
  Gleichtakt, und die Last kommt als Welle zurueck — genau wenn die API sich
  erholt. Exponentielle Wartezeiten landen jetzt in `[0.5x, 1.5x]`. Auf einem
  `Retry-After` ist die Streuung einseitig (`[1.0x, 1.25x]`): spaeter ist
  hoeflich, frueher waere die Missachtung derselben Angabe, die man gerade
  gelesen hat.

- **Deckel von 20 s auf jede einzelne Wartezeit** — gegen die unbegrenzt
  wachsende Leiter und gegen ein `Retry-After`, das die API senden darf, das man
  aber nicht absitzen muss.

- **Gesamtbudget von 25 s ueber den ganzen Aufruf** (ARCH-014). Eine Anzahl
  Versuche ist keine Grenze: Vier Versuche a 60 s Timeout plus Backoff sind
  ueber vier Minuten, und die Zahl `4` sagt das nirgends. Entscheidender ist,
  dass die massgebliche Grenze gar nicht uns gehoert — der Aufrufer hat sein
  eigenes Timeout, und jenseits davon hoert niemand mehr zu: Die Arbeit laeuft
  weiter, die Last landet bei TERMDAT, das Ergebnis geht ins Leere.

  Der Anker ist gemessen, nicht geschaetzt: Das Python-MCP-SDK setzt
  `MCP_DEFAULT_TIMEOUT = 30.0` fuer allgemeine Operationen
  (`mcp/shared/_httpx_utils.py`). 25 s lassen Luft fuer MCP-Framing,
  Antwort-Parsing und die Tool-Schicht. Ein Test haelt die Beziehung fest und
  schlaegt an, wenn das SDK seinen Default senkt.

  Geprueft wird vor jedem Versuch: Eine Wartezeit, die das Budget ueberdauern
  wuerde, wird nicht mehr angetreten, und das Timeout eines einzelnen Versuchs
  ist auf die verbleibende Zeit geklemmt. Log-Event und Meldung nennen neu,
  **welche** Grenze gegriffen hat — «all 4 attempts used» und «25s budget
  spent» verlangen verschiedene Antworten.

  Das Client-Timeout faellt von 60 s auf 25 s: Ein Wert oberhalb des Budgets
  haette nur noch behauptet, was er nicht mehr gewaehrt.

  Die Abwaegung ist bewusst: Ein langsamer erster Versuch kann jetzt das Budget
  aufbrauchen und laesst dann keinen Retry mehr zu. Genau das ist die
  beabsichtigte Antwort — ein Retry, der nach dem Aufgeben des Aufrufers fertig
  wird, bringt niemandem etwas und kostet TERMDAT eine Anfrage.

## [0.1.3] - 2026-08-02

### Fixed

- **`structlog` carried no upper bound, and the index already serves a major past
  the floor.** The declared range was `structlog>=24.1`; PyPI has been serving
  `26.1.0`. The artefact does not change — the resolver's answer to the next
  fresh install does, and that is exactly how `swiss-energy-mcp` 0.3.3 became
  uninstallable when `mcp` 2.0.0 removed the module it imported.

  Now `structlog>=24.1,<27`. The bound is measured rather than guessed: this package
  installs and imports against `structlog 26.1.0` today, so the cap admits what
  demonstrably works and stops only the next, unknown major.

A dependency range only reaches users through a new release, hence the
version bump. No code changed.

## [0.1.2] — 2026-07-30

### Fixed

- **The User-Agent reports the actual package version again.** The published
  `0.1.1` sent `termdat-mcp/0.1.0` to every upstream — the version string was
  hardcoded and had been left behind by earlier bumps. The version now comes
  from the package metadata, so it can no longer drift from the package.

### Documented

- **The public API exposes less than the website** — a coverage limit of the
  source, not a scope setting on our side. Follow-up to #11: @dfch supplied the
  12 entry IDs the website lists for «Quellensteuer»; the API returns 7 at
  maximum recall (every language, all 11 fields, infix wildcard, all
  classifications and collections), and the two sets overlap in exactly **one**
  entry, 447912. Fetching the missing IDs directly via `/v2/Entry` returns
  HTTP 200 with an empty body — they are not served at all, so no query can
  reach them. The one exception, 1557, is served but carries status
  `In Bearbeitung` in a collection marked «(aufgehoben)», which suggests the
  search index covers validated entries while the website also shows drafts and
  repealed material.

  This corrects an earlier guess. The residual was described in #11 as probably
  a counting difference — the website listing designations where the API counts
  entries. The IDs disprove that: they are twelve distinct entries. Recorded
  here so the wrong explanation does not outlive the measurement.

  Documented in both READMEs, and in the `search_terms` docstring, where it
  matters most: a model told only that «a term may genuinely be absent» will
  conclude «absent from TERMDAT», which is false for entries the website shows.
  The docstring now distinguishes the two.

### Fixed

- **Capped `mcp` at `<2`.** `mcp` 2.0.0, published 2026-07-28, removed
  `mcp.server.fastmcp` — the module this server imports. With the previous
  unbounded `>=1.28.1` every fresh resolve picked 2.0.0 and failed at import
  with `ModuleNotFoundError`, in CI and for anyone running `pip install` alike.
  Verified in both directions: 2.0.0 fails, `<2` resolves to 1.29.0 and imports
  cleanly. Migrating to the 2.x API (`mcp.server.mcpserver`) stays a separate,
  deliberate piece of work.

## [0.1.1] — 2026-07-27

### Fixed
- **MCP Registry publish was blocked by a missing ownership marker.** The
  registry verifies ownership of a PyPI package by looking for an
  `mcp-name: <server-name>` marker in the *published* package README. The marker
  was added to `README.md` after 0.1.0 shipped, so it never reached PyPI — and
  PyPI releases are immutable, so it cannot be added to the 0.1.0 artifact
  retroactively. This release carries it into the package metadata.
- **Search was confined to the `VARIA` classification** (#11, reported by
  @dfch). `/v2/Search` restricts an ID-less query to a "default set (=VARIA)",
  so every unfiltered search covered 1 of 23 subject areas — and reported the
  result as a normal empty answer. `search_terms`, `translate_term` and
  `check_terms` now send the full classification set unless the caller narrows
  it. «Quellensteuer» 0 → 3 entries, «Pensionskasse» 1 → 21.
- **`fields` could widen a search but never narrow it.** Unsent `Field.*` flags
  keep their API-side default (`Terminus`, `Name`, `Abbreviation`,
  `Phraseology` = true), so `fields="Terminus"` was a no-op. All eleven flags
  are now sent explicitly.
- **Default field set widened** to include `Definition`, `Note` and `Source`;
  `translate_term` and `check_terms` stay on the four designation fields, so a
  term merely mentioned in a definition is never reported as an equivalent.
- **Misleading scope caveat.** The `search_terms` docstring presented an empty
  result as probable out-of-scope, which invited models to invent a designation
  instead of retrying. It now documents Lucene wildcards and asks for a retry;
  an empty `SearchResult` carries a `hint` field saying the same.

### Security
- **SEC-016 (NeighborJack):** the SSE transport now binds to `127.0.0.1` by
  default instead of `0.0.0.0`. Binding to `0.0.0.0` is an explicit opt-in that
  logs a stderr warning when used outside a container. README/SECURITY updated.
- **SEC-021:** code-layer egress allow-list (`ALLOWED_HOSTS` + `assert_host_allowed`),
  enforced before every request; `docs/network-egress.md`.
- **SEC-018:** input bounds at the tool boundary — `max_results` 1–100, plus
  string/list length limits on `search_term`, `term`, `terms`, `entry_ids`, `fields`.
- **SEC-007:** hardened non-root `Dockerfile` for SSE deployments.
- **SEC-005 / SCALE-002:** accepted-risk ADRs for DNS pinning and stateful load
  balancing (`docs/adr/0001`, `0002`).

### Added
- Typed configuration via `pydantic-settings` (`settings.py`); new env vars
  `TERMDAT_MCP_LOG_LEVEL`, `TERMDAT_MCP_CORS_ORIGINS`, `TERMDAT_MCP_VOCAB_TTL`.
- Structured logging via `structlog`, pinned to stderr as JSON (`logging_config.py`).
- FastMCP `lifespan` owning the shared HTTP client (cleanup on shutdown).
- Explicit CORS for the SSE transport, exposing only `Mcp-Session-Id`.
- `CONTRIBUTING.md` / `CONTRIBUTING.de.md`; scheduled/manual live-test workflow.
- Expanded test suite (12 → 28 offline tests): per-tool coverage, error paths,
  egress allow-list, tool-schema input bounds.
- MCP best-practice audit against the portfolio catalog (68 checks, 36
  applicable) under `audits/`: **production-ready**; the 19-item hardening
  backlog from that audit is addressed by the changes above.

### Changed
- `api_status` and the client no longer forward raw upstream exception strings to
  the model (OBS-002 error-detail masking); detail goes to the structured log.
- `check_terms` runs its per-term lookups concurrently (`asyncio.gather`) and
  reports progress via `ctx` when available (ARCH-007 / SDK-003).
- Tools grouped rationale + MCP-primitives note documented in the READMEs.

## [0.1.0] — 2026-07-20

First public release, published to PyPI.

### Added
- Seven read-only tools over the TERMDAT public v2 API: `search_terms`,
  `translate_term`, `check_terms`, `get_entries`, `list_collections`,
  `list_classifications`, `api_status`.
- Vocabulary cache (24 h TTL) for collections and classifications, with
  stale-serve fallback on refresh failure.
- Retry with exponential backoff (2/4/8 s); 4xx except 429 fails fast.
- Dual transport: stdio and SSE.
- PyPI packaging: `Publish to PyPI` workflow (`.github/workflows/publish.yml`)
  using PyPI Trusted Publishing (OIDC) on GitHub Release, and a step-by-step
  `PUBLISHING.md` guide linked from the READMEs.
- Distribution metadata in `pyproject.toml`: `LICENSE`-referenced license,
  per-version Python classifiers (3.10–3.13), `OS Independent`, and
  `Repository` / `Issues` / `Changelog` project URLs.
- GitHub Actions CI workflow (`.github/workflows/ci.yml`): ruff + offline
  pytest on Python 3.10–3.13, with a CI status badge in both READMEs.
- Dependabot config (`.github/dependabot.yml`): monthly `pip` and
  `github-actions` updates to keep the `mcp` SDK and workflow actions current.
- `SECURITY.md` / `SECURITY.de.md`: security posture, accepted-risk decisions,
  and vulnerability-reporting process; linked from both READMEs.
- `.gitignore` for the Python project.
- Bilingual documentation (`README.md` / `README.de.md`) aligned with the Swiss
  Public Data MCP Portfolio convention, including `Project Phase` and
  `MCP Protocol Version` sections.

### Known findings (live probe 2026-07-19)
- **`MaxEntryCount` has a silent default of ~25.** Omit it and the response
  looks complete while it is capped. Always send it explicitly and report
  truncation.
- **Language codes accept only two-letter ISO forms**, case-insensitively.
  `deu` and `de-CH` both return HTTP 400. Normalised client-side with a
  message that names the rejected forms.
- **`OutLanguageCode` is additive, not filtering**, and its effect is visible
  only with `ReturnType=Detail`. Summary responses carry no `languageDetails`
  at all, which makes the parameter look broken.
- **Umlauts must be URL-encoded properly.** `Sonderpädagogik` sent raw returns
  HTTP 400; encoded it returns 3 hits. Trivial, and expensive to debug inside
  an agent chain.
- **Scope is administrative, not domain-specific.** Volksschule, Lehrperson,
  Schulleitung, Unterricht and Kindergarten all return zero hits; Departement
  returns 20. Metaphor for the docs: *TERMDAT is not a dictionary, it is a
  certified name-plate archive.*

### Corrected
- An earlier probe note claimed `OutLanguageCode` filters the result set. It
  does not — two variables had been changed in the same call. Corrected in the
  README and pinned by the live regression test
  `test_out_language_is_additive_not_filtering`.
