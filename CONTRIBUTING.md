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
ruff check src tests
```

## Pull requests

- Add tests for user-facing changes; keep `ruff check` and the offline suite green.
- Add a `CHANGELOG.md` entry under `[Unreleased]`.
- Update both `README.md` and `README.de.md` for any documentation change.
- For release/publishing, see [`PUBLISHING.md`](PUBLISHING.md).

## Reporting security issues

See [`SECURITY.md`](SECURITY.md) — please use private reporting, not public issues.
