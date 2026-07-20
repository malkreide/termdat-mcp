# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [SemVer](https://semver.org/).

## [Unreleased]

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
