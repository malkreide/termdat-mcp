# ADR 0002 — Single-instance deployment; stateful LB deferred (SCALE-002)

**Status:** accepted
**Context:** Horizontal scaling of the SSE/HTTP transport.

## Decision

`termdat-mcp` is operated as a **single instance** (local stdio, or one SSE
container behind a reverse proxy). It does **not** implement sticky sessions or a
shared-state session manager, and it does not claim horizontal-scale readiness.

## Rationale

- The server is **stateless per request** except for an in-process 24 h cache of
  the two small controlled vocabularies (collections, classifications). That
  cache is a latency optimisation, not session state — any instance can serve any
  request, and a cold instance simply refetches.
- There is no user session, no auth, and no write path, so there is nothing to
  pin a client to a specific instance for.
- The SSE transport is offered primarily for a single hosted instance; the
  workload does not require multiple replicas.

## Consequences / re-evaluation

Before running **multiple SSE replicas** behind a load balancer, add one of:

- edge sticky sessions keyed on `Mcp-Session-Id` (HAProxy/Nginx/Ingress), or
- a shared session store (e.g. Redis) with an explicit TTL,

and add a failover test. Until then, run a single replica; scale vertically.
