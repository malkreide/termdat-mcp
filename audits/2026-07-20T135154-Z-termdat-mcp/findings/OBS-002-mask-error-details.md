## Finding: OBS-002 — Mask Error Details

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** OBS-002

### Observed Behavior
Stacktraces are never returned and api_status was hardened to drop the raw exception string, but the pinned SDK has no mask_error_details flag, so raised exception messages still surface as tool-error text.

### Expected Behavior
mask_error_details=True (or equivalent) so upstream/internal error text never reaches the model.

### Evidence
- api_status no longer forwards the raw exception text to the model (masked in this audit run)
- No traceback.format_exc()/exc_info in any tool return

### Gaps
- FastMCP 1.28.1 exposes no mask_error_details flag; raised ValueError/RuntimeError messages still reach the client as tool-error text

### Remediation
Wrap tool bodies to return sanitised isError messages, or adopt an SDK version exposing error masking.

### Effort Estimate
M
