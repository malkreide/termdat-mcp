"""Tests fuer den SessionStart-Hook `.claude/hooks/session-start-stale-clone.sh`.

Alle Faelle laufen gegen echte Wegwerf-Repos mit `file://`-Remotes — kein Netz,
kein Mock der Git-Mechanik. Handgeschriebene Fixtures koennten die Annahme des
Autors nur bestaetigen; ein echtes `git ls-remote` gegen ein echtes Bare-Repo
widerlegt sie.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / ".claude" / "hooks" / "session-start-stale-clone.sh"

GIT_BIN = shutil.which("git")

pytestmark = pytest.mark.skipif(GIT_BIN is None, reason="git nicht im PATH")


def _git(*args: str, cwd: Path) -> str:
    env = dict(os.environ)
    env.update(
        {
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
            "GIT_CONFIG_NOSYSTEM": "1",
        }
    )
    out = subprocess.run([GIT_BIN, *args], cwd=cwd, env=env, capture_output=True, text=True, check=True)
    return out.stdout.strip()


def _commit(repo: Path, message: str) -> None:
    (repo / "datei.txt").write_text(message, encoding="utf-8")
    _git("add", "datei.txt", cwd=repo)
    _git("commit", "-m", message, cwd=repo)


def _make_upstream(tmp_path: Path, default_branch: str) -> Path:
    """Bare-Repo mit `default_branch` als HEAD und einem Startcommit."""
    work = tmp_path / "upstream-work"
    work.mkdir()
    _git("init", f"--initial-branch={default_branch}", ".", cwd=work)
    _commit(work, "start")

    bare = tmp_path / "upstream.git"
    _git("clone", "--bare", str(work), str(bare), cwd=tmp_path)
    _git("symbolic-ref", "HEAD", f"refs/heads/{default_branch}", cwd=bare)
    return bare


def _push_upstream(tmp_path: Path, bare: Path, branch: str, count: int) -> None:
    """Legt `count` neue Commits auf `branch` im Bare-Repo ab."""
    work = tmp_path / f"pusher-{branch}"
    if not work.exists():
        _git("clone", str(bare), str(work), cwd=tmp_path)
    _git("checkout", "-B", branch, f"origin/{branch}", cwd=work)
    for i in range(count):
        _commit(work, f"{branch}-neu-{i}")
    _git("push", "origin", branch, cwd=work)


def _clone(tmp_path: Path, bare: Path, name: str = "klon") -> Path:
    target = tmp_path / name
    _git("clone", str(bare), str(target), cwd=tmp_path)
    return target


def _run_hook(
    project_dir: Path,
    *,
    timeout_secs: str = "5",
    path_prefix: Path | None = None,
    timeout_bin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    env["CLAUDE_STALE_CLONE_TIMEOUT"] = timeout_secs
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    if path_prefix is not None:
        env["PATH"] = f"{path_prefix}{os.pathsep}{env.get('PATH', '')}"
    if timeout_bin is not None:
        env["CLAUDE_STALE_CLONE_TIMEOUT_BIN"] = timeout_bin
    return subprocess.run(
        [str(HOOK)],
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(REPO_ROOT),
        check=False,
    )


def _stub_git_that_hangs_on(tmp_path: Path, subcommand: str, *, mode: str) -> Path:
    """Ein `git` im PATH, das bei `subcommand` haengt bzw. scheitert.

    `mode="hang"` schlaeft 30 s (die Zeitgrenze muss zuschlagen), `mode="fail"`
    bricht sofort ab. Alle anderen Aufrufe gehen an das echte git.
    """
    stub_dir = tmp_path / f"stub-{subcommand}-{mode}"
    stub_dir.mkdir()
    action = "sleep 30; exit 0" if mode == "hang" else "exit 9"
    (stub_dir / "git").write_text(
        "#!/bin/sh\n"
        'for a in "$@"; do\n'
        f'  if [ "$a" = "{subcommand}" ]; then {action}; fi\n'
        "done\n"
        f'exec {GIT_BIN} "$@"\n',
        encoding="utf-8",
    )
    (stub_dir / "git").chmod(0o755)
    return stub_dir


def test_hook_ist_ausfuehrbar() -> None:
    assert HOOK.is_file(), f"{HOOK} fehlt"
    assert os.access(HOOK, os.X_OK), f"{HOOK} ist nicht ausfuehrbar"


def test_meldet_rueckstand_mit_zahl_und_branchname(tmp_path: Path) -> None:
    bare = _make_upstream(tmp_path, "main")
    klon = _clone(tmp_path, bare)
    _push_upstream(tmp_path, bare, "main", 3)

    res = _run_hook(klon)

    assert res.returncode == 0
    assert "3 Commits" in res.stdout
    assert "origin/main" in res.stdout


def test_singular_bei_genau_einem_commit(tmp_path: Path) -> None:
    bare = _make_upstream(tmp_path, "main")
    klon = _clone(tmp_path, bare)
    _push_upstream(tmp_path, bare, "main", 1)

    res = _run_hook(klon)

    assert res.returncode == 0
    assert "1 Commit hinter" in res.stdout


def test_schweigt_wenn_aktuell(tmp_path: Path) -> None:
    bare = _make_upstream(tmp_path, "main")
    klon = _clone(tmp_path, bare)

    res = _run_hook(klon)

    assert res.returncode == 0
    assert res.stdout == ""


def test_default_branch_master_wird_ermittelt_nicht_geraten(tmp_path: Path) -> None:
    """`master` als Default, `main` existiert daneben und ist aktuell.

    Wer `main` annimmt, schweigt hier — und laesst den Klon 4 Commits alt
    werden. Genau dieser Fall ist der Grund fuer den Hook.
    """
    bare = _make_upstream(tmp_path, "master")
    _push_upstream(tmp_path, bare, "master", 0)
    _git("branch", "main", "master", cwd=bare)
    klon = _clone(tmp_path, bare)
    _push_upstream(tmp_path, bare, "master", 4)

    res = _run_hook(klon)

    assert res.returncode == 0
    assert "4 Commits" in res.stdout
    assert "origin/master" in res.stdout
    assert "origin/main" not in res.stdout


def test_ohne_remote_still(tmp_path: Path) -> None:
    solo = tmp_path / "solo"
    solo.mkdir()
    _git("init", "--initial-branch=main", ".", cwd=solo)
    _commit(solo, "start")

    res = _run_hook(solo)

    assert res.returncode == 0
    assert res.stdout == ""


def test_unerreichbares_remote_still(tmp_path: Path) -> None:
    bare = _make_upstream(tmp_path, "main")
    klon = _clone(tmp_path, bare)
    shutil.rmtree(bare)

    res = _run_hook(klon)

    assert res.returncode == 0
    assert res.stdout == ""


def test_kein_git_repo_still(tmp_path: Path) -> None:
    leer = tmp_path / "kein-repo"
    leer.mkdir()

    res = _run_hook(leer)

    assert res.returncode == 0
    assert res.stdout == ""


def test_repo_ohne_commit_still(tmp_path: Path) -> None:
    frisch = tmp_path / "frisch"
    frisch.mkdir()
    _git("init", "--initial-branch=main", ".", cwd=frisch)

    res = _run_hook(frisch)

    assert res.returncode == 0
    assert res.stdout == ""


def test_nicht_existierendes_projektverzeichnis_still(tmp_path: Path) -> None:
    res = _run_hook(tmp_path / "gibt-es-nicht")

    assert res.returncode == 0
    assert res.stdout == ""


def test_detached_head_meldet_und_blockiert_nicht(tmp_path: Path) -> None:
    bare = _make_upstream(tmp_path, "main")
    klon = _clone(tmp_path, bare)
    start = _git("rev-parse", "HEAD", cwd=klon)
    _push_upstream(tmp_path, bare, "main", 2)
    _git("checkout", "--detach", start, cwd=klon)

    res = _run_hook(klon)

    assert res.returncode == 0
    assert "2 Commits" in res.stdout


@pytest.mark.parametrize("timeout_bin", [None, ""], ids=["mit-timeout-binary", "bash-notloesung"])
def test_haengendes_git_bricht_ab_und_schweigt(tmp_path: Path, timeout_bin: str | None) -> None:
    """Ein `git ls-remote`, das 30 s haengt, darf die Session nicht aufhalten."""
    bare = _make_upstream(tmp_path, "main")
    klon = _clone(tmp_path, bare)
    stub = _stub_git_that_hangs_on(tmp_path, "ls-remote", mode="hang")

    start = time.monotonic()
    res = _run_hook(klon, timeout_secs="2", path_prefix=stub, timeout_bin=timeout_bin)
    elapsed = time.monotonic() - start

    assert res.returncode == 0
    assert res.stdout == ""
    assert elapsed < 15, f"Hook lief {elapsed:.1f}s — die Zeitgrenze hat nicht gegriffen"


def test_haengendes_fetch_bricht_ab_und_schweigt(tmp_path: Path) -> None:
    """Auch der zweite Netzaufruf hat eine Zeitgrenze."""
    bare = _make_upstream(tmp_path, "main")
    klon = _clone(tmp_path, bare)
    _push_upstream(tmp_path, bare, "main", 2)
    stub = _stub_git_that_hangs_on(tmp_path, "fetch", mode="hang")

    start = time.monotonic()
    res = _run_hook(klon, timeout_secs="2", path_prefix=stub)
    elapsed = time.monotonic() - start

    assert res.returncode == 0
    assert res.stdout == ""
    assert elapsed < 15, f"Hook lief {elapsed:.1f}s — die Zeitgrenze hat nicht gegriffen"


def test_kein_fetch_wenn_stand_schon_lokal_liegt(tmp_path: Path) -> None:
    """Liegt der Remote-Commit lokal, entfaellt der zweite Roundtrip.

    Nachweis ueber die Zeit, nicht ueber das Ergebnis: der gestubbte `fetch`
    haengt 30 s, die Zeitgrenze steht auf 5 s. Wer trotzdem fetcht, braucht
    mindestens diese 5 s — die Meldung faellt in beiden Faellen gleich aus und
    taugt deshalb nicht als Unterscheidung.
    """
    bare = _make_upstream(tmp_path, "main")
    klon = _clone(tmp_path, bare)
    _push_upstream(tmp_path, bare, "main", 2)
    _git("fetch", "origin", "main", cwd=klon)
    stub = _stub_git_that_hangs_on(tmp_path, "fetch", mode="hang")

    start = time.monotonic()
    res = _run_hook(klon, timeout_secs="5", path_prefix=stub)
    elapsed = time.monotonic() - start

    assert res.returncode == 0
    assert "2 Commits" in res.stdout
    assert elapsed < 3, f"Hook lief {elapsed:.1f}s — es wurde unnoetig gefetcht"


def test_fehlschlagender_fetch_bleibt_still(tmp_path: Path) -> None:
    """Scheitert der noetige `fetch`, fehlt der Vergleichsstand — also Schweigen."""
    bare = _make_upstream(tmp_path, "main")
    klon = _clone(tmp_path, bare)
    _push_upstream(tmp_path, bare, "main", 2)
    stub = _stub_git_that_hangs_on(tmp_path, "fetch", mode="fail")

    res = _run_hook(klon, path_prefix=stub)

    assert res.returncode == 0
    assert res.stdout == ""
