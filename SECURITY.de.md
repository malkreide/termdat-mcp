# Sicherheitsrichtlinie & Posture

[🇬🇧 English Version](SECURITY.md)

`termdat-mcp` ist ein **Read-only-**, **No-Auth-**, **Public-Open-Data-**MCP-Server.
Dieses Dokument fasst die Sicherheits-Posture zusammen und beschreibt, wie
Schwachstellen gemeldet werden.

## Schwachstelle melden

Bitte ein privates Security Advisory im GitHub-Repository eröffnen oder die in
`README.md` genannte Maintainerin kontaktieren. Für ausnutzbare Schwachstellen
keine öffentlichen Issues erstellen.

## Posture-Zusammenfassung

Alle sieben Tools stellen ausschliesslich Lese-Anfragen an die öffentliche
TERMDAT-v2-API (`api.termdat.bk.admin.ch`); es gibt keine Schreib-, Sende- oder
Dateisystem-Fähigkeiten, und es werden keine Personendaten verarbeitet.

| Bereich | Kontrolle |
|---|---|
| Egress | Fixe HTTPS-Basis-URL nur zu `api.termdat.bk.admin.ch`; keine nutzergesteuerten URLs, daher keine SSRF-Angriffsfläche |
| TLS | httpx-Zertifikatsprüfung standardmässig aktiv und im Code nie deaktiviert |
| Auth / Secrets | Unauthentifizierte öffentliche API — es werden keine API-Keys, Tokens oder Secrets gespeichert oder weitergereicht |
| Input | Pydantic-v2-Validierung an allen Tool-Grenzen; Query-Parameter werden URL-kodiert |
| Tools | Alle mit `readOnlyHint: true`, `destructiveHint: false` annotiert; keine dynamische oder Remote-Tool-Registrierung |
| Fehler | Upstream-RFC-9110-Fehlerbodies werden als strukturierte Daten offengelegt, nie stillschweigend verschluckt |
| Stdout | Reserviert für den JSON-RPC-Stream; der Server gibt kein Fremd-Logging auf stdout aus |
| Binding | `stdio` als Default (keine Netzwerk-Angriffsfläche). SSE bindet an `HOST` (Default `0.0.0.0` für Cloud); für rein lokalen Betrieb `HOST=127.0.0.1` setzen |

## Akzeptierte Risiken (Kontrollen auf Portfolio-Ebene)

Die folgenden Punkte werden auf der MCP-Gateway-/Host-Ebene behandelt, nicht in
diesem einzelnen Server. Das Restrisiko ist hier gering, weil der Server
read-only und unauthentifiziert ist und nur einen vertrauenswürdigen
Open-Data-Anbieter erreicht.

- **Session-Krypto-Bindung** — nicht anwendbar: Es gibt keine Nutzeridentität zum
  Binden, da der Server öffentliche Daten ohne Authentifizierung bereitstellt.
- **Server-übergreifende Tool-Poisoning-Erkennung** — Aufgabe des Gateways/Hosts.
  Die Tool-Definitionen dieses Servers sind versioniert, in-repo verfasst und per
  PR reviewt; es gibt keine dynamische oder Remote-Tool-Registrierung.
- **Netzwerk-Binding für gehostete Deployments** — der SSE-Transport bindet für
  Cloud-Hosting standardmässig an `0.0.0.0`. Mit einem Reverse-Proxy / Gateway
  betreiben, das TLS und Zugriffskontrolle erzwingt, oder für lokalen Betrieb
  `HOST=127.0.0.1` setzen.

## Re-Evaluations-Trigger

Diese Akzeptanzen sind neu zu bewerten, sobald der Server je:

- **Schreib**-Fähigkeit erhält oder **PII** verarbeitet, oder
- ein **Authentifizierungs**-Modell erhält (dann gebundene, TTL-behaftete,
  serverseitig invalidierbare Session-IDs implementieren und vor dem Merge
  re-auditieren), oder
- Tools **dynamisch** / aus Remote-Quellen registriert, oder
- hinter einem gemeinsamen MCP-Gateway aggregiert wird (dann Tool-Allow-Listing
  und Tool-Poisoning-Erkennung des Gateways aktivieren).
