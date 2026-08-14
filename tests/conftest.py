"""Gemeinsame Fixtures der Testsuite.

Der Client wiederholt fehlgeschlagene Requests viermal mit 2s/4s/8s-Backoff
(``client.fetch_with_retry``). In den gemockten Tests ist diese Wartezeit reine
Wanduhr: Der respx-Mock antwortet ohnehin sofort, und die Schlafphase prüft
nichts. Fünf Tests über zwei Module schöpften die Leiter voll aus und trugen
damit 58 der 60 Sekunden Laufzeit der Offline-Suite.

Live-Tests sind ausgenommen, und zwar nicht aus Vorsicht, sondern aus
Höflichkeit: Sie sprechen mit der echten TERMDAT-API. Ein Backoff, der dort
ausgepatcht wird, verwandelt einen Retry in vier Requests ohne Pause — genau
die Last, die der Backoff von der Quelle fernhalten soll. Die Ausnahme ist in
``tests/test_live.py`` festgehalten, damit sie nicht still verfällt.
"""

from __future__ import annotations

import pytest

from termdat_mcp import client as client_module


@pytest.fixture(autouse=True)
def _no_sleep(request, monkeypatch):
    """Backoff in gemockten Tests überspringen, in Live-Tests nicht anfassen."""
    if "live" in request.keywords:
        return

    async def _instant(_seconds):
        return None

    # ``client_module.asyncio`` *ist* das stdlib-Modul, der Patch wirkt also
    # prozessweit — monkeypatch nimmt ihn nach jedem Test zurück.
    monkeypatch.setattr(client_module, "_sleep", _instant)
