"""Inbound Host/Origin validation on the SSE transport (SEC-005, inbound half).

The SDK leaves DNS-rebinding protection off while ``transport_security`` is
unset. This server never set it, so there was no Host check at all. These tests
pin the new behaviour and fail if the protection is dropped again.
"""

from __future__ import annotations

import pytest

from termdat_mcp.__main__ import build_transport_security
from termdat_mcp.settings import Settings


def _cfg(host="127.0.0.1", port=8000, allowed_hosts=None, cors_allow_origins=None):
    # The Settings fields carry a `validation_alias`, so they can only be
    # populated under that alias — Settings(host=...) is silently ignored and
    # falls back to the default, which quietly makes every assertion here test
    # the loopback case.
    return Settings(
        HOST=host,
        PORT=port,
        TERMDAT_MCP_ALLOWED_HOSTS=allowed_hosts if allowed_hosts is not None else [],
        TERMDAT_MCP_CORS_ORIGINS=cors_allow_origins if cors_allow_origins is not None else [],
    )


def test_loopback_bind_enables_protection():
    sec = build_transport_security(_cfg())
    assert sec is not None
    assert sec.enable_dns_rebinding_protection is True
    assert "127.0.0.1:8000" in sec.allowed_hosts
    assert "localhost:8000" in sec.allowed_hosts


def test_non_local_bind_without_allowlist_stays_off():
    """0.0.0.0 with no allow-list: the reachable name is unknowable here, so a
    guess would reject every real request. Protection stays off; caller warns."""
    assert build_transport_security(_cfg(host="0.0.0.0")) is None


def test_non_local_bind_with_allowlist_enables_protection():
    sec = build_transport_security(_cfg(host="0.0.0.0", allowed_hosts=["mcp.example.ch"]))
    assert sec is not None
    assert "mcp.example.ch" in sec.allowed_hosts
    # Loopback stays in, otherwise container health checks break.
    assert "127.0.0.1:8000" in sec.allowed_hosts


def test_port_is_taken_from_settings():
    """The allow-list must follow the configured port, not a hard-coded 8000."""
    sec = build_transport_security(_cfg(port=9443))
    assert "127.0.0.1:9443" in sec.allowed_hosts
    assert "127.0.0.1:8000" not in sec.allowed_hosts


def test_configured_cors_origin_passes_transport_check():
    sec = build_transport_security(_cfg(cors_allow_origins=["https://claude.ai"]))
    assert "https://claude.ai" in sec.allowed_origins


def test_wildcard_cors_is_not_copied():
    """ "*" is matched literally by the SDK, so copying it would look like a
    wildcard while doing nothing."""
    sec = build_transport_security(_cfg(cors_allow_origins=["*"]))
    assert "*" not in sec.allowed_origins


def test_default_deny_cors_still_allows_loopback_origins():
    """CORS is default-deny here, so allowed_origins is just the derived set —
    it must not come out empty, or a same-host browser request would fail."""
    sec = build_transport_security(_cfg(cors_allow_origins=[]))
    assert "http://127.0.0.1:8000" in sec.allowed_origins


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
def test_all_loopback_forms_are_local(host):
    assert build_transport_security(_cfg(host=host)) is not None
