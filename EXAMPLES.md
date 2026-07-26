# Use Cases & Examples — termdat-mcp

Praxisnahe Anfragen nach Zielgruppe. TERMDAT ist die Terminologiedatenbank der Schweizerischen Bundesverwaltung (Bundeskanzlei): offiziell validierte Bezeichnungen von Behörden, Departementen und Erlassen in DE / FR / IT / EN — mit Quellenangabe und Validierungsstatus. **Kein API-Key nötig** (öffentliche, unauthentifizierte API). Beachte: TERMDAT ist ein Namens-Archiv, kein Sachwörterbuch — es liefert amtliche Benennungen, keine Fachdefinitionen von Begriffen.

## 🏫 Bildung & Schule

**«Wie heisst die Bildungsdirektion offiziell auf Französisch und Italienisch?»**
**API-Key nötig:** Nein
→ `translate_term(term="Bildungsdirektion", from_language="DE", to_language="FR")`
→ `translate_term(term="Bildungsdirektion", from_language="DE", to_language="IT")`
Warum nützlich: Für mehrsprachige Elternbriefe, Websites und offizielle Korrespondenz muss der Behördenname exakt in der validierten Form stehen — TERMDAT liefert genau die amtliche Entsprechung statt einer freien Übersetzung.

**«Welche Erlasse und Behörden im Bildungsbereich sind in TERMDAT erfasst?»**
**API-Key nötig:** Nein
→ `list_classifications(language="DE")` (liefert u.a. `BILD` = Bildung)
→ `search_terms(search_term="Bildung", classification_ids=[<BILD-ID>], max_results=25)`
Warum nützlich: Verschafft einen Überblick über die offiziell benannten Bildungs-Organisationseinheiten des Bundes und der Kantone, bevor man sie in einem Dokument zitiert.

**«Sind die Behördennamen in unserem Schulreglement offiziell korrekt geschrieben?»**
**API-Key nötig:** Nein
→ `check_terms(terms=["Erziehungsdepartement", "Bildungsdirektion", "Staatssekretariat für Bildung"], language="DE")`
Warum nützlich: Kommunikations-QA in einem Aufruf — jede Bezeichnung wird als `validated`, `found_unvalidated` oder `not_found` zurückgemeldet, so lassen sich veraltete oder falsche Amtsnamen vor der Publikation erkennen.

## 👨‍👩‍👧 Eltern & Schulgemeinde

**«An welches Departement richte ich mich — und wie heisst es korrekt?»**
**API-Key nötig:** Nein
→ `search_terms(search_term="Departement", fields="Terminus,Abbreviation", max_results=25)`
Warum nützlich: Eltern und Schulgemeinden finden die exakte offizielle Bezeichnung samt gültiger Abkürzung, statt eine informelle oder überholte Variante zu verwenden.

**«Wie lautet die anerkannte Abkürzung dieses Bundesamts?»**
**API-Key nötig:** Nein
→ `search_terms(search_term="Bundesamt für Statistik", fields="Terminus,Abbreviation")`
Warum nützlich: Offizielle Abkürzungen (z.B. in Formularen oder Einladungen) sind validiert abrufbar — nützlich für die Schulgemeinde-Kommunikation mit Amtsstellen.

## 🗳️ Bevölkerung & öffentliches Interesse

**«Wie heisst dieser Erlass in allen vier Landessprachen?»**
**API-Key nötig:** Nein
→ `search_terms(search_term="Verordnung", max_results=10)` (liefert `entry_id`s)
→ `get_entries(entry_ids=[<gefundene ID>], in_language="DE", out_language="FR")`
Warum nützlich: Für Recherchen und Medienarbeit lassen sich die amtlichen Titel von Erlassen mit allen Sprachvarianten und Quellenreferenz belegen.

**«Ist TERMDAT gerade erreichbar und welche Felder sind durchsuchbar?»**
**API-Key nötig:** Nein
→ `api_status()`
Warum nützlich: Transparenz über Datenverfügbarkeit — die Statusabfrage meldet Erreichbarkeit, Anzahl Collections/Classifications und durchsuchbare Felder, ohne je stillschweigend leer zurückzugeben.

## 🤖 KI-Interessierte & Entwickler:innen

**«Zeige mir die verfügbaren Filterwerte (Collections/Classifications), damit ich Suchen gezielt einschränken kann.»**
**API-Key nötig:** Nein
→ `list_collections(language="DE")` (die ~140 Terminologie-Collections)
→ `list_classifications(language="DE")` (die 23 Sachklassifikationen)
Warum nützlich: Macht die Filterargumente `collection_ids` / `classification_ids` von `search_terms` für einen Agenten legibel — Grundlage für präzise, reproduzierbare Abfragen.

**«Portfolio-Kombination: amtliche Bezeichnung validieren und den zugehörigen Erlass im Recht nachschlagen.»**
**API-Key nötig:** Nein (für swiss-ip-mcp separat IGE-Zugangsdaten nötig)
→ `translate_term(term="Volksschulgesetz", from_language="DE", to_language="FR")` (termdat-mcp: offizielle Benennung)
→ danach in [`openlex-mcp`](https://github.com/malkreide/openlex-mcp): `openlex__zhlaw_get_law(identifier="VSG")` für den eigentlichen Gesetzestext
Warum nützlich: TERMDAT sichert die korrekte, mehrsprachige Benennung; ein Rechts-Server wie openlex-mcp liefert dann den Inhalt — saubere Trennung von Benennung und Sachvokabular.

## 🔧 Technische Referenz: Tool-Auswahl nach Anwendungsfall

| Ich möchte… | Tool(s) | Auth nötig? |
|---|---|---|
| Amtliche Bezeichnungen per Freitext suchen (mit Feld-, Collection- und Classification-Filtern) | `search_terms` | Nein |
| Die offizielle Entsprechung eines Begriffs in einer anderen Landessprache erhalten | `translate_term` | Nein |
| Bis zu 25 Begriffe gegen validierte Bezeichnungen prüfen (Kommunikations-QA) | `check_terms` | Nein |
| Bekannte Einträge über ihre numerische ID abrufen (alle Sprachvarianten) | `get_entries` | Nein |
| Die ~140 Terminologie-Collections als Filterwerte auflisten | `list_collections` | Nein |
| Die 23 Sachklassifikationen (z.B. `BILD` = Bildung) auflisten | `list_classifications` | Nein |
| Verfügbarkeit der TERMDAT-API und durchsuchbare Felder prüfen | `api_status` | Nein |

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_018dMqNTA37PLHvLRGriRDmq
