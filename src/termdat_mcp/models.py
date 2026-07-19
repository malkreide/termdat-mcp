"""Pydantic v2 models for the TERMDAT MCP server."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ATTRIBUTION = (
    "Data: TERMDAT, terminology database of the Swiss Federal Administration, "
    "Swiss Federal Chancellery (BK), via api.termdat.bk.admin.ch. "
    "The I14Y catalogue record carries no explicit licence statement — "
    "clarify terms with the Federal Chancellery before republishing."
)

Provenance = Literal["live_api", "cached"]
LANGS = ("DE", "FR", "IT", "EN", "RM", "LA")


class Envelope(BaseModel):
    source: str = Field(default=ATTRIBUTION)
    provenance: Provenance
    retrieved_at: str = Field(description="ISO-8601 UTC timestamp")


class TermVariant(BaseModel):
    """One designation in one language, as validated by the Federal Chancellery."""

    language: str
    name: str
    sequence: int | None = Field(
        default=None, description="1 = preferred designation; higher = accepted variant"
    )
    definition: str | None = None
    note: str | None = Field(
        default=None,
        description="TERMDAT note codes: REG = regional usage, USG = usage, EXP = explanation",
    )
    source: str | None = None


class TermEntry(BaseModel):
    entry_id: int
    url: str = Field(description="Human-readable TERMDAT page")
    status: str = Field(description="e.g. 'Validiert' — only validated entries are authoritative")
    reliability: str = ""
    office: str = ""
    collection: str = Field(description="Terminology collection this entry belongs to")
    classification: str = ""
    subjects: list[str] = Field(default_factory=list)
    variants: list[TermVariant] = Field(default_factory=list)

    @property
    def is_validated(self) -> bool:
        return self.status.casefold().startswith("valid")


class SearchResult(Envelope):
    search_term: str
    in_language: str
    out_language: str | None = None
    returned: int
    truncated: bool = Field(
        description="True if the result hit max_results — narrow the query or raise the limit"
    )
    entries: list[TermEntry]


class TranslationHit(BaseModel):
    source_term: str
    target_language: str
    preferred: str | None = Field(default=None, description="sequence == 1 designation, if any")
    alternatives: list[str] = Field(default_factory=list)
    entry_id: int
    collection: str
    status: str
    url: str


class TranslationResult(Envelope):
    term: str
    from_language: str
    to_language: str
    total_entries: int
    hits: list[TranslationHit]


class TermCheck(BaseModel):
    term: str
    verdict: Literal["validated", "found_unvalidated", "not_found"]
    matched_designation: str | None = None
    entry_id: int | None = None
    url: str | None = None
    note: str = ""


class CheckResult(Envelope):
    language: str
    checked: int
    validated: int
    not_found: int
    results: list[TermCheck]
    caveat: str = Field(
        default=(
            "TERMDAT covers federal and cantonal administrative nomenclature — authority names, "
            "official titles of legal acts, abbreviations. Domain vocabulary (e.g. pedagogy) is "
            "largely absent, so 'not_found' means 'not in TERMDAT', not 'incorrect'."
        )
    )


class Vocabulary(BaseModel):
    id: int
    code: str
    text: str


class VocabularyResult(Envelope):
    kind: Literal["collection", "classification"]
    language: str
    count: int
    values: list[Vocabulary]


class StatusResult(Envelope):
    reachable: bool
    collections: int = 0
    classifications: int = 0
    message: str
