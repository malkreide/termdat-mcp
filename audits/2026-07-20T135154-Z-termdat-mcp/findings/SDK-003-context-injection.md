## Finding: SDK-003 — Context Injection

**Severity:** medium
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** SDK-003

### Observed Behavior
No tool uses Context injection; the potentially slow check_terms reports no progress and logs no warnings via ctx.

### Expected Behavior
ctx: Context on long-running tools with ctx.report_progress() and ctx.warning()/error() instead of silent handling.

### Evidence
- Most tools are single upstream calls (<2s)

### Gaps
- No ctx: Context injection anywhere; check_terms (up to 25 sequential calls) can exceed 2s with no progress reporting

### Remediation
Add ctx to check_terms; report progress per term and surface partial failures via ctx.warning().

### Effort Estimate
S
