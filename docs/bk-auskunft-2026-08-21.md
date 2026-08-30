# Auskunft der Bundeskanzlei zu Abdeckung und Weiterverwendung (21.08.2026)

*Federal Chancellery statement on API coverage and reuse — German original below,
English summary at the end.*

Warum dieses Dokument existiert: Die README erklärte den Abdeckungsunterschied
zwischen `api.termdat.bk.admin.ch/v2` und der Weboberfläche mit einer **Vermutung**
(«das legt nahe, dass der Suchindex validierte Einträge abdeckt»), und das Feld
`source` jeder Antwort behauptete, die Nutzungsbedingungen seien unbekannt. Beides
war eine Selbstauskunft des Servers über eine Frage, die man der Quelle stellen
kann. Sie wurde gestellt.

## Anfrage

Am 30.07.2026 an `terminologie@bk.admin.ch`, mit den Messwerten aus
[Issue #11](https://github.com/malkreide/termdat-mcp/issues/11): Suche nach
«Quellensteuer» — 12 Einträge auf der Weboberfläche, 7 über die API bei maximaler
Abfragebreite, Überschneidung genau ein Eintrag (447912); 10 der 12 Entry-IDs
liefern auch beim gezielten Abruf über `/v2/Entry` HTTP 200 mit leerem Körper.
Gefragt wurde nach Absicht, Auswahlkriterium, geplanter Abdeckung und Lizenz.

Damit ist zugleich die unten genannte Informationspflicht für den Betrieb dieses
Servers erfüllt: Zweck und Art der Nutzung (quelloffener, nicht kommerzieller
MCP-Konnektor, Quellenangabe in jeder Antwort) waren Gegenstand derselben Anfrage.
Eine **eigene** Weiterveröffentlichung stromabwärts braucht eine eigene Meldung.

## Antwort, wörtlich

> Sehr geehrter Herr Oezkan
>
> Danke für Ihr Interesse für TERMDAT. Zu Ihren Fragen:
>
> Ja, die öffentliche API bildet bewusst nur einen Teil der TERMDAT-Einträge ab.
> Die Auswahl der Einträge, die über die API verfügbar sind, orientiert sich an die
> Bedürfnisse der Übersetzerinnen und Übersetzer der Bundesverwaltung.
> Eine vollständigere Abdeckung ist nicht geplant.
> Die Weiterverwendung und Weiterveröffentlichung von TERMDAT-Inhalten ist nur
> unter Angabe der Quelle (www.termdat.ch) zulässig. Die Sektion Terminologie der
> Bundeskanzlei ist vorgängig über Zweck und Art der Weiterverwendung und
> Weiterveröffentlichung zu informieren.
>
> Freundliche Grüsse
>
> Bundeskanzlei
> Zentrale Sprachdienste, Sektion Terminologie
> Gurtengasse 3, 3003 Bern

## Was daraus im Server steht

| Befund | Wo er wirkt |
|---|---|
| Teilabdeckung ist **beabsichtigt**, kein Fehler und kein Scope-Parameter | Coverage-Caveat in `search_terms`, `hint` auf Leermengen, `caveat` in `check_terms` |
| Auswahlkriterium: **Bedarf der Übersetzerinnen und Übersetzer der Bundesverwaltung** — nicht Validierungsstatus, nicht Sammlung | dieselben Stellen; die frühere Vermutung «validierte Einträge» ist damit erledigt |
| Vollständigere Abdeckung ist **nicht geplant** | Bekannte Einschränkungen in beiden READMEs — kein Workaround in Aussicht |
| Weiterverwendung nur **mit Quellenangabe `www.termdat.ch`** | `ATTRIBUTION` in `src/termdat_mcp/models.py`, also Feld `source` jeder Antwort |
| Sektion Terminologie ist **vorgängig** über Zweck und Art zu informieren | ebenda |

Was die Antwort **nicht** hergibt: welche Einträge im Einzelfall zum
Übersetzungsbedarf zählen. Das Kriterium ist genannt, aber nicht so operationalisiert,
dass sich vorhersagen liesse, ob ein bestimmter Eintrag ausgeliefert wird. Der Server
kann deshalb weiterhin nur *messen*, ob er einen Eintrag bekommt, und darf aus einer
Leermenge nichts über TERMDAT als Ganzes schliessen.

## English summary

Asked on 2026-07-30 about the gap between the public API and the TERMDAT website,
the Terminology Section of the Swiss Federal Chancellery answered on 2026-08-21:

1. The public API **deliberately** exposes only part of the TERMDAT records.
2. The selection follows **the needs of the federal administration's translators**.
3. **No fuller coverage is planned.**
4. Reuse and republication are permitted **only with the source named
   (www.termdat.ch)**, and the Terminology Section **must be informed beforehand**
   of the purpose and manner of the reuse.

Point 4 replaced this server's earlier "no licence statement — clarify the terms
yourself" note: the terms exist, they are simply not in the I14Y catalogue record
(which still carries `license: null`).
