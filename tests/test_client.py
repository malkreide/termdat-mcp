from __future__ import annotations

import httpx
import pytest
import respx

from termdat_mcp.client import (
    BASE_URL,
    TermdatClient,
    UpstreamUnavailable,
    flatten_entry,
    normalise_language,
)

SEARCH_URL = f"{BASE_URL}/Search"
COLLECTION_URL = f"{BASE_URL}/Collection"

RAW_ENTRY = {
    "id": 3053,
    "url": "https://www.termdat.bk.admin.ch/search/entry/3053",
    "status": {"code": "1", "text": "Validiert"},
    "reliability": {"code": "2", "text": "Sprachlich/formal überprüft"},
    "office": {"id": 1, "code": "ACH", "text": "Schweizerische Bundesverwaltung"},
    "collection": {"id": 101, "code": "ADFB23", "text": "Bezeichnungen der Organisationseinheiten"},
    "classification": {"id": 16, "code": "VARI", "text": "VARIA"},
    "subject": [{"id": 20, "text": "BILDUNG"}],
    "languageDetails": [
        {"id": 1, "languageIsoCode": "DE", "sequence": 1, "name": "Bundeskanzlei", "note": None},
        {
            "id": 2,
            "languageIsoCode": "FR",
            "sequence": 1,
            "name": "Chancellerie fédérale",
            "note": None,
        },
        {
            "id": 3,
            "languageIsoCode": "FR",
            "sequence": 2,
            "name": "Chancellerie fédérale suisse",
            "note": None,
        },
    ],
}


def test_normalise_language_accepts_case_insensitive_iso2():
    assert normalise_language("de") == "DE"
    assert normalise_language("FR") == "FR"


@pytest.mark.parametrize("bad", ["de-CH", "deu", "", "xx"])
def test_normalise_language_rejects_locale_and_iso3(bad):
    with pytest.raises(ValueError):
        normalise_language(bad)


def test_flatten_entry_extracts_nested_text_fields():
    entry = flatten_entry(RAW_ENTRY)
    assert entry["entry_id"] == 3053
    assert entry["status"] == "Validiert"
    assert entry["collection"].startswith("Bezeichnungen")
    assert entry["subjects"] == ["BILDUNG"]
    assert len(entry["variants"]) == 3
    assert entry["variants"][1]["language"] == "FR"


@respx.mock
async def test_search_happy_path_sends_expected_params():
    route = respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, json=[RAW_ENTRY]))
    client = TermdatClient(http=httpx.AsyncClient())
    entries, _ = await client.search("Bundeskanzlei", "de", out_language="fr", detail=True)

    assert len(entries) == 1
    params = route.calls[0].request.url.params
    assert params["InLanguageCode"] == "DE"
    assert params["OutLanguageCode"] == "FR"
    assert params["ReturnType"] == "Detail"
    assert params["Field.Terminus"] == "true"
    await client.aclose()


@respx.mock
async def test_search_retries_after_503():
    respx.get(SEARCH_URL).mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json=[RAW_ENTRY])]
    )
    client = TermdatClient(http=httpx.AsyncClient())
    entries, _ = await client.search("Bundeskanzlei")
    assert len(entries) == 1
    await client.aclose()


@respx.mock
async def test_search_400_fails_fast_without_retry():
    route = respx.get(SEARCH_URL).mock(return_value=httpx.Response(400, json={"title": "invalid"}))
    client = TermdatClient(http=httpx.AsyncClient())
    with pytest.raises(httpx.HTTPStatusError):
        await client.search("x")
    assert route.call_count == 1
    await client.aclose()


@respx.mock
async def test_network_error_raises_clean_exception():
    respx.get(SEARCH_URL).mock(side_effect=httpx.ConnectError("boom"))
    client = TermdatClient(http=httpx.AsyncClient())
    with pytest.raises(UpstreamUnavailable):
        await client.search("Bundeskanzlei")
    await client.aclose()


@respx.mock
async def test_vocabulary_is_cached():
    route = respx.get(COLLECTION_URL).mock(
        return_value=httpx.Response(200, json=[{"id": 90, "code": "ABR24", "text": "Abkürzungen"}])
    )
    client = TermdatClient(http=httpx.AsyncClient())
    _, first, _ = await client.vocabulary("Collection", "de")
    _, second, _ = await client.vocabulary("Collection", "de")
    assert (first, second) == ("live_api", "cached")
    assert route.call_count == 1
    await client.aclose()


async def test_invalid_field_rejected():
    client = TermdatClient(http=httpx.AsyncClient())
    with pytest.raises(ValueError):
        await client.search("x", fields=("Nonsense",))
    with pytest.raises(ValueError):
        await client.search("   ")
    await client.aclose()
