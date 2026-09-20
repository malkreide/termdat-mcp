"""Die beiden Listen-Variablen nehmen Kommaform und JSON.

Befund vom 20.09.2026 aus dem Railway-Deployment: `TERMDAT_MCP_ALLOWED_HOSTS`
und `TERMDAT_MCP_CORS_ORIGINS` erzwangen JSON, waehrend alle uebrigen Server
des Portfolios dieselbe Variable kommagetrennt lesen (`lindas-mcp` etwa per
`os.getenv(...).split(",")`). Wer die Portfolio-Schreibweise verwendete, bekam
einen `SettingsError` beim Start.

Der Kommentar im Code behauptete dabei mehr, als der Code hielt: «a JSON list
or a single origin». Ein nacktes `mcp.example.ch` ist kein gueltiges JSON und
starb am selben Parser — der Einzelwert ging nie. Genau dieser Fall steht
unten deshalb als eigener Test.

Gemessen wird ueber die Umgebung, nicht ueber kwargs: Die Zerlegung sitzt in
`EnvSettingsSource`, und ein `Settings(TERMDAT_MCP_ALLOWED_HOSTS=[...])` geht
an ihr vorbei. Ein Test, der nur kwargs fuettert, waere gegen den Befund gruen
gewesen — er prueft die Stelle nicht, an der er entstand.
"""

from __future__ import annotations

import pytest

from termdat_mcp.settings import Settings

# (Variable, Feldname) — beide Variablen tragen dieselbe Mechanik, und beide
# einzeln zu fahren ist der Unterschied zwischen «eine repariert» und «beide».
VARIABLEN = [
    ("TERMDAT_MCP_ALLOWED_HOSTS", "allowed_hosts"),
    ("TERMDAT_MCP_CORS_ORIGINS", "cors_allow_origins"),
]


@pytest.fixture(autouse=True)
def _leere_umgebung(monkeypatch: pytest.MonkeyPatch) -> None:
    """Beide Variablen abraeumen, damit ein gesetzter Wert der Umgebung keinen
    Test still verfaelscht."""
    for name, _ in VARIABLEN:
        monkeypatch.delenv(name, raising=False)


def lade(monkeypatch: pytest.MonkeyPatch, name: str, wert: str) -> Settings:
    monkeypatch.setenv(name, wert)
    return Settings()


@pytest.mark.parametrize(("name", "feld"), VARIABLEN)
def test_kommaform_wird_zerlegt(monkeypatch: pytest.MonkeyPatch, name: str, feld: str) -> None:
    """Der eigentliche Befund: Diese Schreibweise warf vorher `SettingsError`."""
    settings = lade(monkeypatch, name, "a.example.ch,b.example.ch")
    assert getattr(settings, feld) == ["a.example.ch", "b.example.ch"]


@pytest.mark.parametrize(("name", "feld"), VARIABLEN)
def test_einzelwert_ohne_klammern(monkeypatch: pytest.MonkeyPatch, name: str, feld: str) -> None:
    """Der Fall, den der alte Kommentar versprach und der Code nie konnte."""
    assert getattr(lade(monkeypatch, name, "a.example.ch"), feld) == ["a.example.ch"]


@pytest.mark.parametrize(("name", "feld"), VARIABLEN)
def test_json_liste_bleibt_gueltig(monkeypatch: pytest.MonkeyPatch, name: str, feld: str) -> None:
    """Die bisherige Schreibweise darf nicht brechen — bestehende Deployments
    fahren sie."""
    settings = lade(monkeypatch, name, '["a.example.ch", "b.example.ch"]')
    assert getattr(settings, feld) == ["a.example.ch", "b.example.ch"]


@pytest.mark.parametrize(("name", "feld"), VARIABLEN)
def test_leerraum_und_leere_eintraege_fallen_weg(
    monkeypatch: pytest.MonkeyPatch, name: str, feld: str
) -> None:
    """Ein nachgestelltes Komma ist ein Tippfehler, kein Host."""
    settings = lade(monkeypatch, name, "  a.example.ch , , b.example.ch ,")
    assert getattr(settings, feld) == ["a.example.ch", "b.example.ch"]


@pytest.mark.parametrize(("name", "feld"), VARIABLEN)
def test_beide_formen_ergeben_dasselbe(monkeypatch: pytest.MonkeyPatch, name: str, feld: str) -> None:
    """Dieselbe Absicht, zwei Schreibweisen, ein Ergebnis — einschliesslich der
    leeren Eintraege.

    Ohne diese Zusicherung koennte die JSON-Seite Leereintraege behalten,
    waehrend die Kommaseite sie verwirft. Das waere kein harmloser Unterschied:
    `build_transport_security()` prueft `if cfg.allowed_hosts:`, und `[""]` ist
    wahr — der Server aktivierte dann den DNS-Rebinding-Schutz mit einer
    Allow-Liste aus Loopback und Leerstring und beantwortete jede echte Anfrage
    mit 421, was im Betrieb wie ein Netzfehler aussieht.
    """
    komma = getattr(lade(monkeypatch, name, "a.example.ch,,b.example.ch"), feld)
    monkeypatch.delenv(name)
    js = getattr(lade(monkeypatch, name, '["a.example.ch", "", "b.example.ch"]'), feld)
    assert komma == js == ["a.example.ch", "b.example.ch"]


@pytest.mark.parametrize(("name", "feld"), VARIABLEN)
def test_leerstring_ergibt_leere_liste(monkeypatch: pytest.MonkeyPatch, name: str, feld: str) -> None:
    """Default-Deny bleibt Default-Deny. Eine gesetzte, aber leere Variable
    darf nicht als «ein Eintrag» durchgehen."""
    assert getattr(lade(monkeypatch, name, ""), feld) == []


@pytest.mark.parametrize(("name", "feld"), VARIABLEN)
def test_ungesetzt_bleibt_leer(monkeypatch: pytest.MonkeyPatch, name: str, feld: str) -> None:
    """Negativkontrolle zum Default: Ohne die Variable darf nichts entstehen."""
    assert getattr(Settings(), feld) == []


@pytest.mark.parametrize(("name", "feld"), VARIABLEN)
def test_kaputtes_json_wird_benannt(monkeypatch: pytest.MonkeyPatch, name: str, feld: str) -> None:
    """Ein Wert, der mit `[` beginnt, ist als JSON gemeint.

    Ihn bei einem Syntaxfehler still an die Kommaform durchzureichen, ergaebe
    einen Host namens `["mcp.example.ch` — eine Konfiguration, die nie greift
    und nichts meldet. Die Fehlermeldung nennt stattdessen beide erlaubten
    Formen.
    """
    monkeypatch.setenv(name, '["a.example.ch"')
    with pytest.raises(ValueError, match="kommagetrennte"):
        Settings()


def test_listen_kwarg_geht_unveraendert_durch() -> None:
    """`tests/test_transport_security.py` baut `Settings(...)` mit Listen-kwargs.

    Der Validator darf daran nichts aendern — sonst behebt dieser Commit eine
    Variable und bricht die Testhilfe, die die andere Haelfte prueft.
    """
    settings = Settings(
        TERMDAT_MCP_ALLOWED_HOSTS=["mcp.example.ch"],
        TERMDAT_MCP_CORS_ORIGINS=["https://claude.ai"],
    )
    assert settings.allowed_hosts == ["mcp.example.ch"]
    assert settings.cors_allow_origins == ["https://claude.ai"]
