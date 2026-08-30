"""What the server tells the model about coverage and terms of use.

These are string assertions, which are only worth writing because the strings are
the product here: the model never sees the Federal Chancellery's answer, only the
`source` field and the caveats. Two of them previously said the opposite of the
truth — that the terms of use were unknown, and that an empty result meant a term
was absent from TERMDAT. Nothing was red, because nothing checked the wording.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from termdat_mcp import server
from termdat_mcp.client import BASE_URL, TermdatClient
from termdat_mcp.models import ATTRIBUTION, CheckResult

SEARCH_URL = f"{BASE_URL}/Search"


@pytest.fixture
def mocked_client(monkeypatch):
    client = TermdatClient(http=httpx.AsyncClient())
    monkeypatch.setattr(server, "_client", client)
    yield client


def test_attribution_names_the_source_the_chancellery_requires():
    """Naming `www.termdat.ch` is the condition itself, not decoration."""
    assert "www.termdat.ch" in ATTRIBUTION


def test_attribution_states_the_prior_notification_duty():
    lowered = ATTRIBUTION.lower()
    assert "informed" in lowered
    assert "beforehand" in lowered
    assert "terminologie@bk.admin.ch" in lowered


def test_attribution_no_longer_claims_the_terms_are_unknown():
    """The I14Y record has no licence field; the terms exist all the same.

    Telling the model to «clarify the terms» made a stated condition look open, and
    a downstream user cannot meet a condition nobody names.
    """
    lowered = ATTRIBUTION.lower()
    assert "no explicit licence statement" not in lowered
    assert "clarify terms" not in lowered


@respx.mock
async def test_response_envelope_carries_the_terms(mocked_client):
    """The constant is only useful if it reaches an actual answer."""
    respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, json=[]))
    res = await server.search_terms("Bundeskanzlei")
    assert "www.termdat.ch" in res.source
    await mocked_client.aclose()


def _flat(text: str) -> str:
    """One line, single spaces — so a line break cannot hide a missing phrase."""
    return " ".join(text.split())


def test_check_terms_caveat_scopes_absence_to_the_api():
    caveat = _flat(CheckResult.model_fields["caveat"].default)
    assert "'not_found' means 'not in the public API'" in caveat
    assert "never 'not in TERMDAT'" in caveat


def test_empty_hint_scopes_absence_to_the_api():
    hint = _flat(server._EMPTY_HINT)
    assert "absent from the public API" in hint
    assert "absent from TERMDAT" not in hint


def test_coverage_caveat_reports_the_confirmed_answer():
    """Deliberate subset, translators' needs, no fuller coverage planned.

    Before the Chancellery answered, this docstring guessed at a validation-status
    filter. A guess in a tool description reads to the model exactly like a fact.
    """
    doc = _flat(server.search_terms.__doc__ or "")
    assert "deliberate" in doc
    assert "translators" in doc
    assert "no fuller coverage is planned" in doc
