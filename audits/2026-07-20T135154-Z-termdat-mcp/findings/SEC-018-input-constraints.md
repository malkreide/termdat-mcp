## Finding: SEC-018 — Input-Validation Constraints

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** SEC-018

### Observed Behavior
Core validation (language and field whitelists, term/empty guards, typed args) is present, but numeric args lack ge/le bounds, strings lack length limits, and strict/extra=forbid are not set.

### Expected Behavior
ge/le on numeric args, min/max_length on strings, and strict=True / extra='forbid' on tool input models.

### Evidence
- Language codes whitelisted (normalise_language); search fields whitelisted; empty/25-term guards; Pydantic-typed args and returns

### Gaps
- max_results has no ge/le bound
- No min/max_length on string args
- strict=True / extra='forbid' not set on tool inputs

### Remediation
Constrain max_results (e.g. ge=1, le=100); add length bounds; enable strict input models.

### Effort Estimate
S
