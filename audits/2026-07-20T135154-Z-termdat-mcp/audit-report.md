# MCP-Server Audit-Report — `termdat-mcp`

**Audit-Datum:** 2026-07-20
**Skill-Version:** 1.0.0
**Catalog-Version:** hash:091f446b2796

---

## 1. Executive Summary

Server `termdat-mcp` wurde gegen 35 anwendbare Best-Practice-Checks geprüft. 16 bestanden, 19 Findings dokumentiert (0 critical, 11 high, 8 medium, 0 low). Production-Readiness: erreicht.

**Production-Readiness:** YES

---

## 2. Profil-Snapshot

| Feld | Wert |
|---|---|
| Server-Name | `termdat-mcp` |
| Audit-Datum | 2026-07-20 |
| Skill-Version | 1.0.0 |
| Catalog-Version | hash:091f446b2796 |
| transport | `dual` |
| auth_model | `none` |
| data_class | `Public Open Data` |
| write_capable | `False` |
| deployment | `['local-stdio']` |
| uses_sampling | `False` |
| tools_make_external_requests | `True` |
| stadt_zuerich_context | `False` |
| schulamt_context | `False` |
| data_source.is_swiss_open_data | `True` |

---

## 3. Applicability

### Status pro Kategorie

| Kategorie | Pass | Fail | Partial | Todo | N/A |
|---|---|---|---|---|---|
| ARCH | 5 | 0 | 6 | 0 | 0 |
| CH | 1 | 0 | 0 | 0 | 0 |
| OBS | 1 | 1 | 2 | 0 | 0 |
| OPS | 1 | 0 | 2 | 0 | 0 |
| SCALE | 0 | 0 | 1 | 0 | 0 |
| SDK | 1 | 0 | 3 | 0 | 0 |
| SEC | 7 | 0 | 4 | 0 | 1 |
| **Total** | **16** | **1** | **18** | **0** | **1** |

---

## 4. Findings-Übersicht

_Policy: `fail-or-partial`_

| ID | Category | Severity | Status |
|---|---|---|---|
| ARCH-004 | ARCH | high | partial |
| OBS-001 | OBS | high | partial |
| OBS-002 | OBS | high | partial |
| OPS-001 | OPS | high | partial |
| SCALE-002 | SCALE | high | partial |
| SDK-001 | SDK | high | partial |
| SDK-004 | SDK | high | partial |
| SEC-005 | SEC | high | partial |
| SEC-007 | SEC | high | partial |
| SEC-018 | SEC | high | partial |
| SEC-021 | SEC | high | partial |
| ARCH-002 | ARCH | medium | partial |
| ARCH-007 | ARCH | medium | partial |
| ARCH-008 | ARCH | medium | partial |
| ARCH-011 | ARCH | medium | partial |
| ARCH-012 | ARCH | medium | partial |
| OBS-003 | OBS | medium | fail |
| OPS-002 | OPS | medium | partial |
| SDK-003 | SDK | medium | partial |

**Gesamt:** 19 Findings

---

## 5. Detail-Findings

### ARCH-002

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


### ARCH-004

## Finding: ARCH-004 — IoC: Transport-agnostische Server-Logik

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** ARCH-004

### Observed Behavior
Transport selection works and tools never touch the request, but configuration uses raw os.environ and a module-global client rather than a Settings object.

### Expected Behavior
Configuration via a pydantic-settings object; shared setup provided through lifespan rather than module globals.

### Evidence
- Dual transport selectable via TERMDAT_MCP_TRANSPORT (server + __main__)
- Tools are transport-agnostic; no direct request access

### Gaps
- Config read directly from os.environ, not a pydantic-settings object
- Module-global mcp and _client instead of a settings/lifespan-provided instance

### Remediation
Introduce a pydantic-settings Settings model; provide the client via a FastMCP lifespan (see SDK-001).

### Effort Estimate
M


### ARCH-007

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


### ARCH-008

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


### ARCH-011

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


### ARCH-012

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


### OBS-001

## Finding: OBS-001 — Protocol vs. Execution Errors

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** OBS-001

### Observed Behavior
Execution vs protocol error separation is handled by FastMCP's default exception-to-isError behaviour, but there is no explicit handling and limited error-path test coverage.

### Expected Behavior
Explicit isError results for execution errors and dedicated tests for both execution- and protocol-error paths.

### Evidence
- Tool argument errors raised as ValueError -> FastMCP returns them as tool execution errors (isError), not JSON-RPC errors
- api_status catches upstream failure and returns a structured reachable=false result

### Gaps
- No explicit isError construction; relies on FastMCP default exception handling
- Error-path test coverage is thin

### Remediation
Add tests asserting tool-level errors for invalid args/upstream failure.

### Effort Estimate
S


### OBS-002

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


### OBS-003

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


### OPS-001

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


### OPS-002

## Finding: OPS-002 — Doku-Standard: CONTRIBUTING

**Severity:** medium
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** OPS-002

### Observed Behavior
Documentation is strong and bilingual, but there is no standalone bilingual CONTRIBUTING.md.

### Expected Behavior
A bilingual CONTRIBUTING.md at repo root.

### Evidence
- README has all 8 mandatory sections incl. ASCII architecture diagram and Known Limitations; README.de.md parallel; CHANGELOG Keep-a-Changelog

### Gaps
- No separate bilingual CONTRIBUTING.md (only a Contributing section in the READMEs)

### Remediation
Add CONTRIBUTING.md / CONTRIBUTING.de.md (build, test, changelog, tool-read-only rule).

### Effort Estimate
S


### SCALE-002

## Finding: SCALE-002 — Stateful Load Balancing (SSE)

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** SCALE-002

### Observed Behavior
The SSE transport is available but there is no stateful load-balancing design; acceptable for single-instance/local use, not yet for horizontal cloud deployment.

### Expected Behavior
Sticky sessions on Mcp-Session-Id or a shared-state session manager with explicit TTL before horizontal scaling.

### Evidence
- Server is single-instance and not cloud-deployed (deployment: local-stdio; is_cloud_deployed=false)

### Gaps
- SSE transport is offered but there is no sticky-session/shared-state design, session TTL or failover story

### Remediation
Defer until cloud deployment; then add edge sticky-sessions or a Redis session store with TTL. Document as an accepted risk for now.

### Effort Estimate
M


### SDK-001

## Finding: SDK-001 — FastMCP Lifespan + Client-Cleanup

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** SDK-001

### Observed Behavior
The anti-pattern (a client per call) is avoided, but there is no FastMCP lifespan, so the shared httpx client is never cleanly closed on shutdown.

### Expected Behavior
A @asynccontextmanager lifespan that owns the client and closes it on exit.

### Evidence
- Single shared httpx.AsyncClient is created lazily and reused across calls (client.py _client()) — no per-call client

### Gaps
- No FastMCP lifespan; the shared httpx client is never closed on shutdown (aclose() exists but is unwired)

### Remediation
Add a FastMCP lifespan that constructs TermdatClient and awaits aclose() in finally; pass lifespan=... to FastMCP.

### Effort Estimate
M


### SDK-003

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


### SDK-004

## Finding: SDK-004 — CORS Mcp-Session-Id

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** SDK-004

### Observed Behavior
The SSE transport ships without explicit CORS configuration, so Mcp-Session-Id exposure and origin restriction are unaddressed.

### Expected Behavior
CORS middleware exposing/allowing Mcp-Session-Id with an explicit (non-wildcard) origin list in production.

### Evidence
- stdio is the default transport; SSE is opt-in and not cloud-deployed

### Gaps
- No CORS middleware configured for the SSE transport; Mcp-Session-Id is not explicitly exposed; allow_origins not restricted

### Remediation
Configure CORS on the SSE app (expose_headers/allow_headers = Mcp-Session-Id; explicit allow_origins) before browser/cloud SSE use.

### Effort Estimate
S


### SEC-005

## Finding: SEC-005 — DNS-Rebinding-Prevention

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** SEC-005

### Observed Behavior
DNS is not pinned, but every request targets one hardcoded trusted host with no user-controlled hostname, so DNS-rebinding risk is minimal.

### Expected Behavior
Pin DNS once per request and reuse the resolved IP, preserving Host/SNI (or accept the risk via ADR for a single trusted host).

### Evidence
- All egress targets a single hardcoded trusted host (api.termdat.bk.admin.ch); no user-controlled hostnames

### Gaps
- No DNS pinning; httpx resolves per request (TOCTOU-theoretical only, single trusted host)

### Remediation
Accept as low risk for a single hardcoded host (mirror fedlex ADR 0001), or add a pinning transport if egress ever broadens.

### Effort Estimate
S


### SEC-007

## Finding: SEC-007 — Container-Sandboxing

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** SEC-007

### Observed Behavior
There is no container artifact yet, so container-sandboxing controls are not expressed; required before any container deployment.

### Expected Behavior
A hardened Dockerfile (non-root UID>=10000) and k8s securityContext (runAsNonRoot, readOnlyRootFilesystem, cap drop ALL, seccomp).

### Evidence
- Server runs locally via stdio by default; no container is shipped

### Gaps
- No Dockerfile / k8s manifests, so non-root USER, readOnlyRootFilesystem, cap-drop, seccomp are not yet expressed

### Remediation
Add a hardened Dockerfile + k8s manifest when containerising; until then the server is stdio/local only.

### Effort Estimate
M


### SEC-018

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


### SEC-021

## Finding: SEC-021 — Egress-Allow-List

**Severity:** high
**Status:** open
**Server:** termdat-mcp
**Check-Reference:** SEC-021

### Observed Behavior
Egress is de-facto pinned to one hardcoded host, but there is no formal frozenset allow-list / pre-request assertion or network-egress documentation.

### Expected Behavior
A frozenset egress allow-list enforced by assert_host_allowed before each request, plus network-layer egress docs.

### Evidence
- All requests go to the hardcoded BASE_URL/SPEC_URL (single host); no user-controlled URLs

### Gaps
- Egress host is a module constant, not a frozenset allow-list with an assert_host_allowed pre-request check; no network-egress docs

### Remediation
Add a frozenset allow-list checked before requests, and a docs/network-egress.md note.

### Effort Estimate
S


---

## 6. Remediation-Plan

### Empfohlene Reihenfolge

1. **ARCH-004** (high, partial)
2. **OBS-001** (high, partial)
3. **OBS-002** (high, partial)
4. **OPS-001** (high, partial)
5. **SCALE-002** (high, partial)
6. **SDK-001** (high, partial)
7. **SDK-004** (high, partial)
8. **SEC-005** (high, partial)
9. **SEC-007** (high, partial)
10. **SEC-018** (high, partial)
11. **SEC-021** (high, partial)
12. **ARCH-002** (medium, partial)
13. **ARCH-007** (medium, partial)
14. **ARCH-008** (medium, partial)
15. **ARCH-011** (medium, partial)
16. **ARCH-012** (medium, partial)
17. **OBS-003** (medium, fail)
18. **OPS-002** (medium, partial)
19. **SDK-003** (medium, partial)

---

## 7. Audit-Metadata

| Feld | Wert |
|---|---|
| skill_version | `1.0.0` |
| catalog_version | `hash:091f446b2796` |
| audit_date | `2026-07-20` |


_Generated by tools/build_report.py — do not edit by hand._

---

## 8. Remediation applied during this audit run

Two fixes were applied to `termdat-mcp` while this audit was in progress and are
reflected in the final results above:

| Check | Before | Fix | Result |
|---|---|---|---|
| **SEC-016** (critical) | SSE bound to `0.0.0.0` by default (`__main__.py`) — NeighborJack exposure | Default changed to `127.0.0.1`; `0.0.0.0` is now an explicit opt-in that warns on stderr outside a container; README + SECURITY updated | **fail → pass** (unblocks production-readiness) |
| **OBS-002** (high) | `api_status` forwarded the raw upstream exception string to the model | Raw exception text removed from the tool result | partial (improved; full masking still blocked by the SDK version — see finding) |

With SEC-016 remediated there are **no open critical/high failures**, so the
server reaches production-readiness. The remaining 19 findings (0 critical,
11 high, 8 medium — all `partial` except OBS-003) form the post-release
hardening backlog and do not block the portfolio listing.
