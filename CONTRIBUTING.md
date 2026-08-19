# Contributing

[🇩🇪 Deutsche Version](CONTRIBUTING.de.md)

Thanks for your interest in `termdat-mcp`. This is a read-only MCP server over the
public TERMDAT API; contributions should keep it that way.

## Ground rules

- **Read-only.** Every tool stays annotated `readOnlyHint: true`,
  `destructiveHint: false`. No write, send, or filesystem capability.
- **One egress host.** Requests go only to `api.termdat.bk.admin.ch` via the
  `ALLOWED_HOSTS` allow-list (see [`docs/network-egress.md`](docs/network-egress.md)).
- **No secrets.** The API is unauthenticated; do not add credential handling.

## Development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"

PYTHONPATH=src pytest tests/ -m "not live"   # offline, respx-mocked
PYTHONPATH=src pytest tests/ -m live         # hits the real API
python scripts/check_ruff_pin.py
ruff check src/ tests/ scripts/
ruff format --check src/ tests/ scripts/
python scripts/check_version_sync.py
```

## Pull requests

- Add tests for user-facing changes; keep `ruff check` and the offline suite green.
- Add a `CHANGELOG.md` entry under `[Unreleased]`.
- Update both `README.md` and `README.de.md` for any documentation change.
- For release/publishing, see [`PUBLISHING.md`](PUBLISHING.md).

## Reporting security issues

See [`SECURITY.md`](SECURITY.md) — please use private reporting, not public issues.

## The live suite: when it runs, and who sees a red result

**Cadence:** every Monday at 05:17 UTC, plus on demand via *Actions → Live API tests → Run
workflow*. See [`.github/workflows/live.yml`](.github/workflows/live.yml).

**Who sees it:** A red run opens an issue labelled `upstream` and the stable title “Live-Tests gegen api.termdat.bk.admin.ch rot (<Datum>)”. A second red run recognises the open issue by its title prefix and appends to that same thread rather than opening a second one. Once the suite is green again, the issue closes itself.

**Three answers, not two.** `scripts/classify_live_run.py` reads the JUnit XML rather than
the exit code and separates `clear` (ran, green), `finding` (ran, something
fell) and `unknown` (did not run — install failed, nothing collected,
everything skipped). An `unknown` never closes an issue: closing would claim a
comparison that never happened.

**A red live run does not necessarily mean *our* bug.** It means the contract
with the source has changed, or the source is down. Both belong seen; only the
first belongs fixed. Please read the run before disabling the job — that is how
this check dies, and it is the only one in the repository that can contradict a
wrong assumption about api.termdat.bk.admin.ch. Every other test asserts against a fixture, and
the fixture was written from the same assumption as the code.
