"""TERMDAT public API client (api.termdat.bk.admin.ch, OpenAPI 3.0.4, no auth).

Architecture A (live API only). Only the two small controlled vocabularies
(140 collections, 23 classifications) are cached, because they change rarely
and are needed to make filter arguments legible to an agent.
"""

from __future__ import annotations

import asyncio
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlsplit

import httpx

from . import __version__
from .logging_config import log

BASE_URL = "https://api.termdat.bk.admin.ch/v2"
SPEC_URL = "https://api.termdat.bk.admin.ch/swagger/v2/swagger.json"
VOCAB_TTL_SECONDS = 24 * 60 * 60

# Code-layer egress allow-list (SEC-021): the only host this server may reach.
# Enforced before every outbound request; not mutable at runtime.
ALLOWED_HOSTS = frozenset({"api.termdat.bk.admin.ch"})

# --- Retry policy (ARCH-014) ------------------------------------------------
# *What* is retried is settled in `fetch_with_retry` (4xx except 429 fails
# fast). These settle *how fast*.

# Ceiling on a single wait. Guards the exponential ladder, which would otherwise
# grow without bound, and a `Retry-After` TERMDAT is entitled to send but that
# we are not obliged to sit through.
MAX_DELAY_S = 20.0

# Ceiling on the *whole* call — every attempt, every wait, together.
#
# An attempt count is not a bound: four attempts at a 60s per-request timeout
# plus backoff are over four minutes, and the number `4` never says so. Worse,
# the relevant limit is not ours. The caller has its own timeout, and past it
# nobody is listening any more — the work continues, the load lands on TERMDAT,
# and the result goes nowhere.
#
# The anchor is measured, not guessed: the Python MCP SDK ships
# ``MCP_DEFAULT_TIMEOUT = 30.0`` for general operations
# (``mcp/shared/_httpx_utils.py``). 25s leaves headroom for MCP framing,
# response parsing and the tool layer on top of the fetch.
#
# The trade-off is deliberate: a slow first attempt can consume the budget and
# leave no room for a retry. That is the intended answer — a retry that
# finishes after the caller gave up buys nothing and costs TERMDAT a request.
TOTAL_BUDGET_S = 25.0

# Per-operation ceiling (connect, read, write, pool) — httpx applies it to each,
# not to the call as a whole. `TOTAL_BUDGET_S` bounds the whole call; the
# effective per-attempt timeout is the smaller of the two.
REQUEST_TIMEOUT_S = 25.0

# Jitter spread. Without it every client that hit the same outage retries in
# lockstep, and the load returns as a wave exactly when the API recovers — the
# retry storm extends the outage it was meant to bridge.
JITTER_SPREAD = 0.5  # exponential delays land in [0.5x, 1.5x]

# On a `Retry-After` the spread is one-sided: the API said when to come back,
# so later is polite and earlier would ignore the very value we just read.
RETRY_AFTER_JITTER = 0.25  # lands in [1.0x, 1.25x]

# Statuses that carry a meaningful `Retry-After` (RFC 9110 §10.2.3).
RETRY_AFTER_STATUSES = frozenset({429, 503})


def parse_retry_after(resp: httpx.Response | None) -> float | None:
    """Seconds to wait per the response's ``Retry-After``, or None.

    RFC 9110 §10.2.3 allows two forms: delta-seconds (``120``) and an HTTP-date
    (``Wed, 21 Oct 2026 07:28:00 GMT``). Both occur, so both are read. Anything
    unparseable yields None and the caller falls back to its own curve — a
    malformed header must not become a crash on the error path.
    """
    if resp is None or resp.status_code not in RETRY_AFTER_STATUSES:
        return None
    raw = (resp.headers.get("Retry-After") or "").strip()
    if not raw:
        return None
    if raw.isdigit():
        return float(raw)
    try:
        when = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:  # RFC 9110 dates are GMT; a naive one means UTC
        when = when.replace(tzinfo=timezone.utc)
    # Past date means "now".
    return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())


def retry_delay(attempt: int, last_error: Exception | None) -> float:
    """Seconds to wait before ``attempt``.

    The API's own answer beats our guess: a ``Retry-After`` on a 429 or 503 wins
    over the exponential curve, which is guessing at the same question.
    """
    hinted = parse_retry_after(getattr(last_error, "response", None))
    if hinted is not None:
        capped = min(hinted, MAX_DELAY_S)
        return capped * (1.0 + random.random() * RETRY_AFTER_JITTER)
    capped = min(float(2**attempt), MAX_DELAY_S)
    return capped * (1.0 - JITTER_SPREAD + random.random() * 2 * JITTER_SPREAD)


class EgressNotAllowed(RuntimeError):
    """Raised when a request targets a host outside the egress allow-list."""


def assert_host_allowed(url: str) -> None:
    """Reject any URL whose scheme is not https or whose host is not allow-listed."""
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise EgressNotAllowed(f"non-https egress blocked: {parts.scheme!r}")
    if parts.hostname not in ALLOWED_HOSTS:
        raise EgressNotAllowed(f"host not in egress allow-list: {parts.hostname!r}")

VALID_LANGUAGES = ("DE", "FR", "IT", "EN", "RM", "LA")

# The 11 searchable fields exposed by the API as Field.* boolean flags.
SEARCH_FIELDS = (
    "Terminus",
    "Name",
    "Abbreviation",
    "Phraseology",
    "Definition",
    "Note",
    "Context",
    "Source",
    "Metadata",
    "Country",
    "Comment",
)

# Fields that carry a *designation* rather than free text. Translation and QA
# lookups stay inside these: a term mentioned in a definition is not a synonym.
DESIGNATION_FIELDS = ("Terminus", "Name", "Abbreviation", "Phraseology")

# Default for open-ended search. The API's own defaults are the four designation
# fields only, which misses entries that name the term in their definition, note
# or source — see the "Quellensteuer" case in issue #11.
DEFAULT_SEARCH_FIELDS = (*DESIGNATION_FIELDS, "Definition", "Note", "Source")


class UpstreamUnavailable(RuntimeError):
    """Raised when TERMDAT stays unreachable after all retries."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalise_language(code: str, *, field: str = "language") -> str:
    """TERMDAT accepts two-letter ISO codes, case-insensitively; 'de-CH' and 'deu' are rejected."""
    value = (code or "").strip().upper()
    if value not in VALID_LANGUAGES:
        raise ValueError(
            f"{field} must be one of {', '.join(VALID_LANGUAGES)} — got {code!r}. "
            "Locale forms such as 'de-CH' and three-letter codes such as 'deu' are rejected upstream."
        )
    return value


async def fetch_with_retry(
    http: httpx.AsyncClient,
    url: str,
    params: dict[str, Any] | None = None,
    *,
    max_attempts: int = 4,
    total_budget: float = TOTAL_BUDGET_S,
) -> httpx.Response:
    """GET with jittered exponential backoff (2s/4s/8s, capped at MAX_DELAY_S).

    A ``Retry-After`` sent by TERMDAT on a 429 or 503 overrides that curve; see
    :func:`retry_delay`. 4xx except 429 fails fast.

    ``total_budget`` bounds the whole call — attempts and waits together — and
    is the limit that actually matters: past the caller's own timeout nobody
    receives the answer any more.
    """
    assert_host_allowed(url)  # SEC-021: enforce the egress allow-list per request
    deadline = time.monotonic() + total_budget
    last_error: Exception | None = None
    attempts = 0
    for attempt in range(max_attempts):
        if attempt > 0:
            delay = retry_delay(attempt, last_error)
            # A wait that outlasts the budget is a wait for nobody: the caller
            # has given up by the time it ends. Stop instead.
            if delay >= deadline - time.monotonic():
                break
            await asyncio.sleep(delay)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        attempts += 1
        try:
            # The budget wins over the per-operation ceiling once it is the
            # tighter of the two — otherwise a single slow attempt could
            # outlast the whole allowance.
            resp = await http.get(
                url, params=params, timeout=min(REQUEST_TIMEOUT_S, remaining)
            )
            resp.raise_for_status()
            return resp
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            last_error = exc
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status is not None and 400 <= status < 500 and status != 429:
                raise
            log.warning(
                "termdat.request_retry", attempt=attempt + 1, status=status, error=type(exc).__name__
            )
    if last_error is None:  # budget gone before a single request went out
        raise UpstreamUnavailable(
            f"TERMDAT not attempted: {total_budget:g}s budget already spent "
            f"(host={urlsplit(url).hostname})"
        )
    # OBS-002: log the concrete error to stderr, but do not leak it to the model.
    # OBS-007: name the *type* as well. httpx timeout and connect errors carry an
    # empty ``str()``, so ``error=str(last_error)`` alone left this event — the
    # one that matters — with an empty field, while the retry line above had the
    # type all along. A structured event with a filled ``attempts`` field looks
    # complete; an empty ``error`` field is easy to miss in JSON.
    #
    # Which limit ran out is part of that diagnosis: "all 4 attempts used" and
    # "the budget ran out after 2" call for different fixes — more patience in
    # the first case, a faster source or a wider budget in the second.
    why = (
        f"all {max_attempts} attempts used"
        if attempts >= max_attempts
        else f"{total_budget:g}s budget spent"
    )
    log.error(
        "termdat.unreachable",
        attempts=attempts,
        limit=why,
        host=urlsplit(url).hostname,
        error_type=type(last_error).__name__,
        error=str(last_error) or "no further detail",
    )
    raise UpstreamUnavailable(
        f"TERMDAT unreachable after {attempts} attempt(s), {why} "
        f"(host={urlsplit(url).hostname}): {type(last_error).__name__}"
    ) from last_error


def flatten_entry(raw: dict) -> dict:
    """Flatten one TERMDAT entry into the TermEntry shape."""

    def text_of(key: str) -> str:
        value = raw.get(key)
        return value.get("text", "") if isinstance(value, dict) else ""

    variants = []
    for detail in raw.get("languageDetails") or []:
        variants.append(
            {
                "language": detail.get("languageIsoCode", ""),
                "name": detail.get("name", ""),
                "sequence": detail.get("sequence"),
                "definition": detail.get("definition"),
                "note": detail.get("note"),
                "source": detail.get("nameSource"),
            }
        )

    return {
        "entry_id": raw.get("id", 0),
        "url": raw.get("url", ""),
        "status": text_of("status"),
        "reliability": text_of("reliability"),
        "office": text_of("office"),
        "collection": text_of("collection"),
        "classification": text_of("classification"),
        "subjects": [s.get("text", "") for s in (raw.get("subject") or []) if isinstance(s, dict)],
        "variants": variants,
    }


class TermdatClient:
    def __init__(self, http: httpx.AsyncClient | None = None, vocab_ttl: int = VOCAB_TTL_SECONDS):
        self._http = http
        self._own_http = http is None
        self._vocab_ttl = vocab_ttl
        self._vocab: dict[tuple[str, str], list[dict]] = {}
        self._vocab_at: dict[tuple[str, str], float] = {}
        self._vocab_iso: dict[tuple[str, str], str] = {}
        self._lock = asyncio.Lock()

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(
                # 60s used to sit here, above the whole retry budget — a value
                # that only claimed what it no longer grants.
                timeout=httpx.Timeout(REQUEST_TIMEOUT_S),
                headers={"User-Agent": f"termdat-mcp/{__version__}"},
            )
        return self._http

    async def aclose(self) -> None:
        if self._http is not None and self._own_http:
            await self._http.aclose()
            self._http = None

    async def _all_classification_ids(self) -> list[int] | None:
        """Every classification ID, so that an unfiltered search really is unfiltered.

        /v2/Search restricts an ID-less query to a "default set (=VARIA)" — one of
        23 subject areas, and the residual one at that. Sending the full set is the
        only way to search the whole database. Returns None if the vocabulary is
        unavailable: widening the search must never be able to break it.
        """
        try:
            values, _, _ = await self.vocabulary("Classification", "DE")
        except Exception:  # noqa: BLE001 — best-effort widening, never fatal
            log.warning("termdat.classification_widening_unavailable")
            return None
        return [v["id"] for v in values if isinstance(v.get("id"), int)] or None

    async def search(
        self,
        search_term: str,
        in_language: str = "DE",
        *,
        out_language: str | None = None,
        detail: bool = False,
        fields: tuple[str, ...] = DEFAULT_SEARCH_FIELDS,
        collection_ids: list[int] | None = None,
        classification_ids: list[int] | None = None,
        max_results: int = 25,
    ) -> tuple[list[dict], str]:
        """Call /v2/Search. Returns (flattened entries, retrieved_at).

        `classification_ids=None` means "search everything", which costs an extra
        (cached) vocabulary call — see `_all_classification_ids`. Pass an explicit
        list to narrow.
        """
        if not search_term.strip():
            raise ValueError("search_term must not be empty")
        for field in fields:
            if field not in SEARCH_FIELDS:
                raise ValueError(f"Unknown search field {field!r}; expected one of {SEARCH_FIELDS}")

        if classification_ids is None and not collection_ids:
            classification_ids = await self._all_classification_ids()

        params: dict[str, Any] = {
            "SearchTerm": search_term,
            "InLanguageCode": normalise_language(in_language, field="in_language"),
            "ReturnType": "Detail" if detail else "Summary",
            "MaxEntryCount": max_results,
        }
        if out_language:
            params["OutLanguageCode"] = normalise_language(out_language, field="out_language")
        # Every flag is sent explicitly. Unsent flags keep their API-side default
        # (Terminus/Name/Abbreviation/Phraseology = true), so omitting them would
        # make `fields` able to widen the search but never to narrow it.
        requested = set(fields)
        for field in SEARCH_FIELDS:
            params[f"Field.{field}"] = "true" if field in requested else "false"
        if collection_ids:
            params["CollectionIds"] = collection_ids
        if classification_ids:
            params["ClassificationIds"] = classification_ids

        http = await self._client()
        resp = await fetch_with_retry(http, f"{BASE_URL}/Search", params)
        return [flatten_entry(item) for item in resp.json()], _now_iso()

    async def entries(
        self, entry_ids: list[int], in_language: str = "DE", out_language: str | None = None
    ) -> tuple[list[dict], str]:
        """Call /v2/Entry for one or more known entry IDs."""
        if not entry_ids:
            raise ValueError("entry_ids must not be empty")
        params: dict[str, Any] = {
            "EntryIds": entry_ids,
            "InLanguageCode": normalise_language(in_language, field="in_language"),
        }
        if out_language:
            params["OutLanguageCode"] = normalise_language(out_language, field="out_language")
        http = await self._client()
        resp = await fetch_with_retry(http, f"{BASE_URL}/Entry", params)
        return [flatten_entry(item) for item in resp.json()], _now_iso()

    async def vocabulary(self, kind: str, language: str = "DE") -> tuple[list[dict], str, str]:
        """Cached /v2/Collection or /v2/Classification. Returns (values, provenance, retrieved_at)."""
        if kind not in ("Collection", "Classification"):
            raise ValueError("kind must be 'Collection' or 'Classification'")
        lang = normalise_language(language, field="language")
        key = (kind, lang)

        stamp = self._vocab_at.get(key)
        if stamp is not None and time.monotonic() - stamp < self._vocab_ttl:
            return self._vocab[key], "cached", self._vocab_iso[key]

        async with self._lock:
            stamp = self._vocab_at.get(key)
            if stamp is not None and time.monotonic() - stamp < self._vocab_ttl:
                return self._vocab[key], "cached", self._vocab_iso[key]

            http = await self._client()
            try:
                resp = await fetch_with_retry(http, f"{BASE_URL}/{kind}", {"languageCode": lang})
                values = resp.json()
            except (UpstreamUnavailable, httpx.HTTPError):
                if key in self._vocab:
                    return self._vocab[key], "cached", self._vocab_iso[key]
                raise

            self._vocab[key] = values
            self._vocab_at[key] = time.monotonic()
            self._vocab_iso[key] = _now_iso()
            return values, "live_api", self._vocab_iso[key]
