## Finding: ARCH-007 — Capability-Aggregation: Parallelisierung

**Severity:** medium
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** ARCH-007

### Observed Behavior
Aggregating tools return complete results, but check_terms issues its per-term upstream searches sequentially.

### Expected Behavior
Where aggregation applies, parallelise upstream calls with asyncio.gather.

### Evidence
- Tools return self-contained results (TermEntry/TranslationHit), not pointers

### Gaps
- check_terms iterates up to 25 terms sequentially; no asyncio.gather parallelisation

### Remediation
Gather the per-term searches in check_terms with asyncio.gather (bounded concurrency).

### Effort Estimate
S
