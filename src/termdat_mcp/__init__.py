"""MCP server for TERMDAT — terminology database of the Swiss Federal Administration."""

# Version, Zusammenfassung und Projekt-URL löst `_version` auf, gespeist aus
# den Metadaten der installierten Distribution. Die Auflösung stand bis hierher
# in dieser Datei; sie ist nach `_version` gezogen, weil `server.py` inzwischen
# dieselben Angaben braucht (`serverInfo`) und zwei Auflösungsstellen für eine
# Angabe genau der Anfang der Drift sind, gegen die sie existiert.
from ._version import __version__

__all__ = ["__version__"]
