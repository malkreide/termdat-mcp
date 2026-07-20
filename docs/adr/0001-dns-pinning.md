# ADR 0001 — DNS pinning is an accepted risk (SEC-005)

**Status:** accepted
**Context:** DNS-rebinding / TOCTOU prevention for outbound requests.

## Decision

`termdat-mcp` does **not** implement per-request DNS pinning. httpx resolves the
hostname per request in the normal way.

## Rationale

- **No user-controlled destination.** Every outbound request targets a single
  hardcoded, HTTPS-only host (`api.termdat.bk.admin.ch`), enforced before each
  request by the code-layer egress allow-list (`assert_host_allowed`, SEC-021).
  No tool argument can influence the scheme, host, or path.
- DNS-rebinding attacks require an attacker who controls the hostname being
  resolved (to swap a benign IP for an internal one between check and use). That
  precondition does not exist here.
- TLS certificate validation is on by default and pins trust to the
  `api.termdat.bk.admin.ch` certificate regardless of the resolved IP.

## Re-evaluation triggers

Implement DNS pinning (resolve once, connect to the pinned IP, keep Host/SNI) if
the server ever:

- accepts a user- or config-supplied destination host, or
- broadens the egress allow-list beyond a small set of trusted government hosts.
