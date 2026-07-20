## Finding: ARCH-012 — protocolVersion-Pinning + SDK-Disziplin

**Severity:** medium
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** ARCH-012

### Observed Behavior
CHANGELOG, protocol-version README section and Dependabot are present, but the MCP protocolVersion is negotiated by the SDK rather than pinned in code (the FastMCP norm).

### Expected Behavior
Pin protocolVersion explicitly, or document that the SDK negotiates it (portfolio-consistent).

### Evidence
- CHANGELOG.md in Keep-a-Changelog format; README has 'MCP Protocol Version' section; Dependabot active

### Gaps
- protocolVersion is negotiated by the FastMCP SDK at the initialize handshake, not pinned in server code

### Remediation
Document the SDK-negotiation policy in the README's MCP Protocol Version section (already partly present); pin if the SDK later exposes it.

### Effort Estimate
S
