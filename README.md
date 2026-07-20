> 🇨🇭 Part of the [**Swiss Public Data MCP Portfolio**](https://github.com/malkreide/swiss-public-data-mcp) — open-source MCP servers connecting AI agents to Swiss public and open data.
> This is a private project. It is independent of any employer or institutional affiliation.

# 🏷️ termdat-mcp

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)
[![CI](https://github.com/malkreide/termdat-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/malkreide/termdat-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Model_Context_Protocol-8A2BE2.svg)](https://modelcontextprotocol.io/)
[![Auth: none](https://img.shields.io/badge/auth-none-brightgreen.svg)](#architecture-decision)
[![Portfolio](https://img.shields.io/badge/portfolio-swiss--public--data--mcp-informational)](https://github.com/malkreide/swiss-public-data-mcp)

> Official, validated Swiss administrative designations across DE / FR / IT / EN — with source references and validation status.

[🇩🇪 Deutsche Version](README.de.md)

## Overview

MCP server for **TERMDAT**, the terminology database of the Swiss Federal Administration, maintained by the Federal Chancellery. It gives an AI agent the officially validated designations of Swiss authorities, departments and legal acts across DE / FR / IT / EN — with source references and validation status.

Discovered through [`i14y-mcp`](https://github.com/malkreide/i14y-mcp), which catalogues TERMDAT as data service `ff0c37eb-2f7c-4ff6-996e-d22b77bf52fc`.

**What this is — and what it is not.** TERMDAT is not a subject dictionary. It is a **certified name-plate archive**: it will not tell you what «Sonderpädagogik» means, but it will tell you the official name of the authority responsible for it, and what that authority is called in French.

Measured coverage (live, 2026-07-19, German search over the Terminus field):

| Search term | Hits |
|---|---|
| Departement | 20 |
| Bildung | 13 |
| Verordnung | 8 |
| Schule | 5 |
| Behörde | 4 |
| Sonderpädagogik | 3 |
| Volksschule · Lehrperson · Schulleitung · Unterricht · Kindergarten | **0** |

The thirteen «Bildung» hits are organisational names — Bildungsdirektion, Erziehungsdepartement, Departement für Volkswirtschaft und Bildung — not pedagogical concepts. Plan accordingly: this server is strong for **authority naming, official titles and abbreviations**, and largely silent on domain vocabulary.

## Features

- Seven read-only tools over the official TERMDAT public v2 API.
- Official designations across **DE / FR / IT / EN**, with source reference and validation status on every response.
- Communication QA: check up to 25 terms in one call against validated designations.
- Vocabulary cache (24 h TTL) for the 140 collections and 23 classifications, with stale-serve fallback.
- Retry with exponential backoff (2/4/8 s); explicit `MaxEntryCount` to avoid silent truncation.
- Dual transport: `stdio` (local) and SSE (cloud).
- No authentication required — public, unauthenticated API (No-Auth-First).

## 🎯 Anchor demo query

> *«What are the official French and Italian names of the education directorates of the German-speaking cantons?»*

Resolved with `list_classifications` → `search_terms` → `translate_term`.

## Prerequisites

- Python 3.10+
- [`uv` / `uvx`](https://docs.astral.sh/uv/) (recommended) or `pip`
- Network access to `api.termdat.bk.admin.ch` — no API key needed

## Installation

```bash
uvx termdat-mcp
```

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "termdat": {
      "command": "uvx",
      "args": ["termdat-mcp"]
    }
  }
}
```

## Quickstart

```bash
# Run locally over stdio (default transport)
uvx termdat-mcp

# From a checkout, without installing
PYTHONPATH=src python -m termdat_mcp
```

## Configuration

All configuration is via environment variables. Defaults are safe for local use.

| Variable | Default | Purpose |
|---|---|---|
| `TERMDAT_MCP_TRANSPORT` | `stdio` | Transport: `stdio` (local) or `sse` / `streamable-http` / `http` (cloud) |
| `HOST` | `0.0.0.0` | Bind host (SSE transport only) |
| `PORT` | `8000` | Bind port (SSE transport only) |

Cloud (Render / Railway):

```bash
TERMDAT_MCP_TRANSPORT=sse PORT=8000 termdat-mcp   # exposes /sse
```

## Available Tools

| Tool | Purpose |
|---|---|
| `search_terms` | Search TERMDAT with field flags, collection and classification filters |
| `translate_term` | Official equivalent of an administrative term in another national language |
| `check_terms` | Communication QA: check up to 25 terms against validated designations |
| `get_entries` | Fetch known entries by numeric ID |
| `list_collections` | The ~140 terminology collections (filter values) |
| `list_classifications` | The 23 subject classifications, e.g. `BILD` = education |
| `api_status` | Availability; never returns silently empty |

All tools are annotated `readOnlyHint: true`, `destructiveHint: false`.

## Architecture

```
┌─────────────────┐   stdio / SSE    ┌──────────────────────────┐
│  MCP host       │ ───────────────► │  termdat-mcp             │
│  (Claude, IDE)  │ ◄─────────────── │                          │
└─────────────────┘                  │  vocabulary cache (24 h) │
                                     │  140 collections         │
                                     │   23 classifications     │
                                     └────────────┬─────────────┘
                                                  │ httpx + retry (2/4/8 s)
                                                  ▼
                              https://api.termdat.bk.admin.ch/v2
                              ├── /Search          (SearchTerm + InLanguageCode)
                              ├── /Entry           (EntryIds)
                              ├── /Collection      (140 values)
                              └── /Classification  ( 23 values, incl. BILD)
```

## Architecture decision

This server uses **Architecture A (live API only)**, with caching limited to the two controlled vocabularies.

Rationale (verified live on 2026-07-19):

- The API publishes a complete **OpenAPI 3.0.4 specification** at `/swagger/v2/swagger.json` and declares **no security schemes** — unauthenticated access, No-Auth-First satisfied.
- Server-side search works properly, including 11 field flags and filters by collection and classification. There is no reason to mirror the database locally, and no bulk dump is offered.
- `/Collection` (140 entries) and `/Classification` (23 entries) change rarely and are needed to make filter arguments legible to an agent, so they are cached with a 24-hour TTL and a stale-serve fallback.

Consequences:

- Every search is a live call; `provenance` is `live_api` except for vocabulary lookups.
- Validation errors arrive as clean RFC 9110 payloads and are surfaced rather than swallowed.

## Project Structure

```
termdat-mcp/
├── src/termdat_mcp/
│   ├── __init__.py
│   ├── __main__.py       # entry point; dual transport (stdio / SSE)
│   ├── client.py         # httpx client, retry, vocabulary cache
│   ├── models.py         # Pydantic models
│   └── server.py         # MCP tool definitions
├── tests/
│   ├── test_client.py    # offline, respx-mocked
│   └── test_live.py       # hits the real TERMDAT API
├── README.md
├── README.de.md
├── CHANGELOG.md
├── LICENSE
└── pyproject.toml
```

## Safety & Limits

- **Read-only.** Every tool is annotated `readOnlyHint: true`, `destructiveHint: false`; the server never writes to TERMDAT.
- **No credentials handled.** The API is unauthenticated; the server stores and forwards no secrets.
- **No silent empties.** `api_status` and error paths surface failures instead of returning an empty result that looks complete.
- **Truncation is explicit.** `MaxEntryCount` is always sent and `truncated` is reported (see Known Limitations).
- **Licence caution.** TERMDAT content carries no licence statement; every response repeats this in `source`. Clarify terms with the Federal Chancellery before republishing downstream.

## Known Limitations

- **Administrative scope only.** See the coverage table above. `check_terms` returns `not_found`, never «incorrect», precisely because absence from TERMDAT is not evidence of error.
- **`MaxEntryCount` has a silent default of ~25.** Omitting it looks like a complete result set. This server always sends the parameter explicitly and reports `truncated`.
- **Multilingual variants are opt-in.** Without `OutLanguageCode`, entries return German designations only. `translate_term` sets it for you.
- **No licence statement.** The I14Y catalogue record carries `license: null`. Clarify terms with the Federal Chancellery before republishing TERMDAT content downstream. Every response repeats this in `source`.
- **Entry-level language coverage varies.** Not every entry exists in all four languages; `translate_term` omits entries without a target-language variant rather than inventing one.

### Live probe findings (2026-07-19)

| Endpoint | HTTP | Status | Note |
|---|---|---|---|
| `/swagger/v2/swagger.json` | 200 | ✅ | OpenAPI 3.0.4, 132 KB, `securitySchemes: []` |
| `/v2/Search` | 200 | ✅ | requires `SearchTerm`, `InLanguageCode`, `ReturnType` |
| `/v2/Entry` | 200 | ✅ | requires `EntryIds`, `InLanguageCode` |
| `/v2/Collection` | 200 | ✅ | 140 values |
| `/v2/Classification` | 200 | ✅ | 23 values, incl. `BILD` (education) |
| `/v2/` (root) | 404 | ❌ | no index; the I14Y record points here |
| `InLanguageCode=deu` / `de-CH` | 400 | ❌ | only two-letter ISO codes, case-insensitive |

**Probe note: a correction worth recording.** An earlier probe concluded that `OutLanguageCode` *filters* the result set, because adding it appeared to drop all hits. It does not. Two variables had been changed at once — the parameter and the search term — and the term itself («Volksschule») genuinely has zero hits. Verified afterwards across four broad terms: result counts are identical with and without `OutLanguageCode`; the parameter is purely additive. A regression test (`test_out_language_is_additive_not_filtering`) now guards this.

**Rule of thumb:** *change one variable per probe call, or the API will confess to a crime it did not commit.*

## Project Phase

This server is in **Phase 1 (read-only)**. All tools are annotated
`readOnlyHint: true` / `destructiveHint: false` and only ever query the public
TERMDAT v2 API — there are no write, send, or filesystem capabilities.

| Phase | Scope | Status |
|---|---|---|
| **1 — Read-only** | Search, translate and check administrative designations | ✅ current |
| 2 — Write-capable | (none planned) | — |
| 3 — Multi-agent | (none planned) | — |

A transition to a later phase would require a re-audit and human-in-the-loop
controls before any write-capable tool is added.

## MCP Protocol Version

The protocol version is negotiated at the `initialize` handshake by the
[`mcp`](https://pypi.org/project/mcp/) Python SDK (pinned to `>=1.2.0` in
`pyproject.toml`). The SDK is kept current via monthly Dependabot PRs
(`.github/dependabot.yml`); protocol-relevant bumps are noted in
[`CHANGELOG.md`](CHANGELOG.md).

## Testing

```bash
PYTHONPATH=src pytest tests/ -m "not live"   # offline, respx-mocked
PYTHONPATH=src pytest tests/ -m live         # hits the real API
PYTHONPATH=src ruff check src tests
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Security

See [SECURITY.md](SECURITY.md) for the security posture, hardening controls, and how to report a vulnerability.

## Contributing

Issues and pull requests are welcome. Please keep tools read-only, run `ruff check` and the offline test suite before submitting, and add a `CHANGELOG.md` entry under `[Unreleased]` for user-facing changes.

Maintainers: see [PUBLISHING.md](PUBLISHING.md) for the step-by-step PyPI release process (Trusted Publishing via GitHub Release).

## License

MIT for this server — see [LICENSE](LICENSE). TERMDAT content remains subject to the Federal Chancellery's terms.

## Author

**Hayal Oezkan** · [github.com/malkreide](https://github.com/malkreide)

## Credits & Related Projects

- Data: [TERMDAT](https://www.termdat.bk.admin.ch/), Swiss Federal Chancellery (BK).
- Catalogue entry: [I14Y data service `ff0c37eb…`](https://www.i14y.admin.ch/en/catalog/dataservices/ff0c37eb-2f7c-4ff6-996e-d22b77bf52fc/description)
- Discovery server: [i14y-mcp](https://github.com/malkreide/i14y-mcp)
- Portfolio index: [swiss-public-data-mcp](https://github.com/malkreide/swiss-public-data-mcp)
