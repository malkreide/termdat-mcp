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
