"""MCP server for TERMDAT, the terminology database of the Swiss Federal Administration.

Anchor demo query:
    "What are the official French and Italian names of the education directorates
     of the German-speaking cantons?"
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import SEARCH_FIELDS, TermdatClient, normalise_language
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

mcp = FastMCP("termdat-mcp")
_client = TermdatClient()

_READ_ONLY: dict[str, Any] = {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True}


def _fields(fields: str) -> tuple[str, ...]:
    parsed = tuple(f.strip() for f in fields.split(",") if f.strip())
    return parsed or ("Terminus",)


@mcp.tool(annotations=_READ_ONLY)
async def search_terms(
    search_term: str,
    in_language: str = "DE",
    out_language: str = "",
    detail: bool = True,
    fields: str = "Terminus",
    collection_ids: list[int] | None = None,
    classification_ids: list[int] | None = None,
    max_results: int = 25,
) -> SearchResult:
    """Search TERMDAT for official designations of the Swiss Federal Administration.

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
    entry_ids: list[int], in_language: str = "DE", out_language: str = ""
) -> SearchResult:
    """Fetch known TERMDAT entries by their numeric IDs, with full language variants."""
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
    term: str, from_language: str = "DE", to_language: str = "FR", max_results: int = 10
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


@mcp.tool(annotations=_READ_ONLY)
async def check_terms(terms: list[str], language: str = "DE") -> CheckResult:
    """Check a list of terms against validated TERMDAT designations.

    Intended for communication QA: verify that authority names, department titles and
    abbreviations in a draft match the officially validated form. Each term is reported
    as `validated`, `found_unvalidated` or `not_found`.
    """
    if not terms:
        raise ValueError("terms must not be empty")
    if len(terms) > 25:
        raise ValueError("check at most 25 terms per call to stay within upstream rate limits")

    lang = normalise_language(language, field="language")
    results: list[TermCheck] = []
    retrieved_at = ""

    for term in terms:
        cleaned = term.strip()
        if not cleaned:
            continue
        entries, retrieved_at = await _client.search(
            cleaned, lang, detail=True, fields=("Terminus",), max_results=10
        )

        exact = None
        for entry in entries:
            for variant in entry["variants"]:
                if variant["language"] == lang and variant["name"].casefold() == cleaned.casefold():
                    exact = (entry, variant)
                    break
            if exact:
                break

        if exact is None:
            results.append(
                TermCheck(
                    term=cleaned,
                    verdict="not_found",
                    note=(
                        f"{len(entries)} related entr{'y' if len(entries) == 1 else 'ies'} found, "
                        "but no exact designation match."
                    ),
                )
            )
            continue

        entry, variant = exact
        validated = entry["status"].casefold().startswith("valid")
        results.append(
            TermCheck(
                term=cleaned,
                verdict="validated" if validated else "found_unvalidated",
                matched_designation=variant["name"],
                entry_id=entry["entry_id"],
                url=entry["url"],
                note=(variant.get("note") or entry["status"]),
            )
        )

    return CheckResult(
        provenance="live_api",
        retrieved_at=retrieved_at or "unavailable",
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
        # (OBS-002: mask upstream/internal error details).
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
