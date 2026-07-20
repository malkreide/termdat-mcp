## Finding: SDK-004 — CORS Mcp-Session-Id

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** SDK-004

### Observed Behavior
The SSE transport ships without explicit CORS configuration, so Mcp-Session-Id exposure and origin restriction are unaddressed.

### Expected Behavior
CORS middleware exposing/allowing Mcp-Session-Id with an explicit (non-wildcard) origin list in production.

### Evidence
- stdio is the default transport; SSE is opt-in and not cloud-deployed

### Gaps
- No CORS middleware configured for the SSE transport; Mcp-Session-Id is not explicitly exposed; allow_origins not restricted

### Remediation
Configure CORS on the SSE app (expose_headers/allow_headers = Mcp-Session-Id; explicit allow_origins) before browser/cloud SSE use.

### Effort Estimate
S
