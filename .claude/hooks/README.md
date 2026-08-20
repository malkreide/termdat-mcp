# SessionStart-Hook: Klon-Aktualität

`session-start-stale-clone.sh` meldet beim Sessionstart, wie viele Commits der
ausgecheckte Stand hinter `origin/<default-branch>` liegt. Registriert ist er in
[`../settings.json`](../settings.json).

## Grund

Ein veralteter Klon hat am 3.8.2026 zweimal eine rote CI erzeugt, deren Ursache
nicht im Diff stand — die fehlenden Commits waren jeweils genau die, die das
Gate einführten, an dem der Branch scheiterte. Wer den Fehler im eigenen Diff
sucht, sucht in den falschen Dateien. Die Prüfung kostet eine Sekunde und
ersetzt diese Fehlersuche.

## Zusicherungen, in der Reihenfolge ihrer Wichtigkeit

1. **Der Hook blockiert die Session niemals.** Kein Netz, kein `origin`,
   detached HEAD, flatterndes DNS, fehlende Credentials, gar kein Git-Repo:
   jeder dieser Fälle endet still mit `exit 0` und ohne Ausgabe. Ein Hook, der
   bei Netzproblemen die Arbeit anhält, wird nach dem zweiten Mal abgeschaltet
   und schützt danach gar nichts. Deshalb steht im Skript ausdrücklich kein
   `set -e`: jeder Fehlschlag wird einzeln behandelt.
2. **Kurzes Timeout auf jede Netzoperation** (Standard 5 s, siehe
   `CLAUDE_STALE_CLONE_TIMEOUT`), damit der Sessionstart nicht hängt.
   Zusätzlich sind interaktive Git-Prompts abgeschaltet
   (`GIT_TERMINAL_PROMPT=0`, `ssh -o BatchMode=yes`) — ein wartender
   Passphrase-Dialog wäre genau das Hängen, das der Hook vermeiden soll.
3. **Ausgabe nur, wenn tatsächlich Commits fehlen.** Bei 0 schweigt er.
4. **Der Default-Branch wird ermittelt, nicht als `main` angenommen.** Drei
   Server im Portfolio heissen ihren Default-Branch `master`; genau diese
   Annahme hat schon einmal einen Branch 15 Commits alt werden lassen. Quelle
   ist `git ls-remote --symref origin HEAD`. Lässt sich der Default-Branch nicht
   ermitteln, schweigt der Hook — es gibt keinen Fallback auf `main`, lieber
   nichts melden als das Falsche.

## Kosten

Ein Netz-Roundtrip (`ls-remote --symref`) liefert Name *und* SHA des
Default-Branch. Ist dieser Commit schon lokal vorhanden, entfällt der `fetch`
ganz; nur bei tatsächlichem Rückstand kommt ein zweiter Roundtrip dazu.

## Konfiguration

| Variable | Default | Zweck |
| --- | --- | --- |
| `CLAUDE_STALE_CLONE_TIMEOUT` | `5` | Sekunden pro Netzoperation. |
| `CLAUDE_STALE_CLONE_TIMEOUT_BIN` | `$(command -v timeout)` | Pfad zu `timeout`. Auf macOS ohne coreutils z. B. `gtimeout`; leer gesetzt greift die reine Bash-Notlösung im Skript. |

## Manuell ausführen

```bash
CLAUDE_PROJECT_DIR="$(git rev-parse --show-toplevel)" \
  .claude/hooks/session-start-stale-clone.sh
```

Keine Ausgabe heisst: aktuell — oder nicht feststellbar. Beides ist gewollt.

## Tests

`tests/test_session_start_hook.py` fährt das Skript gegen echte Wegwerf-Repos
mit `file://`-Remotes (kein Netz) und deckt die vier Zusicherungen oben ab,
inklusive `master` als Default-Branch und eines künstlich hängenden `git`, an
dem das Timeout nachgewiesen wird. Läuft in der normalen CI mit
(`pytest tests/ -m "not live"`).
