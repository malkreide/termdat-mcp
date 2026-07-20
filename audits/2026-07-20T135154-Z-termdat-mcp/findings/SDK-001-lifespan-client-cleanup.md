## Finding: SDK-001 — FastMCP Lifespan + Client-Cleanup

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** SDK-001

### Observed Behavior
The anti-pattern (a client per call) is avoided, but there is no FastMCP lifespan, so the shared httpx client is never cleanly closed on shutdown.

### Expected Behavior
A @asynccontextmanager lifespan that owns the client and closes it on exit.

### Evidence
- Single shared httpx.AsyncClient is created lazily and reused across calls (client.py _client()) — no per-call client

### Gaps
- No FastMCP lifespan; the shared httpx client is never closed on shutdown (aclose() exists but is unwired)

### Remediation
Add a FastMCP lifespan that constructs TermdatClient and awaits aclose() in finally; pass lifespan=... to FastMCP.

### Effort Estimate
M
