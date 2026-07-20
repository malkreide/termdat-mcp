"""Typed configuration via pydantic-settings (ARCH-004).

All runtime configuration flows through this Settings object rather than ad-hoc
`os.environ` reads scattered across the code. Environment-variable names are kept
backward compatible (`TERMDAT_MCP_TRANSPORT`, `HOST`, `PORT`).
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    transport: str = Field(default="stdio", validation_alias="TERMDAT_MCP_TRANSPORT")
    host: str = Field(default="127.0.0.1", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    log_level: str = Field(default="INFO", validation_alias="TERMDAT_MCP_LOG_LEVEL")
    vocab_ttl_seconds: int = Field(default=24 * 60 * 60, validation_alias="TERMDAT_MCP_VOCAB_TTL")

    # SSE/HTTP CORS: default-deny. Set a comma-free JSON list or a single origin.
    # Empty means no browser origin is allowed (server-to-server / local only).
    cors_allow_origins: list[str] = Field(
        default_factory=list, validation_alias="TERMDAT_MCP_CORS_ORIGINS"
    )

    @property
    def is_network_transport(self) -> bool:
        return self.transport.lower() in ("sse", "streamable-http", "http")


def load_settings() -> Settings:
    return Settings()
