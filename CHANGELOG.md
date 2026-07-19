# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [SemVer](https://semver.org/).

## [Unreleased]

### Added
- GitHub Actions CI workflow (`.github/workflows/ci.yml`): ruff + offline
  pytest on Python 3.10–3.13, with a CI status badge in both READMEs.
- Dependabot config (`.github/dependabot.yml`): monthly `pip` and
  `github-actions` updates to keep the `mcp` SDK and workflow actions current.
- `SECURITY.md` / `SECURITY.de.md`: security posture, accepted-risk decisions,
  and vulnerability-reporting process; linked from both READMEs.
- `.gitignore` for the Python project.
- `Project Phase` and `MCP Protocol Version` sections in both READMEs, matching
  the portfolio convention.

### Changed
- Documentation aligned with the Swiss Public Data MCP Portfolio convention:
  bilingual language cross-links, extended badge row (version, MCP, no-auth),
  canonical section order, and new `Features`, `Prerequisites`, `Quickstart`,
  `Configuration`, `Project Structure`, `Safety & Limits`, `Contributing` and
  `Author` sections in both `README.md` and `README.de.md`.

## [0.1.0] — 2026-07-19

### Added
- Seven read-only tools over the TERMDAT public v2 API: `search_terms`,
  `translate_term`, `check_terms`, `get_entries`, `list_collections`,
  `list_classifications`, `api_status`.
- Vocabulary cache (24 h TTL) for collections and classifications, with
  stale-serve fallback on refresh failure.
- Retry with exponential backoff (2/4/8 s); 4xx except 429 fails fast.
- Dual transport: stdio and SSE.

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
