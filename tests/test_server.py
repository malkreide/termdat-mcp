"""Tool-level tests: exercise each MCP tool against a mocked upstream."""

from __future__ import annotations

import httpx
import pytest
import respx

from termdat_mcp import server
from termdat_mcp.client import BASE_URL, TermdatClient

SEARCH_URL = f"{BASE_URL}/Search"
ENTRY_URL = f"{BASE_URL}/Entry"
COLLECTION_URL = f"{BASE_URL}/Collection"
CLASSIFICATION_URL = f"{BASE_URL}/Classification"

ENTRY = {
    "id": 3053,
    "url": "https://www.termdat.bk.admin.ch/search/entry/3053",
    "status": {"code": "1", "text": "Validiert"},
    "collection": {"id": 101, "text": "Organisationseinheiten"},
    "languageDetails": [
        {"languageIsoCode": "DE", "sequence": 1, "name": "Bundeskanzlei"},
        {"languageIsoCode": "FR", "sequence": 1, "name": "Chancellerie fédérale"},
    ],
}


@pytest.fixture
def mocked_client(monkeypatch):
    client = TermdatClient(http=httpx.AsyncClient())
    monkeypatch.setattr(server, "_client", client)
    yield client


@respx.mock
async def test_search_terms_returns_envelope(mocked_client):
    respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, json=[ENTRY]))
    res = await server.search_terms("Bundeskanzlei", out_language="FR")
    assert res.provenance == "live_api"
    assert res.returned == 1
    assert res.entries[0].entry_id == 3053
    await mocked_client.aclose()


@respx.mock
async def test_get_entries_by_id(mocked_client):
    respx.get(ENTRY_URL).mock(return_value=httpx.Response(200, json=[ENTRY]))
    res = await server.get_entries([3053])
    assert res.returned == 1
    await mocked_client.aclose()


@respx.mock
async def test_translate_term_extracts_target_language(mocked_client):
    respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, json=[ENTRY]))
    res = await server.translate_term("Bundeskanzlei", to_language="FR")
    assert res.to_language == "FR"
    assert res.hits and res.hits[0].preferred == "Chancellerie fédérale"
    await mocked_client.aclose()


@respx.mock
async def test_check_terms_runs_concurrently_and_flags_validated(mocked_client):
    respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, json=[ENTRY]))
    res = await server.check_terms(["Bundeskanzlei", "Bundeskanzlei"])
    assert res.checked == 2
    assert res.validated == 2
    await mocked_client.aclose()


@respx.mock
async def test_check_terms_not_found_is_not_incorrect(mocked_client):
    respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, json=[]))
    res = await server.check_terms(["Volksschule"])
    assert res.results[0].verdict == "not_found"
    assert res.not_found == 1
    await mocked_client.aclose()


async def test_check_terms_rejects_empty_after_strip(mocked_client):
    with pytest.raises(ValueError):
        await server.check_terms(["   "])
    await mocked_client.aclose()


@respx.mock
async def test_list_collections_and_classifications(mocked_client):
    respx.get(COLLECTION_URL).mock(
        return_value=httpx.Response(200, json=[{"id": 1, "code": "ABR", "text": "Abkürzungen"}])
    )
    respx.get(CLASSIFICATION_URL).mock(
        return_value=httpx.Response(200, json=[{"id": 16, "code": "BILD", "text": "Bildung"}])
    )
    cols = await server.list_collections()
    cls = await server.list_classifications()
    assert cols.count == 1 and cols.kind == "collection"
    assert cls.values[0].code == "BILD"
    await mocked_client.aclose()


@respx.mock
async def test_api_status_reachable(mocked_client):
    respx.get(COLLECTION_URL).mock(return_value=httpx.Response(200, json=[{"id": 1, "code": "A", "text": "x"}]))
    respx.get(CLASSIFICATION_URL).mock(
        return_value=httpx.Response(200, json=[{"id": 16, "code": "BILD", "text": "Bildung"}])
    )
    res = await server.api_status()
    assert res.reachable is True
    await mocked_client.aclose()


@respx.mock
async def test_api_status_masks_error_when_unreachable(mocked_client):
    respx.get(COLLECTION_URL).mock(side_effect=httpx.ConnectError("boom"))
    res = await server.api_status()
    assert res.reachable is False
    # OBS-002: the raw upstream error text must not leak into the tool result.
    assert "boom" not in res.message
    await mocked_client.aclose()


async def test_upstream_error_is_masked_for_search(mocked_client):
    with respx.mock:
        respx.get(SEARCH_URL).mock(side_effect=httpx.ConnectError("internal detail"))
        with pytest.raises(Exception) as exc:  # noqa: PT011
            await server.search_terms("Bundeskanzlei")
        assert "internal detail" not in str(exc.value)
    await mocked_client.aclose()
