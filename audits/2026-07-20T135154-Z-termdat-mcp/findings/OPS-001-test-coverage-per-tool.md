## Finding: OPS-001 — Test-Strategie

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** OPS-001

### Observed Behavior
The mocked-unit + live-marked split and CI wiring are in place, but coverage is ~12 tests for 7 tools and there is no scheduled live-test workflow.

### Expected Behavior
>=5 unit tests per tool and a separate nightly/manual live-test workflow.

### Evidence
- tests/test_client.py (respx-mocked) + tests/test_live.py (live-marked); live marker registered in pyproject; CI runs pytest -m 'not live'

### Gaps
- 12 offline tests total across 7 tools (< 5 per tool)
- No separate nightly/manual live-test workflow

### Remediation
Add per-tool unit tests (edge cases) and a scheduled workflow_dispatch/nightly job running -m live.

### Effort Estimate
M
