## Finding: SCALE-002 — Stateful Load Balancing (SSE)

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** SCALE-002

### Observed Behavior
The SSE transport is available but there is no stateful load-balancing design; acceptable for single-instance/local use, not yet for horizontal cloud deployment.

### Expected Behavior
Sticky sessions on Mcp-Session-Id or a shared-state session manager with explicit TTL before horizontal scaling.

### Evidence
- Server is single-instance and not cloud-deployed (deployment: local-stdio; is_cloud_deployed=false)

### Gaps
- SSE transport is offered but there is no sticky-session/shared-state design, session TTL or failover story

### Remediation
Defer until cloud deployment; then add edge sticky-sessions or a Redis session store with TTL. Document as an accepted risk for now.

### Effort Estimate
M
