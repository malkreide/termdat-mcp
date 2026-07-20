## Finding: SEC-021 — Egress-Allow-List

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** SEC-021

### Observed Behavior
Egress is de-facto pinned to one hardcoded host, but there is no formal frozenset allow-list / pre-request assertion or network-egress documentation.

### Expected Behavior
A frozenset egress allow-list enforced by assert_host_allowed before each request, plus network-layer egress docs.

### Evidence
- All requests go to the hardcoded BASE_URL/SPEC_URL (single host); no user-controlled URLs

### Gaps
- Egress host is a module constant, not a frozenset allow-list with an assert_host_allowed pre-request check; no network-egress docs

### Remediation
Add a frozenset allow-list checked before requests, and a docs/network-egress.md note.

### Effort Estimate
S
