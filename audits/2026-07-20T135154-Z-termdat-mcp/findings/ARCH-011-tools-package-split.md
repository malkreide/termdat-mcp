## Finding: ARCH-011 — Standardisierte Repo-Struktur

**Severity:** medium
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** ARCH-011

### Observed Behavior
Repo structure is standard, but all 7 tools sit in one server.py where the catalog suggests a tools/ package for >5 tools.

### Expected Behavior
Split tools into a tools/ package (file-per-group) for >5 tools, or document the single-file choice.

### Evidence
- All mandatory top-level files present (README.md, README.de.md, CHANGELOG.md, LICENSE, pyproject.toml)
- src/ layout, tests/, .github/workflows/ (ci.yml + publish.yml) present

### Gaps
- 7 tools live in a single server.py; catalog suggests a tools/ split for >5 tools
- CI workflow named ci.yml, catalog names test.yml (cosmetic)

### Remediation
Optionally split server.py into a tools/ package; or add a one-line rationale in the README.

### Effort Estimate
S
