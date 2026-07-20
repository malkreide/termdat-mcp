## Finding: OBS-003 — Structured Logging

**Severity:** medium
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** OBS-003

### Observed Behavior
The server performs no logging at all: there is no structured logger, no severity levels and no per-call context.

### Expected Behavior
A structured logger (structlog/loguru) writing JSON/logfmt to stderr with >=4 severity levels and per-call bound context.

### Evidence
- No print()/stdout writes in src/ (good for stdio hygiene, OBS-004)

### Gaps
- No structured logging library (structlog/loguru) in dependencies; no logging at all
- No per-call bound context (tool name, correlation id)

### Remediation
Add structlog with a WriteLoggerFactory(file=sys.stderr); bind tool name + a correlation id per call; log at info/warning/error.

### Effort Estimate
M
