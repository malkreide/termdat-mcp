# Codex-Statuskasten: laufende Messreihe

Der Abschnitt «Fünfte Form» in [`CLAUDE.md`](../CLAUDE.md) beschreibt den vom
Codex-Bot gepflegten Statuskasten («Codex Review Summary»). Er nennt dort zwei
Zahlen — wann der Kasten erscheint und wann der Lauf beginnt. Diese Datei hält
die Rohwerte fest, aus denen sie stammen, damit sie sich nachrechnen und
später fortschreiben lassen statt aus der Erinnerung.

Warum getrennt: Die Zahlen im Abschnitt beruhten anfangs auf zwei Läufen, und
eine Spanne aus zwei Punkten ist keine Messreihe. Nachgezogen wird sie
deshalb nicht bei jedem Lauf, sondern in einem Zug — zuletzt bei n=4, als der
dritte Lauf die alte Obergrenze überholt hatte. Die Rohwerte wachsen hier
weiter, auch wenn der Abschnitt eine Weile stehen bleibt.

Alle Zeiten UTC, Repo `malkreide/termdat-mcp`, Auslöser jeweils «Draft marked
ready».

| PR | «ready» | Merge | Kasten angelegt (Δ) | Laufbeginn laut Kasten (Δ) | Abschluss (Δ) | Befund |
|---|---|---|---|---|---|---|
| [#64](https://github.com/malkreide/termdat-mcp/pull/64) | 30.8. 18:12:47 | 18:12:49 | 18:12:58 (11 s) | 18:12:54 (7 s) | 18:14:55 (2:08) | keiner |
| [#65](https://github.com/malkreide/termdat-mcp/pull/65) | 30.8. 18:42:45 | 18:42:49 | 18:42:55 (10 s) | 18:42:51 (6 s) | 18:43:51 (1:06) | keiner |
| [#66](https://github.com/malkreide/termdat-mcp/pull/66) | 31.8. 03:48:01 | 03:48:05 | 03:48:16 (15 s) | nicht erfasst | 03:49:49 (1:48) | keiner |
| [#67](https://github.com/malkreide/termdat-mcp/pull/67) | 31.8. 04:07:04 | 04:07:08 | 04:07:16 (12 s) | 04:07:12 (8 s) | 04:08:35 (1:31) | keiner |

«Befund: keiner» heisst hier viermal dasselbe: `get_reviews` leer, keine
Befundlos-Meldung, `reactions.total_count` 0 am PR wie am Kommentar — belegt
ist also je ein **Lauf**, kein Urteil. Der Abschnitt in `CLAUDE.md` sagt,
warum das ein Unterschied ist.

Stand der Zahlen (n=4): Kasten-Anlage **10–15 s** nach «ready», Laufbeginn
**6–8 s** (n=3, bei #66 nicht erfasst), Abschluss **1:06 bis 2:08** nach
«ready». Der Abschnitt in `CLAUDE.md` nennt dieselben Spannen und verweist
hierher; wer eine davon ändert, ändert beide Stellen.

`updated_at` ist kein Abschluss-Signal. Bei #67 sprang es um 04:07:21 hoch,
während der Text noch `🔄 Running` sagte — der Bot editiert den Kommentar auch
zwischendurch. Nur der Text sagt, ob der Lauf fertig ist; dieselbe Falle wie
beim Kommentarzähler, eine Ebene tiefer.

## Wie erfasst wird

`get_comments` **zweimal** lesen: einmal unmittelbar nach «ready», einmal rund
zwei Minuten später. Der Kasten ist derselbe, in place editierte Kommentar —
die Zeile `🔄 Running since …` wird beim Abschluss durch `✅ Completed …`
**ersetzt**. Wer nur einmal spät liest, verliert den Laufbeginn; genau so fehlt
er bei #66.

## Was die Reihe nicht hergibt

In allen drei Fällen fiel der Merge, **bevor** der Lauf begann (2 bis 4
Sekunden nach «ready», der Lauf begann nach 6 bis 7). Belegt ist damit: Ein
Merge verhindert den Start nicht, und der Lauf endet auf dem gemergten Head.
Ob ein Merge einen **bereits laufenden** Review überlebt, ist ungemessen —
dafür bräuchte es einen Merge grob zwischen 10 Sekunden und 2 Minuten nach
«ready».
