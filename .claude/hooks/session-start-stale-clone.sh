#!/usr/bin/env bash
#
# SessionStart-Hook: meldet, wie viele Commits der ausgecheckte Stand hinter
# origin/<default-branch> liegt. Bei 0 schweigt er.
#
# GRUND: Ein veralteter Klon hat am 3.8.2026 zweimal eine rote CI erzeugt,
# deren Ursache nicht im Diff stand — die fehlenden Commits waren jeweils
# genau die, die das Gate einfuehrten, an dem der Branch scheiterte. Die
# Pruefung kostet eine Sekunde und ersetzt eine Fehlersuche in den falschen
# Dateien.
#
# WICHTIGSTE ZUSICHERUNG: Der Hook blockiert die Session NIEMALS. Kein Netz,
# kein Remote, detached HEAD, flatterndes DNS, kein Git-Repo — jeder dieser
# Faelle geht still durch (exit 0, keine Ausgabe). Ein Hook, der bei
# Netzproblemen die Arbeit anhaelt, wird nach dem zweiten Mal abgeschaltet
# und schuetzt danach gar nichts.
#
# Deshalb ausdruecklich KEIN `set -e` und KEIN `set -o pipefail`: jeder
# Fehlschlag wird einzeln behandelt und endet in `exit 0`. `set -u` ist
# gesetzt, damit ein Tippfehler in einem Variablennamen beim Testen auffaellt;
# alle Expansionen unten haben Defaults.
set -u

# Sekunden pro Netzoperation. Ueberschreibbar, u.a. fuer die Tests.
timeout_secs="${CLAUDE_STALE_CLONE_TIMEOUT:-5}"

# Pfad zu `timeout`. Leer = reine Bash-Notloesung unten (macOS ohne coreutils,
# dort heisst es `gtimeout`). Die Zuweisung nutzt `-` statt `:-`, damit ein
# absichtlich leer gesetzter Wert erhalten bleibt und nicht neu gesucht wird.
timeout_bin="${CLAUDE_STALE_CLONE_TIMEOUT_BIN-$(command -v timeout 2>/dev/null || true)}"

# Keine interaktiven Prompts: ein wartender Credential- oder Passphrase-Dialog
# ist genau das Haengen, das dieser Hook nicht verursachen darf.
export GIT_TERMINAL_PROMPT=0
export GIT_ASKPASS=/bin/true
export SSH_ASKPASS=/bin/true
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh} -o BatchMode=yes -o ConnectTimeout=${timeout_secs}"

# Fuehrt "$@" mit harter Zeitgrenze aus. Rueckgabe 124 bei Zeitueberschreitung
# (wie `timeout`). stdout des Kommandos bleibt durchgereicht, damit der Aufruf
# in einer Kommandosubstitution funktioniert.
run_limited() {
  local secs="$1"
  shift
  if [ -n "$timeout_bin" ]; then
    "$timeout_bin" -k 1 "$secs" "$@"
    return $?
  fi
  # Notloesung ohne `timeout`: Hintergrundprozess, pollen, notfalls toeten.
  #
  # `set -m` ist hier nicht Kosmetik: ohne Job-Control landet der
  # Hintergrundjob in DIESER Prozessgruppe, und ein `kill` auf die PID trifft
  # nur `git` selbst. Ein Enkelprozess (git ruft ssh/git-remote-https auf) haelt
  # dann die stdout-Pipe weiter offen — die Kommandosubstitution am Aufrufpunkt
  # wartet auf genau diese Pipe und haengt die volle Zeit, obwohl die Zeitgrenze
  # laengst zugeschlagen hat. Mit Job-Control bekommt der Job eine eigene
  # Prozessgruppe, und `kill -- -PID` nimmt die Enkel mit. (GNU `timeout` macht
  # im Zweig darueber dasselbe.)
  local had_monitor=0
  case "$-" in
    *m*) had_monitor=1 ;;
  esac
  set -m
  "$@" &
  local pid=$! ticks=0 limit=$((secs * 10))
  [ "$had_monitor" = 1 ] || set +m
  while kill -0 "$pid" 2>/dev/null; do
    if [ "$ticks" -ge "$limit" ]; then
      kill -TERM "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null
      sleep 1
      kill -KILL "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null
      wait "$pid" 2>/dev/null
      return 124
    fi
    sleep 0.1
    ticks=$((ticks + 1))
  done
  wait "$pid"
}

cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0

# Kein Git-Repo, oder ein Repo ohne einen einzigen Commit -> still durch.
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
head_sha="$(git rev-parse --verify --quiet HEAD 2>/dev/null)" || exit 0
[ -n "$head_sha" ] || exit 0

# Kein `origin` -> nichts zu vergleichen.
git remote get-url origin >/dev/null 2>&1 || exit 0

# Default-Branch ERMITTELN, nicht raten. `main` ist hier keine Annahme: drei
# Server im Portfolio heissen ihren Default-Branch `master`, und genau diese
# Annahme hat schon einmal einen Branch 15 Commits alt werden lassen.
# `ls-remote --symref` liefert Name UND SHA in einem Roundtrip.
symref_out="$(run_limited "$timeout_secs" git ls-remote --symref origin HEAD 2>/dev/null)"
default_branch="$(printf '%s\n' "$symref_out" |
  sed -n 's|^ref: refs/heads/\([^[:space:]]*\)[[:space:]]*HEAD$|\1|p' | head -n 1)"
remote_sha="$(printf '%s\n' "$symref_out" |
  sed -n 's|^\([0-9a-f]\{7,\}\)[[:space:]]*HEAD$|\1|p' | head -n 1)"

if [ -z "$default_branch" ] || [ -z "$remote_sha" ]; then
  # Netz weg, DNS flattert, Auth fehlt, Remote antwortet nicht wie erwartet:
  # Es gibt keinen Fallback auf `main` — lieber schweigen als das Falsche
  # melden.
  exit 0
fi

# Liegt der Remote-Stand schon lokal, entfaellt der zweite Roundtrip komplett.
if ! git cat-file -e "${remote_sha}^{commit}" 2>/dev/null; then
  run_limited "$timeout_secs" git fetch --quiet --no-tags origin \
    "+refs/heads/${default_branch}:refs/remotes/origin/${default_branch}" >/dev/null 2>&1
  git cat-file -e "${remote_sha}^{commit}" 2>/dev/null || exit 0
fi

behind="$(git rev-list --count "${head_sha}..${remote_sha}" 2>/dev/null)" || exit 0
case "$behind" in
  '' | *[!0-9]*) exit 0 ;;
  0) exit 0 ;;  # Aktuell — hier schweigt der Hook.
esac

commit_word="Commits"
[ "$behind" = "1" ] && commit_word="Commit"

cat <<MSG
[Klon-Aktualitaet] Der ausgecheckte Stand liegt $behind $commit_word hinter origin/${default_branch}.
  Aktualisieren: git fetch origin ${default_branch} && git merge origin/${default_branch}
  Grund: Ein veralteter Klon erzeugt eine rote CI, deren Ursache nicht im Diff steht — es fehlen
  dann genau die Commits, die das Gate eingefuehrt haben, an dem der Branch scheitert.
MSG

exit 0
