# Security Policy & Posture

[🇩🇪 Deutsche Version](SECURITY.de.md)

`termdat-mcp` is a **read-only**, **no-auth**, **public-open-data** MCP server.
This document summarises its security posture and how to report a vulnerability.

## Reporting a vulnerability

Please open a private security advisory on the GitHub repository, or contact the
maintainer listed in `README.md`. Do not file public issues for exploitable
vulnerabilities.

## Posture summary

All seven tools only issue read requests against the public TERMDAT v2 API
(`api.termdat.bk.admin.ch`); there are no write, send, or filesystem
capabilities, and no personal data is processed.

| Area | Control |
|---|---|
| Egress | Fixed HTTPS base URL to `api.termdat.bk.admin.ch` only; no user-supplied URLs, so no SSRF surface |
| TLS | httpx certificate verification is on by default and never disabled in code |
| Auth / secrets | Unauthenticated public API — no API keys, tokens or secrets are stored or forwarded |
| Input | Pydantic v2 validation at all tool boundaries; query parameters are URL-encoded |
| Tools | All annotated `readOnlyHint: true`, `destructiveHint: false`; no dynamic or remote tool registration |
| Errors | Upstream RFC 9110 error bodies are surfaced as structured data, never silently swallowed |
| Stdout | Reserved for the JSON-RPC stream; the server emits no stray stdout logging |
| Binding | `stdio` by default (no network surface). SSE binds to `HOST` (default `0.0.0.0` for cloud); set `HOST=127.0.0.1` for local-only use |

## Accepted risks (portfolio-level controls)

The following are handled at the MCP gateway / host layer rather than inside
this single server. Residual risk here is low because the server is read-only,
unauthenticated, and reaches only one trusted public-data provider.

- **Session crypto-binding** — not applicable: there is no user identity to bind,
  as the server exposes public data with no authentication.
- **Cross-server tool-poisoning detection** — a gateway/host responsibility. This
  server's tool definitions are version-controlled, authored in-repo, and
  reviewed via PR; there is no dynamic or remote tool registration.
- **Network binding for hosted deployments** — the SSE transport defaults to
  `0.0.0.0` for cloud hosting. Front it with a reverse proxy / gateway that
  enforces TLS and access control, or set `HOST=127.0.0.1` for local use.

## Re-evaluation triggers

Revisit these acceptances if the server ever:

- gains **write** capability or starts processing **PII**, or
- adds an **authentication** model (then implement bound, TTL'd,
  server-side-invalidated session IDs and re-audit before merge), or
- registers tools **dynamically** / from remote sources, or
- is aggregated behind a shared MCP gateway (then enable the gateway's tool
  allow-listing and tool-poisoning detection).
