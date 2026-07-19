"""Live tests against the real TERMDAT API. Excluded from CI via -m "not live"."""

from __future__ import annotations

import pytest

from termdat_mcp.client import TermdatClient

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


async def test_umlaut_is_encoded_correctly():
    client = TermdatClient()
    entries, _ = await client.search("Sonderpädagogik", "DE", detail=True)
    assert entries, "expected hits for Sonderpädagogik"
    await client.aclose()
