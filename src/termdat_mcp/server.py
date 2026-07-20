"""MCP server for TERMDAT, the terminology database of the Swiss Federal Administration.

Anchor demo query:
    "What are the official French and Italian names of the education directorates
     of the German-speaking cantons?"

This server exposes seven read-only Tools. It uses only the MCP *Tools* primitive:
the data has no stable resource hierarchy worth exposing as *Resources* (every
answer is a live query), and there are no server-authored *Prompts*. See the
"MCP Primitives" note in the README.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from .client import SEARCH_FIELDS, TermdatClient, normalise_language
from .logging_config import configure_logging, log
from .models import (
    CheckResult,
    SearchResult,
    StatusResult,
    TermCheck,
    TermEntry,
    TranslationHit,
    TranslationResult,
    Vocabulary,
    VocabularyResult,
)
from .settings import load_settings

settings = load_settings()

# A single shared client for the process lifetime (never one per tool call).
# The lifespan below owns its shutdown (SDK-001).
_client = TermdatClient(vocab_ttl=settings.vocab_ttl_seconds)


@asynccontextmanager
async def _lifespan(_server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Own the shared client's lifecycle: log startup, close the client on shutdown."""
    configure_logging(settings.log_level)
    log.info("termdat_mcp.startup", transport=settings.transport)
    try:
        yield {}
    finally:
        await _client.aclose()
        log.info("termdat_mcp.shutdown")


mcp = FastMCP("termdat-mcp", lifespan=_lifespan)

_READ_ONLY: dict[str, Any] = {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True}

# Reusable, constrained argument aliases (SEC-018: bounds at the tool boundary).
_Term = Annotated[str, Field(min_length=1, max_length=200)]
_Fields = Annotated[str, Field(max_length=200)]
_MaxResults = Annotated[int, Field(ge=1, le=100)]
_EntryIds = Annotated[list[int], Field(min_length=1, max_length=100)]
_Terms = Annotated[list[str], Field(min_length=1, max_length=25)]


def _fields(fields: str) -> tuple[str, ...]:
    parsed = tuple(f.strip() for f in fields.split(",") if f.strip())
    return parsed or ("Terminus",)


@mcp.tool(annotations=_READ_ONLY)
async def search_terms(
    search_term: _Term,
    in_language: str = "DE",
    out_language: str = "",
    detail: bool = True,
    fields: _Fields = "Terminus",
    collection_ids: list[int] | None = None,
    classification_ids: list[int] | None = None,
    max_results: _MaxResults = 25,
) -> SearchResult:
    """Search TERMDAT for official designations of the Swiss Federal Administration.

    Use this to look up the officially validated German/French/Italian/English name
    of an authority, department or legal act — for example to check how a body is
    named in another national language before citing it.

    `out_language` adds a target language to every entry's variants — it is purely
    additive and never filters the result set. `fields` is a comma-separated subset
    of: Terminus, Name, Abbreviation, Phraseology, Definition, Note, Context, Source,
    Metadata, Country, Comment.

    Scope caveat: TERMDAT holds administrative nomenclature (authority names, titles
    of legal acts, abbreviations), not domain vocabulary. An empty result usually
    means the term is out of scope, not that it is wrong.
    """
    entries, retrieved_at = await _client.search(
        search_term,
        in_language,
        out_language=out_language or None,
        detail=detail,
        fields=_fields(fields),
        collection_ids=collection_ids,
        classification_ids=classification_ids,
        max_results=max_results,
    )
    return SearchResult(
        provenance="live_api",
        retrieved_at=retrieved_at,
        search_term=search_term,
        in_language=normalise_language(in_language),
        out_language=normalise_language(out_language) if out_language else None,
        returned=len(entries),
        truncated=len(entries) >= max_results,
        entries=[TermEntry(**e) for e in entries],
    )


@mcp.tool(annotations=_READ_ONLY)
async def get_entries(
    entry_ids: _EntryIds, in_language: str = "DE", out_language: str = ""
) -> SearchResult:
    """Fetch known TERMDAT entries by their numeric IDs, with full language variants.

    Use this to re-retrieve an entry you already found via `search_terms` (its
    `entry_id`), e.g. to pull all four national-language designations at once.
    """
    entries, retrieved_at = await _client.entries(
        entry_ids, in_language, out_language or None
    )
    return SearchResult(
        provenance="live_api",
        retrieved_at=retrieved_at,
        search_term=",".join(str(i) for i in entry_ids),
        in_language=normalise_language(in_language),
        out_language=normalise_language(out_language) if out_language else None,
        returned=len(entries),
        truncated=False,
        entries=[TermEntry(**e) for e in entries],
    )


@mcp.tool(annotations=_READ_ONLY)
async def translate_term(
    term: _Term, from_language: str = "DE", to_language: str = "FR", max_results: _MaxResults = 10
) -> TranslationResult:
    """Get the official equivalent of an administrative term in another national language.

    Returns the preferred designation (sequence 1) plus accepted variants, per matching
    entry. Use this for authority names, department titles and titles of legal acts.
    """
    entries, retrieved_at = await _client.search(
        term,
        from_language,
        out_language=to_language,
        detail=True,
        fields=("Terminus",),
        max_results=max_results,
    )
    target = normalise_language(to_language, field="to_language")

    hits: list[TranslationHit] = []
    for entry in entries:
        variants = [v for v in entry["variants"] if v["language"] == target and v["name"]]
        if not variants:
            continue
        variants.sort(key=lambda v: (v.get("sequence") or 99))
        preferred = variants[0]["name"] if (variants[0].get("sequence") or 99) == 1 else None
        hits.append(
            TranslationHit(
                source_term=term,
                target_language=target,
                preferred=preferred,
                alternatives=[v["name"] for v in variants if v["name"] != preferred],
                entry_id=entry["entry_id"],
                collection=entry["collection"],
                status=entry["status"],
                url=entry["url"],
            )
        )

    return TranslationResult(
        provenance="live_api",
        retrieved_at=retrieved_at,
        term=term,
        from_language=normalise_language(from_language, field="from_language"),
        to_language=target,
        total_entries=len(entries),
        hits=hits,
    )


async def _check_one(term: str, lang: str) -> tuple[TermCheck, str]:
    """Check a single term against validated designations. Returns (result, retrieved_at)."""
    entries, retrieved_at = await _client.search(
        term, lang, detail=True, fields=("Terminus",), max_results=10
    )
    exact = None
    for entry in entries:
        for variant in entry["variants"]:
            if variant["language"] == lang and variant["name"].casefold() == term.casefold():
                exact = (entry, variant)
                break
        if exact:
            break

    if exact is None:
        return (
            TermCheck(
                term=term,
                verdict="not_found",
                note=(
                    f"{len(entries)} related entr{'y' if len(entries) == 1 else 'ies'} found, "
                    "but no exact designation match."
                ),
            ),
            retrieved_at,
        )

    entry, variant = exact
    validated = entry["status"].casefold().startswith("valid")
    return (
        TermCheck(
            term=term,
            verdict="validated" if validated else "found_unvalidated",
            matched_designation=variant["name"],
            entry_id=entry["entry_id"],
            url=entry["url"],
            note=(variant.get("note") or entry["status"]),
        ),
        retrieved_at,
    )


@mcp.tool(annotations=_READ_ONLY)
async def check_terms(terms: _Terms, language: str = "DE", ctx: Context | None = None) -> CheckResult:
    """Check a list of terms against validated TERMDAT designations.

    Intended for communication QA: verify that authority names, department titles and
    abbreviations in a draft match the officially validated form. Each term is reported
    as `validated`, `found_unvalidated` or `not_found`. Up to 25 terms per call; the
    lookups run concurrently.
    """
    cleaned = [t.strip() for t in terms if t.strip()]
    if not cleaned:
        raise ValueError("terms must contain at least one non-empty value")

    lang = normalise_language(language, field="language")

    async def _run(idx: int, term: str) -> tuple[TermCheck, str]:
        result = await _check_one(term, lang)
        if ctx is not None:
            await ctx.report_progress(progress=idx + 1, total=len(cleaned))
        return result

    pairs = await asyncio.gather(*(_run(i, t) for i, t in enumerate(cleaned)))
    results = [p[0] for p in pairs]
    retrieved_at = next((p[1] for p in reversed(pairs) if p[1]), "unavailable")

    return CheckResult(
        provenance="live_api",
        retrieved_at=retrieved_at,
        language=lang,
        checked=len(results),
        validated=sum(1 for r in results if r.verdict == "validated"),
        not_found=sum(1 for r in results if r.verdict == "not_found"),
        results=results,
    )


@mcp.tool(annotations=_READ_ONLY)
async def list_collections(language: str = "DE") -> VocabularyResult:
    """List the ~140 TERMDAT collections, for use as `collection_ids` filters."""
    values, provenance, retrieved_at = await _client.vocabulary("Collection", language)
    return VocabularyResult(
        provenance=provenance,  # type: ignore[arg-type]
        retrieved_at=retrieved_at,
        kind="collection",
        language=normalise_language(language),
        count=len(values),
        values=[Vocabulary(**v) for v in values],
    )


@mcp.tool(annotations=_READ_ONLY)
async def list_classifications(language: str = "DE") -> VocabularyResult:
    """List the 23 subject classifications (e.g. BILD = education), for `classification_ids`."""
    values, provenance, retrieved_at = await _client.vocabulary("Classification", language)
    return VocabularyResult(
        provenance=provenance,  # type: ignore[arg-type]
        retrieved_at=retrieved_at,
        kind="classification",
        language=normalise_language(language),
        count=len(values),
        values=[Vocabulary(**v) for v in values],
    )


@mcp.tool(annotations=_READ_ONLY)
async def api_status() -> StatusResult:
    """Availability of the TERMDAT API. Never returns silently empty."""
    try:
        collections, provenance, retrieved_at = await _client.vocabulary("Collection")
        classifications, _, _ = await _client.vocabulary("Classification")
    except Exception:  # noqa: BLE001 — status must never raise; report unreachable instead
        # Deliberately do not forward the raw exception text to the model
        # (OBS-002: mask upstream/internal error details). Details go to stderr.
        log.warning("termdat_mcp.status_unreachable")
        return StatusResult(
            provenance="cached",
            retrieved_at="unavailable",
            reachable=False,
            message="TERMDAT is currently unreachable. Retry in ~10 minutes.",
        )

    return StatusResult(
        provenance=provenance,  # type: ignore[arg-type]
        retrieved_at=retrieved_at,
        reachable=True,
        collections=len(collections),
        classifications=len(classifications),
        message=f"TERMDAT reachable. Searchable fields: {', '.join(SEARCH_FIELDS)}.",
    )
