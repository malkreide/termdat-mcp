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
CLASSIFICATION_URL = f"{BASE_URL}/Classification"

CLASSIFICATIONS = [
    {"id": 3, "code": "FINA", "text": "FINANZWESEN"},
    {"id": 16, "code": "VARI", "text": "VARIA"},
]

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
    respx.get(CLASSIFICATION_URL).mock(return_value=httpx.Response(200, json=CLASSIFICATIONS))
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


# --- Search scope (issue #11) ---


@respx.mock
async def test_search_spans_all_classifications_by_default():
    """An ID-less /v2/Search is restricted to VARIA upstream — send the full set."""
    respx.get(CLASSIFICATION_URL).mock(return_value=httpx.Response(200, json=CLASSIFICATIONS))
    route = respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, json=[RAW_ENTRY]))
    client = TermdatClient(http=httpx.AsyncClient())
    await client.search("Quellensteuer")

    ids = route.calls[0].request.url.params.get_list("ClassificationIds")
    assert sorted(ids) == ["16", "3"], "every classification must be searched by default"
    await client.aclose()


@respx.mock
async def test_explicit_classification_ids_are_not_overridden():
    respx.get(CLASSIFICATION_URL).mock(return_value=httpx.Response(200, json=CLASSIFICATIONS))
    route = respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, json=[RAW_ENTRY]))
    client = TermdatClient(http=httpx.AsyncClient())
    await client.search("Quellensteuer", classification_ids=[3])

    assert route.calls[0].request.url.params.get_list("ClassificationIds") == ["3"]
    await client.aclose()


@respx.mock
async def test_search_survives_unreachable_classification_vocabulary():
    """Widening is best-effort: if the vocabulary fails, the search still runs."""
    respx.get(CLASSIFICATION_URL).mock(side_effect=httpx.ConnectError("boom"))
    route = respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, json=[RAW_ENTRY]))
    client = TermdatClient(http=httpx.AsyncClient())
    entries, _ = await client.search("Bundeskanzlei")

    assert len(entries) == 1
    assert "ClassificationIds" not in route.calls[0].request.url.params
    await client.aclose()


@respx.mock
async def test_unrequested_fields_are_sent_as_false():
    """Unsent Field.* flags keep their API-side default, so `fields` could only widen."""
    respx.get(CLASSIFICATION_URL).mock(return_value=httpx.Response(200, json=CLASSIFICATIONS))
    route = respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, json=[RAW_ENTRY]))
    client = TermdatClient(http=httpx.AsyncClient())
    await client.search("Bundeskanzlei", fields=("Terminus",))

    params = route.calls[0].request.url.params
    assert params["Field.Terminus"] == "true"
    assert params["Field.Name"] == "false", "Name defaults to true upstream — must be disabled"
    assert params["Field.Definition"] == "false"
    await client.aclose()


@respx.mock
async def test_default_fields_include_free_text_fields():
    respx.get(CLASSIFICATION_URL).mock(return_value=httpx.Response(200, json=CLASSIFICATIONS))
    route = respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, json=[RAW_ENTRY]))
    client = TermdatClient(http=httpx.AsyncClient())
    await client.search("Pensionskasse")

    params = route.calls[0].request.url.params
    for field in ("Terminus", "Name", "Abbreviation", "Phraseology", "Definition", "Note", "Source"):
        assert params[f"Field.{field}"] == "true"
    assert params["Field.Country"] == "false"
    await client.aclose()


@respx.mock
async def test_search_retries_after_503():
    respx.get(SEARCH_URL).mock(side_effect=[httpx.Response(503), httpx.Response(200, json=[RAW_ENTRY])])
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
async def test_unreachable_message_survives_an_empty_exception_string():
    """OBS-007: the message must still say something when ``str(exc)`` is empty.

    ``httpx.ConnectTimeout``, ``ReadTimeout`` and ``ConnectError`` all carry an
    empty ``str()`` — and those are the errors an outage actually produces. The
    exception type and the host have to survive that, and the cause has to stay
    chained so the original traceback is not lost.
    """
    respx.get(SEARCH_URL).mock(side_effect=httpx.ConnectTimeout(""))
    client = TermdatClient(http=httpx.AsyncClient())
    with pytest.raises(UpstreamUnavailable) as exc_info:
        await client.search("Bundeskanzlei")
    msg = str(exc_info.value)
    assert "ConnectTimeout" in msg
    assert "api.termdat.bk.admin.ch" in msg
    assert not msg.rstrip().endswith(":")
    assert isinstance(exc_info.value.__cause__, httpx.ConnectTimeout)
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


# --- Egress allow-list (SEC-021) ---


def test_assert_host_allowed_accepts_termdat():
    from termdat_mcp.client import assert_host_allowed

    assert_host_allowed(f"{BASE_URL}/Search")  # no raise


@pytest.mark.parametrize(
    "bad_url",
    [
        "http://api.termdat.bk.admin.ch/v2/Search",  # non-https
        "https://evil.example.com/v2/Search",  # host not allow-listed
        "https://169.254.169.254/latest/meta-data",  # cloud metadata
    ],
)
def test_assert_host_allowed_rejects(bad_url):
    from termdat_mcp.client import EgressNotAllowed, assert_host_allowed

    with pytest.raises(EgressNotAllowed):
        assert_host_allowed(bad_url)


async def test_fetch_with_retry_enforces_allow_list():
    from termdat_mcp.client import EgressNotAllowed, fetch_with_retry

    async with httpx.AsyncClient() as http:
        with pytest.raises(EgressNotAllowed):
            await fetch_with_retry(http, "https://evil.example.com/x")


# --- Input constraints exposed in the tool schema (SEC-018) ---


def test_search_terms_schema_bounds_max_results():
    from termdat_mcp import server

    tool = server.mcp._tool_manager.get_tool("search_terms")
    schema = tool.parameters
    mr = schema["properties"]["max_results"]
    assert mr.get("maximum") == 100 and mr.get("minimum") == 1
    st = schema["properties"]["search_term"]
    assert st.get("maxLength") == 200 and st.get("minLength") == 1
