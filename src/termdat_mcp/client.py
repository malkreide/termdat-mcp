"""TERMDAT public API client (api.termdat.bk.admin.ch, OpenAPI 3.0.4, no auth).

Architecture A (live API only). Only the two small controlled vocabularies
(140 collections, 23 classifications) are cached, because they change rarely
and are needed to make filter arguments legible to an agent.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

import httpx

BASE_URL = "https://api.termdat.bk.admin.ch/v2"
SPEC_URL = "https://api.termdat.bk.admin.ch/swagger/v2/swagger.json"
VOCAB_TTL_SECONDS = 24 * 60 * 60

VALID_LANGUAGES = ("DE", "FR", "IT", "EN", "RM", "LA")

# The 12 searchable fields exposed by the API as Field.* boolean flags.
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
    http: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None, *, max_attempts: int = 4
) -> httpx.Response:
    """GET with exponential backoff: 2s, 4s, 8s. 4xx except 429 fails fast."""
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        if attempt > 0:
            await asyncio.sleep(2**attempt)
        try:
            resp = await http.get(url, params=params)
            resp.raise_for_status()
            return resp
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            last_error = exc
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status is not None and 400 <= status < 500 and status != 429:
                raise
    raise UpstreamUnavailable(f"TERMDAT unreachable after {max_attempts} attempts: {last_error}")


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
                timeout=httpx.Timeout(60.0), headers={"User-Agent": "termdat-mcp/0.1.0"}
            )
        return self._http

    async def aclose(self) -> None:
        if self._http is not None and self._own_http:
            await self._http.aclose()
            self._http = None

    async def search(
        self,
        search_term: str,
        in_language: str = "DE",
        *,
        out_language: str | None = None,
        detail: bool = False,
        fields: tuple[str, ...] = ("Terminus",),
        collection_ids: list[int] | None = None,
        classification_ids: list[int] | None = None,
        max_results: int = 25,
    ) -> tuple[list[dict], str]:
        """Call /v2/Search. Returns (flattened entries, retrieved_at)."""
        if not search_term.strip():
            raise ValueError("search_term must not be empty")

        params: dict[str, Any] = {
            "SearchTerm": search_term,
            "InLanguageCode": normalise_language(in_language, field="in_language"),
            "ReturnType": "Detail" if detail else "Summary",
            "MaxEntryCount": max_results,
        }
        if out_language:
            params["OutLanguageCode"] = normalise_language(out_language, field="out_language")
        for field in fields:
            if field not in SEARCH_FIELDS:
                raise ValueError(f"Unknown search field {field!r}; expected one of {SEARCH_FIELDS}")
            params[f"Field.{field}"] = "true"
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
