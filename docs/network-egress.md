# Network egress (SEC-021)

`termdat-mcp` reaches exactly **one** external host.

## Code-layer allow-list

`src/termdat_mcp/client.py` defines an immutable allow-list and enforces it
before every outbound request:

```python
ALLOWED_HOSTS = frozenset({"api.termdat.bk.admin.ch"})

def assert_host_allowed(url: str) -> None:
    # rejects non-https and any host outside ALLOWED_HOSTS
    ...
```

`fetch_with_retry()` calls `assert_host_allowed()` first, so a bug or an injected
URL cannot cause a request to any other host. The allow-list is a module-level
`frozenset` — it is not configurable or mutable at runtime.

| Host | Scheme | Purpose |
|---|---|---|
| `api.termdat.bk.admin.ch` | https | TERMDAT v2 API (search, entries, vocabularies) |

## Network-layer control (deployment)

When deploying the SSE container, pair the code-layer allow-list with a
network-layer egress control so the pod/VM can only reach the host above:

- **Kubernetes:** a `NetworkPolicy` with an egress rule to the TERMDAT host on 443.
- **Cloud:** a security-group / firewall egress rule, or an egress proxy allow-list.

## Updating the allow-list

Changing the set of reachable hosts is a code change (edit `ALLOWED_HOSTS`),
reviewed via pull request — never a runtime configuration toggle.
