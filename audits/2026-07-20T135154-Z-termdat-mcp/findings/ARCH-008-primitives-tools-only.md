## Finding: ARCH-008 — Drei Primitive nutzen

**Severity:** medium
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** ARCH-008

### Observed Behavior
Only the Tools primitive is used; the static vocabulary listings could be Resources, and there is no documented justification for tools-only.

### Expected Behavior
Use >=2 primitives or document in the README why only Tools are used; assess vocab listings for Resource migration.

### Evidence
- Server exposes Tools primitive only

### Gaps
- No Resources or Prompts; no README justification for tools-only
- Static vocabularies (list_collections/list_classifications) are Resource-migration candidates

### Remediation
Add a short 'MCP Primitives' justification to the README, or expose the vocabularies as Resources.

### Effort Estimate
S
