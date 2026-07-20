## Finding: ARCH-004 — IoC: Transport-agnostische Server-Logik

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** ARCH-004

### Observed Behavior
Transport selection works and tools never touch the request, but configuration uses raw os.environ and a module-global client rather than a Settings object.

### Expected Behavior
Configuration via a pydantic-settings object; shared setup provided through lifespan rather than module globals.

### Evidence
- Dual transport selectable via TERMDAT_MCP_TRANSPORT (server + __main__)
- Tools are transport-agnostic; no direct request access

### Gaps
- Config read directly from os.environ, not a pydantic-settings object
- Module-global mcp and _client instead of a settings/lifespan-provided instance

### Remediation
Introduce a pydantic-settings Settings model; provide the client via a FastMCP lifespan (see SDK-001).

### Effort Estimate
M
