"""Typed configuration via pydantic-settings (ARCH-004).

All runtime configuration flows through this Settings object rather than ad-hoc
`os.environ` reads scattered across the code. Environment-variable names are kept
backward compatible (`TERMDAT_MCP_TRANSPORT`, `HOST`, `PORT`).
"""

from __future__ import annotations

import json
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Die beiden Listen-Variablen nehmen Kommaform **und** JSON. `NoDecode` schaltet
# dabei die Dekodierung der Quelle ab, und ohne es waere der Validator unten
# wirkungslos: `EnvSettingsSource` parst komplexe Felder als JSON, *bevor*
# irgendein Validator laeuft, und wirft dort einen `SettingsError`. Der
# Rohstring erreicht einen `mode="before"`-Validator also gar nicht erst.
#
# Gemessen am 20.09.2026: `NoDecode` gibt es ab pydantic-settings 2.7.0; 2.6.1,
# die hoechste 2.6.x, kennt es nicht. Daher die Untergrenze in pyproject.toml.
_CsvList = Annotated[list[str], NoDecode]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    transport: str = Field(default="stdio", validation_alias="TERMDAT_MCP_TRANSPORT")
    host: str = Field(default="127.0.0.1", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    log_level: str = Field(default="INFO", validation_alias="TERMDAT_MCP_LOG_LEVEL")
    vocab_ttl_seconds: int = Field(default=24 * 60 * 60, validation_alias="TERMDAT_MCP_VOCAB_TTL")

    # HTTP CORS: default-deny. Comma-separated is the recommended spelling
    # (`https://a.example,https://b.example`); a JSON list stays valid.
    # Empty means no browser origin is allowed (server-to-server / local only).
    cors_allow_origins: _CsvList = Field(default_factory=list, validation_alias="TERMDAT_MCP_CORS_ORIGINS")

    # Inbound Host allow-list for the HTTP transport (SEC-005, inbound half).
    # e.g. TERMDAT_MCP_ALLOWED_HOSTS="mcp.example.ch,mcp.example.ch:443".
    # Only needed for a non-loopback bind: the reachable name is then a service
    # or public DNS name this process cannot derive from the bind address.
    allowed_hosts: _CsvList = Field(default_factory=list, validation_alias="TERMDAT_MCP_ALLOWED_HOSTS")

    @field_validator("cors_allow_origins", "allowed_hosts", mode="before")
    @classmethod
    def _accept_comma_separated(cls, value: Any) -> Any:
        """Kommagetrennte Liste lesen, JSON weiterhin annehmen.

        Bis zum 20.09.2026 verlangten beide Variablen JSON — und zwar strenger,
        als der Kommentar hier behauptete: Der sagte «a JSON list or a single
        origin», aber ein nacktes `mcp.example.ch` ist kein gueltiges JSON und
        starb am selben Parser wie die Kommaform. Ein Einzelwert ging also nie.
        Alle uebrigen Server des Portfolios lesen dieselbe Variable
        kommagetrennt (`lindas-mcp` etwa per `os.getenv(...).split(",")`), was
        die Abweichung zu einer Stolperfalle beim Deployment machte.

        Nicht-Strings (Listen aus `Settings(...)`-kwargs, der Default) gehen
        unveraendert durch; dort gibt es nichts zu zerlegen.

        Leerraum und leere Eintraege fallen in **beiden** Formen weg. Das ist
        eine Entscheidung, keine Nebenwirkung: `"a.ch,"` und `'["a.ch", ""]'`
        meinen dasselbe, und sie duerfen nicht verschieden ausgehen. Die
        Alternative haette einen Nebeneffekt: `build_transport_security()`
        prueft `if cfg.allowed_hosts:`, und eine Liste `[""]` ist wahr — der
        Server haette dann DNS-Rebinding-Schutz mit einer Allow-Liste aus
        Loopback und Leerstring aktiviert und jede echte Anfrage mit 421
        beantwortet, was wie ein Netzfehler aussieht. Verworfen ergibt `[""]`
        eine leere Liste, und der bestehende Zweig warnt laut und benennbar.
        """
        if not isinstance(value, str):
            return value
        text = value.strip()
        if text.startswith("["):
            # Eindeutig als JSON gemeint. Ein Fehlschlag hier wird benannt und
            # nicht stillschweigend als einelementige Liste weitergereicht —
            # `["mcp.example.ch"` waere sonst ein Host namens `["mcp.example.ch"`.
            try:
                decoded = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Wert beginnt mit '[' und ist damit als JSON-Liste gelesen worden, "
                    f"ist aber keine gueltige: {exc}. Erlaubt sind eine kommagetrennte "
                    f"Liste (empfohlen) oder eine JSON-Liste."
                ) from exc
            if isinstance(decoded, list):
                return [str(item).strip() for item in decoded if str(item).strip()]
            return decoded
        return [part.strip() for part in text.split(",") if part.strip()]

    @property
    def is_network_transport(self) -> bool:
        """Alle drei Werte bedienen Streamable HTTP unter `/mcp`.

        `sse` ist seit dem 18.09.2026 nur noch ein Alias und warnt beim Start:
        der SSE-Transport des SDK kennt die Weiche in die Protokoll-Aera
        `2026-07-28` nicht, ueber das Netz war sie damit unerreichbar. Den Wert
        hier abzulehnen waere sauberer und zugleich der Bruch, der jedes
        bestehende Deployment beim naechsten Start anhaelt — ein Alias mit
        Warnung sagt dasselbe, ohne den Dienst zu stoppen.
        """
        return self.transport.lower() in ("sse", "streamable-http", "http")


def load_settings() -> Settings:
    return Settings()
