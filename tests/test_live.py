"""Live tests against the real TERMDAT API. Excluded from CI via -m "not live"."""

from __future__ import annotations

import asyncio

import pytest

from termdat_mcp import client as client_module
from termdat_mcp.client import TermdatClient

# Beim Import festgehalten — hier hat noch keine Fixture gepatcht.
_UNPATCHED_SLEEP = asyncio.sleep

pytestmark = pytest.mark.live


async def test_vocabularies_reachable():
    client = TermdatClient()
    collections, _, _ = await client.vocabulary("Collection", "DE")
    classifications, _, _ = await client.vocabulary("Classification", "DE")
    assert len(collections) > 100
    assert any(c["code"] == "BILD" for c in classifications)
    await client.aclose()


async def test_out_language_is_additive_not_filtering():
    """Regression guard for the probe finding of 2026-07-19."""
    client = TermdatClient()
    without, _ = await client.search("Departement", "DE", max_results=1000)
    with_fr, _ = await client.search(
        "Departement", "DE", out_language="FR", detail=True, max_results=1000
    )
    assert len(without) == len(with_fr), "OutLanguageCode must not change the result count"
    assert any(v["language"] == "FR" for e in with_fr for v in e["variants"]), (
        "OutLanguageCode adds target-language variants — but only with ReturnType=Detail"
    )
    await client.aclose()


async def test_search_is_not_confined_to_varia():
    """Regression guard for issue #11.

    An ID-less /v2/Search only covers the VARIA classification, which reduced
    «Pensionskasse» to the single PUBLICA entry and «Quellensteuer» to nothing.
    """
    client = TermdatClient()
    entries, _ = await client.search("Pensionskasse", "DE", detail=True, max_results=100)
    assert len(entries) > 1, "search must span all classifications, not just VARIA"
    assert any(e["classification"] != "VARIA" for e in entries)

    hits, _ = await client.search("Quellensteuer", "DE", detail=True, max_results=100)
    assert hits, "«Quellensteuer» is present in TERMDAT and must be found"
    await client.aclose()


async def test_lucene_wildcard_finds_compounds():
    """«Quellensteuer» does not match «Quellensteuerverordnung» — «Quellensteuer*» does."""
    client = TermdatClient()
    exact, _ = await client.search("Quellensteuer", "DE", max_results=100)
    prefix, _ = await client.search("Quellensteuer*", "DE", max_results=100)
    assert len(prefix) > len(exact)
    await client.aclose()


async def test_fields_can_narrow_the_search():
    """Unsent Field.* flags default to true upstream; narrowing must actually narrow."""
    client = TermdatClient()
    broad, _ = await client.search("Steuer", "DE", max_results=1000)
    narrow, _ = await client.search("Steuer", "DE", fields=("Abbreviation",), max_results=1000)
    assert len(narrow) < len(broad)
    await client.aclose()


async def test_umlaut_is_encoded_correctly():
    client = TermdatClient()
    entries, _ = await client.search("Sonderpädagogik", "DE", detail=True)
    assert entries, "expected hits for Sonderpädagogik"
    await client.aclose()


def test_backoff_is_not_patched_out_here():
    """Die ``_no_sleep``-Fixture darf Live-Tests nicht anfassen (conftest.py).

    Sie überspringt in gemockten Tests den 2s/4s/8s-Backoff — hier wäre das
    Unhöflichkeit: Ein Retry gegen die echte TERMDAT-API würde zu vier
    Requests ohne Pause. Der Test braucht kein Netz und läuft genau dann,
    wenn die Ausnahme zählt: im Live-Lauf.
    """
    assert client_module.asyncio.sleep is _UNPATCHED_SLEEP
