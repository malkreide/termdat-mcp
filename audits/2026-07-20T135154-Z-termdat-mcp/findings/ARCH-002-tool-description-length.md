## Finding: ARCH-002 — Tool-Beschreibung mit Use-Case-Tags

**Severity:** medium
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** ARCH-002

### Observed Behavior
Tool descriptions are informative but the shortest ones (list_collections, api_status) pull the median just under 100 chars; no explicit use-case tag.

### Expected Behavior
Median description >=100 chars and an explicit use-case tag (or documented equivalent) in >=80% of tools.

### Evidence
- Rich docstrings on search_terms/translate_term/check_terms with scope caveats and differentiation

### Gaps
- Median description length ~90 chars (list_collections/api_status are one-liners), just under the 100-char bar
- No formal <use_case> tag (contextual equivalent only)

### Remediation
Extend the one-line tool descriptions with a short use-case clause.

### Effort Estimate
S
