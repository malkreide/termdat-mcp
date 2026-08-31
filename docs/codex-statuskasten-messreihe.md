# Codex-Statuskasten: laufende Messreihe

Der Abschnitt «Fünfte Form» in [`CLAUDE.md`](../CLAUDE.md) beschreibt den vom
Codex-Bot gepflegten Statuskasten («Codex Review Summary»). Er nennt dort zwei
Zahlen — wann der Kasten erscheint und wann der Lauf beginnt — und die beruhen
auf den ersten beiden Läufen. Diese Datei hält die Rohwerte fest, damit die
Zahlen im Abschnitt später auf einer breiteren Grundlage korrigiert werden
können statt aus der Erinnerung.

Warum getrennt: Eine Spanne aus zwei Punkten ist keine Messreihe, und sie im
Abschnitt bei jedem neuen Lauf nachzuziehen hiesse, denselben Absatz im
Wochentakt anzufassen. Der Abschnitt bleibt deshalb vorerst stehen, wie er
ist; korrigiert wird er in einem Zug, wenn die Reihe trägt.

Alle Zeiten UTC, Repo `malkreide/termdat-mcp`, Auslöser jeweils «Draft marked
ready».

| PR | «ready» | Merge | Kasten angelegt (Δ) | Laufbeginn laut Kasten (Δ) | Abschluss (Δ) | Befund |
|---|---|---|---|---|---|---|
| [#64](https://github.com/malkreide/termdat-mcp/pull/64) | 30.8. 18:12:47 | 18:12:49 | 18:12:58 (11 s) | 18:12:54 (7 s) | 18:14:55 (2:08) | keiner |
| [#65](https://github.com/malkreide/termdat-mcp/pull/65) | 30.8. 18:42:45 | 18:42:49 | 18:42:55 (10 s) | 18:42:51 (6 s) | 18:43:51 (1:06) | keiner |
| [#66](https://github.com/malkreide/termdat-mcp/pull/66) | 31.8. 03:48:01 | 03:48:05 | 03:48:16 (15 s) | nicht erfasst | 03:49:49 (1:48) | keiner |

«Befund: keiner» heisst hier dreimal dasselbe: `get_reviews` leer, keine
Befundlos-Meldung, `reactions.total_count` 0 am PR wie am Kommentar — belegt
ist also je ein **Lauf**, kein Urteil. Der Abschnitt in `CLAUDE.md` sagt,
warum das ein Unterschied ist.

Stand der Zahlen (n=3): Kasten-Anlage **10–15 s** nach «ready», Laufbeginn
**6–7 s** (n=2). Der Abschnitt nennt bislang 10–11 s und 6–7 s; die
Obergrenze der ersten Zahl ist mit #66 überholt, bleibt aber bis zur
Korrektur in einem Zug stehen.

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
