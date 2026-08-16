# Herkunft der Fixtures

**Erzeugt von `scripts/record_fixtures.py`. Nicht von Hand pflegen.**

Aufgezeichnet am **2026-08-15** von der einzigen Quelle dieses Servers:
`https://api.termdat.bk.admin.ch/v2`.

Ohne Datum ist «aufgezeichnet» nach zwei Jahren von «ausgedacht» nicht
mehr zu unterscheiden — die Datei sieht gleich aus.

**Es sind Ausschnitte, keine Vollabzuege.** Die Auswahlregel steht je
Datei dabei; Feldstruktur und Schluesselnamen sind unangetastet. Eine
Fixture belegt damit die *Form* der Antwort und einen datierten
Ausschnitt ihres Inhalts — nicht den Bestand. Aussagen ueber
Vollstaendigkeit gehoeren in Live-Tests.

**Die Suche sendet ihre Feld-Flags vollstaendig.** Ungesetzte Flags
behalten den API-seitigen Default (Terminus/Name/Abbreviation/
Phraseology = true), womit `fields` die Suche nur verbreitern, nie
verengen koennte. Die Aufzeichnung belegt deshalb dieselbe Anfrage, die
auch der Server stellt — samt aller elf Flags.

Fehlerpfade — 404, Timeouts, maskierte 4xx — bleiben handgeschrieben.
Die lassen sich nicht auf Zuruf aufzeichnen.

## `classification_de.json`

- **Quelle:** `https://api.termdat.bk.admin.ch/v2/Classification?languageCode=DE`
- **Aufgezeichnet:** 2026-08-15
- **Auswahl:** vollstaendig; alle Sachgebiete auf Deutsch
- **Groesse:** 1651 B
- **SHA-256:** `95eca2ab9dcb2ed7dffe6ca7e13f7714144a38efadf0c314417a423f6557d59a`

## `collection_de.json`

- **Quelle:** `https://api.termdat.bk.admin.ch/v2/Collection?languageCode=DE`
- **Aufgezeichnet:** 2026-08-15
- **Auswahl:** vollstaendig; alle Sammlungen auf Deutsch
- **Groesse:** 14226 B
- **SHA-256:** `a984887566d34a6ccbf52b7741f73da8b5dbcaa5d2c9d6d6e49d3da1cf087596`

## `search_detail.json`

- **Quelle:** `https://api.termdat.bk.admin.ch/v2/Search?SearchTerm=Sonderp%C3%A4dagogik&InLanguageCode=DE&ReturnType=Detail&MaxEntryCount=3&Field.Terminus=true&Field.Name=true&Field.Abbreviation=true&Field.Phraseology=true&Field.Definition=true&Field.Note=true&Field.Context=false&Field.Source=true&Field.Metadata=false&Field.Country=false&Field.Comment=false&ClassificationIds=1&ClassificationIds=2&ClassificationIds=24&ClassificationIds=3&ClassificationIds=4&ClassificationIds=22&ClassificationIds=5&ClassificationIds=6&ClassificationIds=7&ClassificationIds=8&ClassificationIds=23&ClassificationIds=10&ClassificationIds=11&ClassificationIds=12&ClassificationIds=13&ClassificationIds=14&ClassificationIds=15&ClassificationIds=16&ClassificationIds=17&ClassificationIds=18&ClassificationIds=19&ClassificationIds=20&ClassificationIds=21`
- **Aufgezeichnet:** 2026-08-15
- **Auswahl:** «Sonderpädagogik», ReturnType=Detail, 3 von hoechstens 3; Feld-Flags wie der Client sie sendet
- **Groesse:** 6214 B
- **SHA-256:** `37a132d900fadb7b5a9ff39443a25fd6a0e9f8218c908ea6e6ac8721155cfb83`

## `search_summary.json`

- **Quelle:** `https://api.termdat.bk.admin.ch/v2/Search?SearchTerm=Sonderp%C3%A4dagogik&InLanguageCode=DE&MaxEntryCount=3&Field.Terminus=true&Field.Name=true&Field.Abbreviation=true&Field.Phraseology=true&Field.Definition=true&Field.Note=true&Field.Context=false&Field.Source=true&Field.Metadata=false&Field.Country=false&Field.Comment=false&ClassificationIds=1&ClassificationIds=2&ClassificationIds=24&ClassificationIds=3&ClassificationIds=4&ClassificationIds=22&ClassificationIds=5&ClassificationIds=6&ClassificationIds=7&ClassificationIds=8&ClassificationIds=23&ClassificationIds=10&ClassificationIds=11&ClassificationIds=12&ClassificationIds=13&ClassificationIds=14&ClassificationIds=15&ClassificationIds=16&ClassificationIds=17&ClassificationIds=18&ClassificationIds=19&ClassificationIds=20&ClassificationIds=21&ReturnType=Summary`
- **Aufgezeichnet:** 2026-08-15
- **Auswahl:** «Sonderpädagogik», ReturnType=Summary, 3 von hoechstens 3; sonst gleiche Parameter wie search_detail
- **Groesse:** 3970 B
- **SHA-256:** `7ac4608f4ca05009adbec7f9553ec8871da5e1277157b8742cce98821b637bbf`

## `entry.json`

- **Quelle:** `https://api.termdat.bk.admin.ch/v2/Entry?EntryIds=106213&InLanguageCode=DE`
- **Aufgezeichnet:** 2026-08-15
- **Auswahl:** ein Eintrag (ID 106213), erster Treffer aus search_detail
- **Groesse:** 1926 B
- **SHA-256:** `f4802192a6406f5e346ed98d89a3359334dcc634d351845bdcd1b99314893d7e`
