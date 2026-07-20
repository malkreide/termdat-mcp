## Finding: SEC-005 — DNS-Rebinding-Prevention

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** SEC-005

### Observed Behavior
DNS is not pinned, but every request targets one hardcoded trusted host with no user-controlled hostname, so DNS-rebinding risk is minimal.

### Expected Behavior
Pin DNS once per request and reuse the resolved IP, preserving Host/SNI (or accept the risk via ADR for a single trusted host).

### Evidence
- All egress targets a single hardcoded trusted host (api.termdat.bk.admin.ch); no user-controlled hostnames

### Gaps
- No DNS pinning; httpx resolves per request (TOCTOU-theoretical only, single trusted host)

### Remediation
Accept as low risk for a single hardcoded host (mirror fedlex ADR 0001), or add a pinning transport if egress ever broadens.

### Effort Estimate
S
