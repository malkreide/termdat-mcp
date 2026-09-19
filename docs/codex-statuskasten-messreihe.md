# Codex-Statuskasten: laufende Messreihe

Der Abschnitt «Fünfte Form» in [`CLAUDE.md`](../CLAUDE.md) beschreibt den vom
Codex-Bot gepflegten Statuskasten («Codex Review Summary»). Er nennt dort zwei
Zahlen — wann der Kasten erscheint und wann der Lauf beginnt. Diese Datei hält
die Rohwerte fest, aus denen sie stammen, damit sie sich nachrechnen und
später fortschreiben lassen statt aus der Erinnerung.

Warum getrennt: Die Zahlen im Abschnitt beruhten anfangs auf zwei Läufen, und
eine Spanne aus zwei Punkten ist keine Messreihe. Nachgezogen wird sie
deshalb nicht bei jedem Lauf, sondern wenn eine Spanne bricht: bei n=4, als der
dritte Lauf die alte Obergrenze überholte; bei n=7, als #71 die Kasten-
Untergrenze unterbot; bei n=8, als #73 die Abschluss-Untergrenze unterbot —
und dieser dritte Bruch in kurzer Folge führte dazu, dass die Abschluss-Spalte
seither grob geführt wird (eigener Abschnitt unten). Die Rohwerte wachsen hier
weiter, auch wenn der Abschnitt eine Weile stehen bleibt.

Alle Zeiten UTC, Repo `malkreide/termdat-mcp`, Auslöser jeweils «Draft marked
ready».

| PR | «ready» | Merge | Kasten angelegt (Δ) | Laufbeginn laut Kasten (Δ) | Abschluss (Δ) | Befund |
|---|---|---|---|---|---|---|
| [#64](https://github.com/malkreide/termdat-mcp/pull/64) | 30.8. 18:12:47 | 18:12:49 | 18:12:58 (11 s) | 18:12:54 (7 s) | 18:14:55 (2:08) | keiner |
| [#65](https://github.com/malkreide/termdat-mcp/pull/65) | 30.8. 18:42:45 | 18:42:49 | 18:42:55 (10 s) | 18:42:51 (6 s) | 18:43:51 (1:06) | keiner |
| [#66](https://github.com/malkreide/termdat-mcp/pull/66) | 31.8. 03:48:01 | 03:48:05 | 03:48:16 (15 s) | nicht erfasst | 03:49:49 (1:48) | keiner |
| [#67](https://github.com/malkreide/termdat-mcp/pull/67) | 31.8. 04:07:04 | 04:07:08 | 04:07:16 (12 s) | 04:07:12 (8 s) | 04:08:35 (1:31) | keiner |
| [#70](https://github.com/malkreide/termdat-mcp/pull/70) | 18.9. 15:39:25 | 15:39:28 | 15:39:36 (11 s) | 15:39:32 (7 s) | 15:40:58 (1:33) | keiner |
| [#71](https://github.com/malkreide/termdat-mcp/pull/71) | 19.9. 14:20:11 | 14:20:13 | 14:20:17 (**6 s**) | nicht erfasst | 14:21:17 (1:06) | keiner |
| [#72](https://github.com/malkreide/termdat-mcp/pull/72) | 19.9. 14:37:44 | 14:37:47 | 14:37:57 (13 s) | nicht erfasst | 14:38:56 (1:12) | keiner |
| [#73](https://github.com/malkreide/termdat-mcp/pull/73) | 19.9. 16:46:57 | 16:47:00 | 16:47:05 (8 s) | 16:47:03 (6 s) | 16:47:59 (**1:02**) | keiner |

«Befund: keiner» heisst hier achtmal dasselbe: `get_reviews` leer, keine
Befundlos-Meldung, `reactions.total_count` 0 am PR wie am Kommentar — belegt
ist also je ein **Lauf**, kein Urteil. Der Abschnitt in `CLAUDE.md` sagt,
warum das ein Unterschied ist.

Stand der Zahlen (n=8): Kasten-Anlage **6–15 s** nach «ready», Laufbeginn
**6–8 s** (n=5; bei #66, #71 und #72 nicht erfasst), Abschluss **rund 1 bis 2
Minuten** nach «ready». Der Abschnitt in `CLAUDE.md` nennt dieselben Spannen
und verweist hierher; wer eine davon ändert, ändert beide Stellen.

Die Untergrenze der Kasten-Anlage fiel mit #71 von 10 s auf 6 s. Eine Spanne,
die einen gemessenen Wert nicht enthält, ist keine Spanne — das ist der Grund
für ein Nachtragen und nicht die reine Zahl der Zeilen.

## Warum der Abschluss grob geführt wird und die anderen zwei nicht

Der Abschluss stand bis zum 19.9.2026 auf die Sekunde da: **1:06 bis 2:08**.
Diese Untergrenze brach mit #73 (1:02), nachdem zwei Läufe zuvor #71 schon die
Kasten-Untergrenze gebrochen hatte. Zwei gebrochene Grenzen in drei Läufen sind
kein Zufall, sondern der Hinweis, dass hier auf eine Genauigkeit gepinnt wurde,
die die Quelle nicht hergibt — der Bezugspunkt «ready» trägt einen Versatz von
einigen Sekunden (siehe unten).

Die Spalte wird deshalb als **rund 1 bis 2 Minuten** geführt. Das ist kein
Verzicht auf Genauigkeit, sondern die Unterscheidung, welche Frage eine Zahl
beantworten soll:

| Grösse | Spanne | Entscheidung, die daran hängt |
|---|---|---|
| Kasten-Anlage | 6–15 s | Mergt man, bevor der Kasten existiert? Braucht Sekunden. |
| Laufbeginn | 6–8 s | Beginnt der Lauf vor oder nach dem Merge? Braucht Sekunden. |
| **Abschluss** | rund 1–2 min | Wie lange bis zum Urteil? **Braucht keine Sekunden.** |

Die Rohwerte in der Tabelle bleiben sekundengenau — sie sind der Nachweis. Grob
geführt wird die daraus abgeleitete Spanne, und zwar nur die eine, an der keine
Entscheidung hängt.

`updated_at` ist kein Abschluss-Signal. Bei #67 sprang es um 04:07:21 hoch,
während der Text noch `🔄 Running` sagte — der Bot editiert den Kommentar auch
zwischendurch. Nur der Text sagt, ob der Lauf fertig ist; dieselbe Falle wie
beim Kommentarzähler, eine Ebene tiefer.

## Wie erfasst wird

`get_comments` **zweimal** lesen: einmal unmittelbar nach «ready», einmal rund
zwei Minuten später. Der Kasten ist derselbe, in place editierte Kommentar —
die Zeile `🔄 Running since …` wird beim Abschluss durch `✅ Completed …`
**ersetzt**. Wer nur einmal spät liest, verliert den Laufbeginn.

**Drei von acht Zeilen haben ihn deshalb nicht** — #66, #71 und #72. Bei #70
und #73 lag die erste Lesung im richtigen Fenster, bei #71 und #72 kam sie erst
nach dem Abschluss, und damit ist der Laufbeginn nicht später nachzuholen: Die
alte Zeile ist überschrieben, nicht ergänzt. Diese Spalte wächst also nur, wenn
jemand **während** des Laufs liest; der Rest der Zeile lässt sich immer
nachtragen.

Bei #73 hat es geklappt, weil die Lesung 20 Sekunden nach der Merge-Meldung
kam statt nach der üblichen Wartezeit. Das ist der ganze Handgriff: einmal
sofort lesen, einmal zwei Minuten später.

## Woher die Zeiten stammen — sie sind nicht gleich belastbar

Drei der fünf Zeitspalten kommen aus Primärquellen, eine nicht:

| Spalte | Quelle |
|---|---|
| Kasten angelegt | `created_at` des Kommentars (GitHub-API) |
| Laufbeginn · Abschluss | Wortlaut im Kommentartext (`Running since …` / `Completed …`) |
| Merge | Committer-Zeit des Merge-Commits (`git log -1 --format=%cI`) |
| **«ready»** | **Benachrichtigung der Session — keine Primärquelle** |

Der Zeitpunkt, an dem ein Draft auf «ready» geht, ist über die hier
verfügbaren Werkzeuge nicht primär abzufragen; er stammt aus dem Zeitstempel
der eingehenden Benachrichtigung. Wie weit die nachläuft, ist am Merge
gemessen: Für #70, #71 und #72 lag die Merge-Benachrichtigung **1 bis 3
Sekunden** hinter der Committer-Zeit desselben Merges.

Damit trägt jedes Δ in der Tabelle eine Unschärfe von einigen Sekunden — und
zwar genau dort, wo die Zahlen selbst einstellig sind. Die 6 s bei #71 können
in Wahrheit 7 oder 9 gewesen sein. Unter 10 s bleiben sie in jedem Fall, die
neue Untergrenze steht also; eine Genauigkeit auf die Sekunde gibt die Reihe
aber nicht her, und die Spannen sind entsprechend zu lesen.

Die Merge-Spalte trug bis zum 19.9.2026 ebenfalls die Benachrichtigungszeit.
Sie steht für #70 bis #72 jetzt auf der Committer-Zeit; die vier älteren
Zeilen wurden nicht nachgemessen und können um dieselben Sekunden zu spät
stehen.

## Was die Reihe nicht hergibt

In allen **fünf** Zeilen mit erfasstem Laufbeginn — #64, #65, #67, #70, #73 —
fiel der Merge, **bevor** der Lauf begann (2 bis 4 Sekunden nach «ready», der
Lauf begann nach 6 bis 8). Belegt ist damit: Ein Merge verhindert den Start
nicht, und der Lauf endet auf dem gemergten Head.

Bei #71 und #72 sagt die Reihe dazu nichts. Der Merge fiel dort 2 bzw. 3
Sekunden nach «ready» und der Kasten entstand nach 6 bzw. 13 — wann der Lauf
begann, steht aber nirgends, und aus der Kasten-Anlage darauf zu schliessen
hiesse, die Grösse zu erfinden, die gerade fehlt.

Am knappsten war es bei #73: Merge 16:47:00, Laufbeginn 16:47:03 — **drei
Sekunden**, vor #70 mit vier. Der Abstand schrumpft, überschritten ist er
nicht. Ob ein Merge einen **bereits laufenden** Review überlebt, ist weiterhin
ungemessen; dafür bräuchte es einen Merge grob zwischen 10 Sekunden und 2
Minuten nach «ready».
