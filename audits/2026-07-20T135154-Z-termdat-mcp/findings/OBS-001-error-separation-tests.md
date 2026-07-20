## Finding: OBS-001 — Protocol vs. Execution Errors

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** OBS-001

### Observed Behavior
Execution vs protocol error separation is handled by FastMCP's default exception-to-isError behaviour, but there is no explicit handling and limited error-path test coverage.

### Expected Behavior
Explicit isError results for execution errors and dedicated tests for both execution- and protocol-error paths.

### Evidence
- Tool argument errors raised as ValueError -> FastMCP returns them as tool execution errors (isError), not JSON-RPC errors
- api_status catches upstream failure and returns a structured reachable=false result

### Gaps
- No explicit isError construction; relies on FastMCP default exception handling
- Error-path test coverage is thin

### Remediation
Add tests asserting tool-level errors for invalid args/upstream failure.

### Effort Estimate
S
