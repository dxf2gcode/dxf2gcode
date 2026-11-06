# R3 und R1b: gemeinsamer Umsetzungsplan

Stand: **06.11.2026**, untersucht auf `2acb289` mit vorhandenen lokalen
Dokumentationsänderungen. **Plan vom Nutzer am 06.11.2026 bestätigt.**
Vor der Umsetzung sind Commit, Push und ein Develop-Release beauftragt.
Die Softwareimplementierung beginnt erst im anschließenden eigenen Auftrag.
Bestätigte Fachregeln und technische Umsetzungsvorschläge sind unterschieden.
[Planungsabschluss](../archive/toolpath-refactoring-completed.md#r3-r1b-plan).

## 1. Ziel und bereits getroffene Entscheidungen

R3 trennt die importierte Zeichnung von ihrer Bearbeitung. R1b wird als
Verschieben von Konturzuordnungen zwischen Bearbeitungsschritten umgesetzt.
Im bisherigen Entwurf als Bearbeitungsgruppe bezeichnet, ist ein solcher
Schritt ein benannter Container wie Schruppen, Schlichten oder Bohren. Die
Einträge darin sind eigenständige Bearbeitungen mit Geometriereferenz.
Ein Gruppenwechsel verändert nicht den ursprünglichen DXF-Layer.

| ID | Entscheidung | Status |
| --- | --- | --- |
| D1 | Entities und Layers bleiben bestehen; Bearbeitung wird ein dritter Tab. Keine Umbenennung oder Ersetzung der beiden vorhandenen Tabs. | Vom Nutzer bestätigt |
| D2 | Eine Originalkontur kann mit mehreren Bearbeitungsschritten verknüpft sein. Kopieren erzeugt eine weitere Bearbeitungszuordnung, keine zweite Originalkontur. | Bestätigt; Verschieben und Kopieren gehören bereits zur ersten nutzbaren Version |
| D3 | Beim Verschieben bleiben eigene Tiefen, Vorschübe und Leads erhalten; geerbte Werte stammen aus dem Zielschritt. Werkzeug folgt verbindlich dem Ziel gemäß D8. | Vom Nutzer bestätigt |
| D4 | Entities und Layers dienen der Geometrieauswahl. Layers zeigt dauerhaft die Originalkonturen und liefert die Ausgangsstruktur des Bearbeitungsbaums. Kein Verschieben zwischen DXF-Layern; Bearbeitungsänderungen brauchen einen aktiven Bearbeitungskontext. | Vom Nutzer präzisiert und bestätigt |
| D5 | Neue versionierte `.d2g`-Struktur; bisherige Versionen 1.1–1.5 weiter lesen, migrierte Dateien zunächst unter neuem Namen speichern. | Vom Nutzer bestätigt |
| D6 | Erste nutzbare Version umfasst Gruppen, Verschieben und Kopieren gemäß D2. Manuelle Stegregionen, Automatik und Fang folgen später; vorhandene BREAKS:-Funktion bleibt erhalten. | Vom Nutzer bestätigt |
| D8 | Jeder Bearbeitungsschritt hat genau ein Werkzeug. Verschieben übernimmt das Zielwerkzeug; alte eigene Werkzeugzuweisungen benötigen getrennte Schritte. | Vom Nutzer bestätigt |
| D14 | Geometrieauswahl zeigt alle Verknüpfungen; ein Schritt ist ausdrücklich aktiv für Vorschau und Parameterbearbeitung. | Vom Nutzer bestätigt |
| D7 | Unklare alte Tiefen-/Vorschubwerte bei Migration als eigene Werte erhalten; bekannte Vererbungszustände bewahren. Später bewusst auf Schrittvorgaben umstellen. | Vom Nutzer bestätigt |
| D15 | Beim Kopieren eigene Tiefen/Vorschübe/Leads kopieren; geerbte Werte und Werkzeug aus dem Ziel übernehmen. Beide Bearbeitungen sind unabhängig änderbar. | Vom Nutzer bestätigt |
| D16 | Je Bearbeitungsschritt genau eine Bearbeitungsart und ein Werkzeug. Schruppen/Schlichten sind freie Namen; Art und Werkzeug werden ausdrücklich eingestellt. | Vom Nutzer bestätigt |
| D9 | Nach erneutem DXF-Import bleiben neue Konturen zunächst ohne Bearbeitungszuordnung; eindeutig wiedererkannte bestehende Verknüpfungen bleiben erhalten. | Vom Nutzer bestätigt |
| D10 | Unpassende Geometrie beim Verschieben/Kopieren vorab erklären und die gesamte Aktion ohne Teiländerung ablehnen. | Vom Nutzer bestätigt |
| D12 | Rückgängig/Wiederholen für die neuen Bearbeitungsaktionen gehört bereits zur ersten Version. | Vom Nutzer bestätigt |
| D17 | Werkzeugdaten und Bearbeitungsvorgaben im Projekt erhalten; Änderungen externer Profile erst durch eine ausdrückliche Aktualisierung übernehmen. | Vom Nutzer bestätigt |
| D18 | Gültige Verschiebe-/Kopieraktionen direkt ausführen, wirksame Änderungen anzeigen und Undo anbieten; keine zusätzliche Bestätigungsabfrage. | Vom Nutzer bestätigt |
| D13 | Bei der ersten Übernahme entspricht die Bearbeitungsstruktur dem Layerbaum; spätere Änderungen bleiben ausschließlich in Bearbeitung. | Bestätigt; Werkzeugtrennung nach D8 erfordert bei gemischten Alt-Layern getrennte Schritte |

Die Bedienregeln einschließlich Abschnitt 7 sind abgestimmt. Technische
Details werden innerhalb dieser Regeln umgesetzt; größere Scope-Änderungen
oder neue fachliche Mehrdeutigkeiten werden vor ihrer Umsetzung besprochen.

### Ein konkreter Bedienablauf

1. Eine DXF mit den Layern Innen und Außen öffnen. Entities und Layers
   zeigen weiterhin die Zeichnungsstruktur.
2. Der neue Tab Bearbeitung zeigt zunächst eine Gruppe je bisherigem
   Bearbeitungslayer. Das erhält den vertrauten Einstieg und die Reihenfolge.
3. Eine Gruppe Schlichten anlegen und Werkzeug, Tiefe und Leads vorgeben.
4. Zwei Arbeitsgänge aus Innen nach Schlichten verschieben. Die Konturen
   bleiben im DXF-Layer Innen. Ihre Arbeitsgang-Identitäten bleiben erhalten.
5. Die Oberfläche zeigt beispielsweise: Werkzeug geerbt 2 → 4, explizite
   Endtiefe unverändert −3 mm, Lead-in geerbt Radius → Gerade.
6. Die Vorschau verwendet die neuen wirksamen Werte; der Export folgt dem
   Bearbeitungsbaum von oben nach unten. Speichern und Laden erhält beides.

Die neu präzisierte Bedienidee ist: Originalkontur auswählen und mit
„Zu Bearbeitungsschritt hinzufügen …“ beispielsweise Schruppen und Schlichten
verknüpfen. Im Bearbeitungsbaum bedeutet „Verschieben“ die bestehende
Zuordnung versetzen; „In weiteren Schritt kopieren …“ erzeugt eine neue
Bearbeitungsidentität mit derselben Geometriereferenz. Verschieben erzeugt
niemals eine Kopie. Beide Bedienaktionen gehören gemäß der aktualisierten
Nutzerentscheidung D2 zur ersten nutzbaren Version. Gemäß D15 übernimmt
die Kopie die eigenen Tiefen/Vorschübe/Leads; geerbte Werte, Werkzeug und
Bearbeitungsart stammen aus dem Zielschritt. Spätere Parameteränderungen
an einer Zuordnung ändern die andere nicht.

Beispiel der bestätigten Werkzeugtrennung und Mehrfachzuordnung:

```text
Layers                         Bearbeitung
  Außen                          Schruppen · T2
    Kontur A                       Kontur A → Original A
  Bohrungen                      Schlichten · T4
    Kreis B                        Kontur A → Original A
                                 Bohren · T3
                                   Kreis B → Original B
```

Dieselbe Originalkontur wird einmal angezeigt und gespeichert; jede ihrer
Bearbeitungen besitzt eigene Werte, Richtung, Startpunkt und Exportposition.

## 2. Befunde aus dem aktuellen Code

| Aktuelle Stelle | Bedeutung für die Umsetzung |
| --- | --- |
| [Shape](../../source/dxf2gcode/domain/project/shape.py) | Verbindet Geometrie, Bearbeitungsparameter, Startpunkt/Richtung, Auswahl und genau ein `parentLayer`. Diese Zuständigkeiten müssen schrittweise getrennt werden. |
| [LayerContent](../../source/dxf2gcode/domain/project/layercontent.py) | Enthält Shape-Mitgliedschaft, Werkzeugvorgaben, Sonderlayersemantik und Exportreihenfolgen. Ein neuer Baum allein schafft noch keine unabhängigen Gruppen. |
| [ToolSettings](../../source/dxf2gcode/domain/project/tool_settings.py) und [Shape-Aktionen](../../source/dxf2gcode/application/shapes.py) | Eigene Werkzeugwerte sind bereits modelliert. Einige Lead-Werte kennen explizite Vererbungszustände; Tiefen/Vorschübe sind dagegen häufig direkt gespeicherte Zahlen. |
| [Project](../../source/dxf2gcode/domain/project/project.py) | Stellt Konturen über Layernamen und Geometriehashes wieder her; beim kleinen Reload wird auch die Shape-Nummer verwendet. Das genügt nicht als dauerhafte Arbeitsgangreferenz. |
| [TreeHandler](../../source/dxf2gcode/presentation/qt/treehandling.py) | Überträgt die Baumreihenfolge in `exp_order`/`exp_order_complete`. Diese Exportzuständigkeit muss kontrolliert an den Bearbeitungsbaum übergehen. |
| [Planungseingaben](../../source/dxf2gcode/adapters/toolpath/planning.py) | Liest aufgelöste Shape-/Werkzeug-/Layerwerte. Neuer Adapter soll Arbeitsgangwerte liefern, ohne Geometriealgorithmen oder den Planvertrag neu zu schreiben. |
| [Routenoptimierung](../../source/dxf2gcode/application/optimization/routes.py) | Optimiert derzeit innerhalb der Layer; beide vorhandenen Modi und die relative Reihenfolge müssen erhalten bleiben. |
| [Breaks](../../source/dxf2gcode/adapters/postprocessor/breaks.py) | Bestehende BREAKS:-Geometrien wirken über Layergrenzen hinweg; neue arbeitsgangbezogene Regionen dürfen diesen Importvertrag nicht unbemerkt ändern. |

A1 bleibt die Grundlage: Domain/Application importieren ohne Qt und konkrete
Außenadapter. Ein gemeinsamer Plan steuert Vorschau und Export; blockierende
Fehler stoppen den gesamten Export vor der Ausgabe. R3/R1b dürfen diese
Grenzen nicht zurücknehmen.

## 3. Vorgeschlagenes Modell

Die folgenden Namen sind Entwurfsnamen, keine bereits existierenden Klassen.

```text
Projektvorgaben / Projektwerkzeuge [gespeicherter Stand]

Zeichnung
  Quelllayer / Entities / Blockinstanzen
    GeometryContour [geometry_id, Herkunft, Geometrie, Revision]
                              ^
                              | geometry_id
Bearbeitungsplan               |
  MachiningGroup [group_id, Name, Vorgaben, geordnete Einträge]
    Operation [operation_id, Geometriereferenz, eigene Werte, Zustand]
    LiteralAction [action_id, benutzerdefinierter G-Code]
    Operation [...]

TabRegion [region_id, Form, absolute Steg-Z-Höhe, Zuordnungen]
```

- **GeometryContour:** gemeinsam genutzte Originalkontur und Herkunft:
  Quelldatei, DXF-Layer, Entity-/Blockinstanzbezug und Fingerabdruck. Keine
  Werkzeugparameter und keine Exportreihenfolge.
- **Operation:** konkrete Bearbeitung dieser Kontur innerhalb eines Schritts.
  Bearbeitungsart und Werkzeug kommen verbindlich aus diesem Schritt;
  Kompensationsseite, Richtung, Startpunkt, Optimierungsfreigabe, Aktivierung,
  eigene Parameter und zugeordnete Stege. Ihre Identität bleibt beim
  Verschieben, Umbenennen und Speichern erhalten.
- **MachiningGroup:** benannte, geordnete Sammlung von Arbeitsgängen mit
  Vorgaben; in der Oberfläche heißt sie Bearbeitungsschritt. Sie kann leer
  sein und Konturen unterschiedlicher DXF-Layer enthalten. Gemäß D8 gilt
  genau ein Werkzeug je Schritt; mehrere Schritte mit demselben Werkzeug
  sind möglich. Gemäß D16 ist auch die Bearbeitungsart je Schritt
  einheitlich. Zunächst keine verschachtelten Gruppen vorschlagen.
- **LiteralAction:** expliziter G-Code-Eintrag ohne fingierte Geometrie.
  Bestehende Werkzeugwechsel-/Rückkehrverträge bleiben anwendbar.
- **TabRegion:** eigenes Bearbeitungsobjekt mit stabiler Identität; kein neu
  erzeugter DXF-Layer als dauerhaftes Ersatzmodell.

Der Bearbeitungsplan ist die einzige verbindliche Reihenfolge für den
Export. Entities und Layers sind weitere Ansichten auf dieselbe Zeichnung;
sie erzeugen keinen zweiten konkurrierenden Bearbeitungsplan.

Für den Übergang darf ein Adapter kurzlebige Shape-/Layer-Sichten für die
bestehende Vorbereitung erzeugen. Diese Sichten sind abgeleitet, werden
nicht separat gespeichert und schreiben keine Bearbeitung zurück in die
gemeinsam verwendete Geometrie. Der alte und neue Zustand dürfen nicht
dauerhaft durch gegenseitige Synchronisierung konkurrieren.

### Identitäten und erneuter DXF-Import

Projektinterne IDs sind unabhängig von Zeilennummern, Gruppennamen und
laufenden Shape-Nummern. Eine neue ID allein löst die Wiedererkennung einer
extern geänderten DXF jedoch nicht.

Vorschlag für die Zuordnung bei Reload:

1. Herkunft einschließlich Blockinstanz und vorhandener Entity-Identität
   verwenden; die tatsächliche Verfügbarkeit im Importadapter zuvor prüfen.
2. Mit Geometriefingerabdruck in Zeichnungskoordinaten gegenprüfen; globale
   Werkstücktransformationen nicht als neue Originalkontur behandeln.
3. Nur eindeutige Treffer automatisch zuordnen. Identische mehrfach vorhandene
   Konturen und veränderte Blockinstanzen müssen als Mehrdeutigkeit erkannt werden.
4. Fehlende oder mehrdeutige Referenzen erhalten ihre Arbeitsgangwerte und
   erscheinen als ungelöst. Aktivierte ungelöste Arbeitsgänge blockieren den
   Export; keine automatische Zuordnung zur nächstgelegenen Kontur.
5. Gemäß D9 erscheinen neue Konturen nach erneutem Import in einer
   Zuordnungsliste und erhalten keinen automatischen aktiven Arbeitsgang.
   Sie bleiben im Original-Layer sichtbar; die bestehende Bearbeitung wird
   nicht durch zusätzliche Exportbewegungen erweitert. Erst eine bewusste
   Zuordnung erzeugt neue Bearbeitungseinträge.

Unzugeordnete neue Geometrie ist keine fehlerhafte aktive Bearbeitung und
blockiert den Export der bestehenden gültigen Schritte nicht. Fehlende oder
mehrdeutige Referenzen eines bereits aktiven Eintrags bleiben dagegen
blockierend. Bei der ersten Dateierstellung gilt weiterhin D13: Ausgangsbaum
aus den Layern aufbauen; D9 betrifft spätere Neuimporte.

## 4. Parameterherkunft und Verschieben

Wirksame Werte benötigen zusätzlich ihre Herkunft. Die Auflösung soll zentral
erfolgen; UI, Planung, Export und Persistenz verwenden denselben Resolver.

Auflösung: eigener Arbeitsgangwert → Schrittvorgabe → gespeicherter
Projektstandard. Werkzeug und Bearbeitungsart stammen verbindlich aus dem
Schritt. Gemäß D17 werden Werkzeugdaten und Bearbeitungsvorgaben im Projekt
gespeichert; ein erneutes Öffnen liest sie nicht still aus veränderten globalen
Profilen nach. Globale Werte dienen beim Anlegen als Ausgangswerte.

Technischer Entwurf zur konsistenten Werkzeughaltung: eine projektinterne
Werkzeugtabelle, auf die die Schritte verweisen. Eine Werkzeugnummer hat
innerhalb eines Projekts eine eindeutige Werkzeugdefinition; Schritte mit
demselben Werkzeug bekommen nicht unabhängig verschiedene Durchmesser.
Eine bewusste Aktualisierung zeigt daher alle betroffenen Schritte und
übernimmt die Werkzeugdefinition gemeinsam. Eigene Bearbeitungswerte werden
dabei nicht zu geerbten Werten umgedeutet oder still zurückgesetzt.

„Vorgaben aktualisieren“ ist eine ausdrückliche Aktion mit nachvollziehbaren
Änderungen und Undo. Fehlt das ursprüngliche Werkzeug inzwischen in der
globalen Tabelle, bleiben seine gespeicherten Projektdaten erhalten; kein
automatischer Ersatz durch Werkzeug 1. Diese Regel betrifft Bearbeitungs-
und Werkzeugvorgaben, nicht allgemeine UI-Einstellungen wie Farben/Layout.
Die endgültigen Datenfeldnamen werden in P1 festgelegt.

**Wichtiger Migrationsfall:** Eine alte gespeicherte Tiefe von −3 mm verrät
nicht zuverlässig, ob sie früher bewusst gesetzt oder nur aus einem Standard
kopiert wurde. Gleichheit mit einem Standard ist kein Beweis für Vererbung.
**Bestätigte Regel D7:** Solche Werte bei Übernahme erhalten und als eigene
Werte behandeln. Wo vorhandene Flags/Defaults echte Vererbung belegen, bleibt diese
erhalten. „Gruppenvorgabe verwenden“ ist anschließend eine bewusste Aktion.

Für jedes Parameterfeld wird vor dem Umbau eine Zuordnungstabelle erstellt:
Quelle heute, neuer Eigentümer, eigene/geerbte Darstellung, Migration,
Einheitenumrechnung und Planinvalidierung. Das umfasst Werkzeug, Drehzahl,
Z-Tiefen, Vorschübe, Offset, Leads, Overcut, Messerwerte und Steg-Passauswahl.

### Atomarer R1b-Anwendungsfall

`MoveOperations` soll Quelle, Ziel und Einfügeposition vor jeder Änderung
prüfen. Für Mehrfachauswahl gilt die bisher sichtbare Bearbeitungsreihenfolge.
Dann werden die wirksamen Änderungen berechnet. Gemäß D18 wird eine
gültige Aktion unmittelbar gemeinsam übernommen. Anschließend zeigt eine
nicht blockierende Rückmeldung die betroffenen Einträge und wesentlichen
Wertänderungen; Rückgängig ist direkt verfügbar. Es gibt keinen zusätzlichen
Bestätigungsdialog. D10 gilt unverändert: Unpassende Geometrie wird vor der
Änderung mit einer verständlichen Erklärung abgelehnt.

- Arbeitsgang-IDs und Geometriereferenzen bleiben erhalten.
- Eigene Tiefen, Vorschübe und Leads bleiben erhalten; geerbte Werte
  werden im Ziel aufgelöst. Das Werkzeug gehört gemäß D8 zum Zielschritt;
  ein individueller Werkzeugoverride ist im neuen Modell nicht vorgesehen.
- Quell-/Ziellisten und Mitgliedschaft ändern sich gemeinsam oder gar nicht.
- Pläne, Projektionen und Routenendpunkte der betroffenen Arbeitsgänge werden
  ungültig; die Originalgeometrie und nicht betroffene Arbeitsgänge bleiben erhalten.
- Ungültige Auswahl, fremdes Projekt, unzulässiger Zieltyp oder Abbruch ändern nichts.
- „Nach oben/unten“ und „In Gruppe verschieben …“ benutzen denselben
  Anwendungsfall wie Drag-and-drop. Kopieren ist ein eigener Anwendungsfall
  mit neuer Bearbeitungs-ID und unveränderter Geometrie-ID und gehört zur
  ersten Version. Gemäß D15 werden eigene Tiefen/Vorschübe/Leads kopiert;
  geerbte Werte und Werkzeug stammen aus dem Ziel, die Art gemäß D16 ebenfalls.
  Die Kopie ist anschließend unabhängig bearbeitbar. Abbruch erzeugt keine
  unvollständigen Kopien.
- Gemäß D12 erfasst Rückgängig/Wiederholen die neuen Bearbeitungsaktionen
  bereits in der ersten Version. Eine Mehrfachaktion ist ein gemeinsamer
  Undo-Schritt; abgelehnte oder abgebrochene Aktionen erzeugen keinen Eintrag.
  Wiederholen verwendet dieselben Bearbeitungs-IDs und erzeugt keine zweite
  Kopie. Quell-/Ziellisten, eigene/geerbte Werte, Auswahlkontext und
  Planinvalidierung werden gemeinsam wiederhergestellt. Keine allgemeine
  Undo-Funktion für alle bisherigen Import-/CAD-Aktionen versprechen.

Ein Wechsel der Schrittart muss vor Verschieben/Kopieren validiert werden.
Beispielsweise kann eine offene Linie nicht als Bohrkontur übernommen werden.
**Bestätigte Regel D10:** Die gesamte ausgewählte Aktion ohne Teilübernahme
ablehnen und die betroffenen Konturen samt Grund nennen. Auch gültige
Einträge derselben Auswahl werden nicht heimlich übernommen. Quelle, Ziel,
Reihenfolge und Undo-Verlauf bleiben bei Ablehnung unverändert. Derselbe
Validator gilt für Drag-and-drop, Menü und spätere weitere Aufrufwege.

Auch bei grundsätzlich passender Geometrie können mit dem Zielwerkzeug
Planungsfehler entstehen, etwa durch ungültige Leads. Solche späteren Fehler
bleiben nach dem A1-Vertrag sichtbar und blockieren den gesamten Export;
keine automatische Korrektur gespeicherter Werte. Die zulässigen Parameter
je Schrittart werden in einer eigenen Matrix festgelegt, einschließlich
G40 für Bohren und der vorhandenen Pocket-/Maschinenregeln.

## 5. Oberfläche mit drei Tabs

### Entities und Layers

Beide vorhandenen Tabs bleiben entsprechend D1 bestehen. Ihre Struktur und
die Herkunftsdarstellung werden nicht durch Bearbeitungsgruppen ersetzt.
Entities und Layers dienen gemäß D4 der Auswahl der Originalgeometrie.
Zwischen DXF-Layern wird weder verschoben noch eine Konturkopie angelegt.
Der neue Bearbeitungsbaum wird anfänglich aus der Layerstruktur aufgebaut,
entwickelt sich anschließend unabhängig. Eine spätere Umordnung der
Bearbeitung verändert weder Layers noch Entities.

**Bestätigter Auswahlvertrag (D14):** Beim Auswählen einer Originalkontur
werden alle zugehörigen Bearbeitungseinträge sichtbar markiert.
Ein ausdrücklich aktiver Schritt bestimmt die editierbaren Werte
und die hervorgehobene Vorschau. Bei mehreren Referenzen keine willkürliche
Bearbeitung aktivieren und keine Parameteränderung automatisch auf alle
übertragen. Ein Klick auf einen Bearbeitungseintrag aktiviert dagegen genau
diesen Kontext und markiert seine Originalkontur in Layers/Entities/Canvas.
Die konkrete Darstellung des Parameterbereichs wird in P0 skizziert.

Zeichnungssichtbarkeit, Auswahl und Exportaktivierung sind getrennte Zustände.
Die bisherigen Checkboxen müssen einzeln zugeordnet und erklärt werden;
sie dürfen nicht im Zuge des Umbaus unbemerkt ihre Wirkung wechseln.

### Neuer Tab Bearbeitung

- Gruppen anlegen, umbenennen, auswählen und sortieren; leere Gruppen zulassen.
- Arbeitsgänge mit Konturbezeichnung, Quelllayer, Operationstyp, effektivem
  Werkzeug und Diagnose anzeigen. Eigene/geerbte Werte unterscheidbar machen.
- Mehrfachauswahl, eindeutige Einfügemarkierung und Ziehen zwischen Gruppen.
- Gleichwertige Menü-/Tastaturaktionen für Verschieben und Sortieren.
- Exportaktivierung und Optimierungsfreigabe sichtbar halten.
- Gruppenauswahl markiert ihre Geometrien; Arbeitsgangauswahl zeigt dessen
  geplante Bahn. Die Originalgeometrie wird je Kontur nur einmal gezeichnet.
- Löschen einer Gruppe mit Inhalt erfordert eine bewusste Wahl: Arbeitsgänge
  in eine andere Gruppe verschieben oder Arbeitsgänge entfernen. Die
  Zeichnungsgeometrie wird dadurch nicht gelöscht.

Keine Ribbon-Abhängigkeit: Die bestehenden Qt-Ansichten/Aktionen reichen für
diesen Umbau. GUI1 bleibt ein eigener optionaler Entwurf.

## 6. Reihenfolge, Sonderfälle und Haltestege

**Export und Optimierung:** Gruppenreihenfolge bleibt fest; innerhalb einer
Gruppe gilt die sichtbare Eintragsreihenfolge. Die vorhandenen Modi
`CONSTRAIN_ORDER_ONLY` und `CONSTRAIN_PLACE_AFTER` sowie ihre relative
Reihenfolgesemantik bleiben erhalten. Keine Optimierung über Gruppengrenzen.
Custom-G-Code und weitere ausdrücklich festgelegte Ablaufgrenzen müssen
gesondert behandelt werden; Optimierung darf sie nicht unbemerkt überqueren.
Kein allgemeines automatisches „Innen vor Außen“ ohne eigenen Auftrag.
Routenanzeige bleibt separat und wird nicht durch eine reine Vorschauaktion aktiviert.

**Bestätigte Werkzeugregel D8:** Genau ein Werkzeug je Bearbeitungsschritt.
Das Werkzeug gehört zum Schritt und wird beim Verschieben aus dem Ziel
übernommen. Eigene Tiefen/Leads bleiben gemäß D3 erhalten. Alte individuelle
Werkzeugzuweisungen werden in getrennte Schritte überführt; sie werden nicht
stillschweigend auf ein gemeinsames Werkzeug vereinheitlicht.

Schruppen und Schlichten bleiben auch bei gleichem Werkzeug getrennte
Schritte, wenn der Nutzer eine getrennte Reihenfolge/Vorgabe möchte. Keine
automatische Zusammenlegung oder Umsortierung aller Schritte desselben Tools.
Der Exporter entscheidet Werkzeugwechsel aus tatsächlicher Folge und Profil.

**Migrationsdetail vor P1 konkretisieren:** Ein alter Layer kann mehrere eigene
Shape-Werkzeuge und Bearbeitungsarten enthalten. Strikte Trennung nach Tool
und Art und gleichzeitig exakt identischer Anfangsbaum sind dafür nicht
ohne Ausnahme erfüllbar. Empfehlung
zu den bestätigten Regeln D8/D16: im Bearbeitungsbaum getrennte, nach
Werkzeug und Bearbeitungsart benannte Schritte anlegen und die Ausnahme anzeigen; Original-Layers unverändert
lassen. Dabei zusammenhängende Werkzeugabschnitte erhalten, damit etwa die
Reihenfolge T2 → T4 → T2 nicht zu T2 → T2 → T4 umsortiert wird. Die genaue
Migration wird vor Umsetzung mit einem solchen Altprojekt abgestimmt.

**Sonderlayer:** IGNORE:-, BREAKS:- und andere Importkonventionen werden beim
Import ausgewertet; sie sind keine frei austauschbaren Bearbeitungsgruppen.
Break-Regionen und G-Code-Einträge benötigen eigene zulässige Ziele und dürfen
nicht als normale Kontur in einen Fräs-/Bohrvorgang verwandelt werden.

**Manuelle Haltestege: gemäß D6 ausdrücklich späteres Folgepaket.**
Bestehende BREAKS:-Layer, Z-Werte und Passauswahl werden schon in der
Grundversion unverändert übernommen. Für das spätere Paket ist vorgesehen:

- Rechteck im Canvas anlegen, auswählen, verschieben, Größe/Z-Höhe ändern und
  löschen. Neue Regionen zunächst ausgewählten Arbeitsgängen zuordnen.
- Bestehende globale BREAKS:-Wirkung als ausdrückliche Kompatibilitätszuordnung
  übernehmen. Ein Gruppenwechsel verliert diese Zuordnung nicht.
- Absolute Steg-Z-Höhe und „Process breaks from“ erhalten; Regionen wirken
  auf die tatsächlich geplante, gegebenenfalls kompensierte Bahn.
- Projektspeicherung erhält Form, ID und Zuordnungen. Vorschau und Export
  verwenden dieselben Stegaktionen und dieselbe Tiefenpassauswahl.
- Automatik und Fang als getrennte Folgepakete planen: Vorschläge müssen
  korrigierbar sein; Fangtoleranz und unterstützte Geometriearten vorher festlegen.

**Teilkonturen:** Startpunkt/Richtung gehören zum Arbeitsgang, nicht zur
gemeinsam referenzierten Originalgeometrie. Das Modell soll spätere Angaben
je resultierender Teilkontur ermöglichen. Deren vollständige Bedienung und
stabile Neuzuordnung sind weiterhin ein gesonderter, zurückgestellter Umfang.

## 7. Abgestimmter Bedienvertrag und Funktionsskizze

Der Nutzer hat den Plan einschließlich Original-/Bearbeitungskontur-Trennung
bestätigt. Skizze und Beispiele konkretisieren den abgestimmten Vertrag.
Die spätere implementierte Oberfläche und Migration werden anhand der Matrix
abgenommen; eine Planfreigabe behauptet keine bereits erfolgte GUI-Abnahme.

**Name und Bearbeitungsart:** Schrittname frei editierbar, mit Vorschlag aus
dem Layernamen. Bearbeitungsart und Werkzeug sind getrennte, vorbelegte Felder.
Umbenennen verändert keine Werkzeugbahn. Beim Zuordnen zu einem vorhandenen
Schritt werden dessen Werkzeug und Art übernommen.

**Ganzen Layer zuordnen:** Layer im Tab Layers auswählen; damit seine Konturen
auswählen. Über „Bearbeitungsschritt aus Auswahl erstellen …“ Name, Art und
Werkzeug festlegen. „Verschieben“ übernimmt bestehende Zuordnungen;
„Zusätzlich bearbeiten“ legt neue an. Auch bei ganzer Layerauswahl gilt D10:
bei einer unpassenden Kontur gesamte Aktion ablehnen. Die Original-Layer-
Mitgliedschaft bleibt unverändert.

**Gespeicherte Inhalte:** Der Schritt speichert seine Vorgaben; die einzelne
Bearbeitungskontur speichert Geometriereferenz, eigene Werte, Richtung,
Startpunkt und Aktivierung. Originalkontur und berechneter Werkzeugweg sind
davon getrennt. Eine Bearbeitungskontur ist keine zweite Geometriekopie.

D11 folgt aus der vereinbarten Trennung: Entfernen einer
Bearbeitungszuordnung löscht die Originalkontur und ihre übrigen Zuordnungen
nicht. Eine zusätzliche CAD-Funktion zum Löschen der Originalgeometrie ist
nicht Teil dieses Auftrags. Beim Entfernen eines ganzen Schritts ist dessen
Inhalt ausdrücklich zu behandeln; Undo stellt die Bearbeitung wieder her.

Technische Entscheidungen wie die genaue Codec-Implementierung werden aus
dem vereinbarten Verhalten abgeleitet und im Entwurf begründet; sie müssen
nicht einzeln als Bedienentscheidung abgefragt werden.

### Skizze des dritten Tabs

```text
[ Entities ] [ Layers ] [ Bearbeitung ]

Bearbeitung                         Originalgeometrie im Canvas
  Schruppen · Kontur · T2            Kontur A ist einmal vorhanden.
    Kontur A  [Export an]            Auswahl markiert ihre beiden
  Schlichten · Kontur · T4           Verknüpfungen im Bearbeitungsbaum.
    Kontur A  [aktiv] [Export an]    Hervorgehoben: Bahn von Schlichten.
  Bohren · Bohren · T3
    Kreis B   [Export an]

Aktive Bearbeitung: Schlichten / Kontur A
  Werkzeug   T4              aus Schritt, hier nicht überschreibbar
  Endtiefe   −3 mm           eigener Wert   [Schrittvorgabe verwenden]
  Zustellung −0,2 mm         aus Schritt
  Vorschub   400 mm/min      eigener Wert   [Schrittvorgabe verwenden]

Rückmeldung: Kontur A kopiert; T2 → T4; Zustellung −0,5 → −0,2 mm
             [Rückgängig]
```

Dies ist eine Funktionsskizze, kein fertiger GUI-Entwurf. Zahlen dienen nur
der Bedienerklärung. `[aktiv]` bezeichnet den Editier-/Vorschaukontext;
`[Export an]` bezeichnet Exportaktivierung. Sichtbarkeit der Originalgeometrie
ist ein davon getrennter Zustand in der Zeichnungsansicht. Beide verknüpften
Bearbeitungen sind in der Skizze für die Anzeige markiert; nur Schlichten
ist aktiv. Die konkrete Darstellung der Markierung wird in P0 geprüft.

### Beispiel: Kopieren mit eigenen und geerbten Werten

Kontur A aus Schruppen nach Schlichten kopieren:

| Wert | Bisherige Bearbeitung | Neue Bearbeitung in Schlichten |
| --- | --- | --- |
| Originalkontur | A | Dieselbe A, keine neue Geometrie |
| Bearbeitungs-ID | Bestehende ID | Neue eigene ID |
| Werkzeug | T2 aus Schruppen | T4 aus Schlichten |
| Art | Kontur aus Schruppen | Kontur aus Schlichten |
| Endtiefe | −3 mm, eigener Wert | −3 mm, eigener Wert kopiert |
| Zustellung | −0,5 mm, geerbt | −0,2 mm, aus Zielschritt |
| Vorschub | 400 mm/min, eigener Wert | 400 mm/min, eigener Wert kopiert |
| Änderung später an Schlichten | — | Verändert Schruppen nicht |

Die Aktion läuft direkt. Die Rückmeldung erklärt die Änderungen und bietet
Undo an. Rückgängig entfernt genau die neue Zuordnung, nicht Kontur A.
Redo stellt dieselbe neue Bearbeitungs-ID wieder her. Bei Verschieben würde
dagegen die vorhandene Bearbeitungs-ID erhalten und die Quellzuordnung
entfernt; Undo setzt deren ursprüngliche Mitgliedschaft wieder ein.

### Beispiel: Migration eines gemischten alten Layers

Angenommene alte Ausgabereihenfolge im Layer Außen:

```text
A: Kontur T2 → B: Kontur T4 → C: Kontur T2 → D: Bohren T3
```

Geplante Übernahme unter Erhalt der Ausgabereihenfolge:

```text
Außen · Kontur · T2 (1)  → A
Außen · Kontur · T4      → B
Außen · Kontur · T2 (2)  → C
Außen · Bohren · T3      → D
```

Damit bleiben Reihenfolge, tatsächliche Werkzeuge und Bearbeitungsarten
erhalten. A und C werden nicht automatisch zusammengezogen, obwohl beide
T2 verwenden. Original-Layers zeigt weiterhin Außen mit A/B/C/D. Bei einem
einheitlichen alten Layer genügt dagegen genau ein neuer Schritt, sodass die
anfängliche Struktur dem Layerbaum entspricht. Zugehörige Custom-G-Code-
Einträge bleiben an ihrer bisherigen Ablaufposition; sie dürfen beim
Aufteilen nicht gesammelt an den Anfang oder das Ende verschoben werden.

## 8. Speicher- und Migrationsentwurf

Gemäß bestätigter D5-Entscheidung neue getrennte Tabellen für Zeichnung/Herkunft, Gruppen,
Arbeitsgänge, G-Code-Aktionen und Stegregionen speichern. Referenzen erfolgen
über IDs; Reihenfolgen sind ausdrücklich geordnete Listen. Eigene Werte
und Vererbungszustände werden verschieden gespeichert.

**Codec-Entscheidung noch offen:** Empfehlung ist ein eigener validierter,
versionierter Daten-Codec, etwa JSON-Inhalt mit expliziter Schemaversion unter
der weiterverwendeten `.d2g`-Endung. Alternativ kann das bisherige eingeschränkte
Zuweisungsformat erweitert werden. Die Wahl folgt erst nach dem fachlichen
Schema; sie darf kein Ausführen von Projektinhalt erfordern. Eine neue
Formatversionsnummer wird erst für das tatsächlich vereinbarte Schema vergeben.

Übernahme bisheriger Projekte:

1. Versionen 1.1–1.5 weiterhin mit dem bestehenden sicheren Decoder lesen.
2. Zeichnung aufbauen und bestehende Zuordnung samt Reihenfolge wiederherstellen.
3. Aus jedem bisherigen Bearbeitungslayer Schritte und aus jedem bisherigen
   Shape eine Bearbeitungszuordnung erzeugen. Für einheitliche Layer entspricht
   die Anfangsstruktur dem Layerbaum; gemischte Werkzeuge/Arten benötigen die
   oben beschriebene Aufteilung ohne Änderung der Ausgabereihenfolge. IDs
   einmal vergeben und anschließend speichern.
4. Werkzeug-Overrides, Tiefen, Einheiten, Startpunkte, Richtung, Leads,
   Messerparameter, deaktivierte Einträge und Custom-G-Code erhalten.
5. BREAKS:-/IGNORE:-Semantik ausdrücklich übernehmen. Sonderlayer nicht als
   normale spanende Arbeitsgänge exportieren.
6. Aufgelöste Werte, Pläne und relevante G-Code-Ausgaben vor/nach Migration
   vergleichen. Nicht eindeutig zuordenbare Altobjekte melden und erhalten.
7. Vorschlag: bei der ersten neuen Speicherung „Speichern unter“ verwenden;
   die Originaldatei nicht automatisch konvertieren/überschreiben.

Neue Projekte sind nicht automatisch rückwärts in alten Programmversionen
bearbeitbar. Ein verlustbehafteter Legacy-Export wäre ein eigener Auftrag;
freie Gruppen und Mehrfachreferenzen lassen sich nicht allgemein
verlustfrei auf das bisherige Layerformat abbilden.

## 9. Umsetzung in prüfbaren Etappen

Jede Etappe bekommt einen eigenen begrenzten Auftrag. Keine Etappe beginnt
mit einer noch offenen fachlichen Entscheidung, von der ihr Verhalten abhängt.

| Paket | Inhalt und hauptsächlich betroffene Bereiche | Abnahme / Voraussetzung |
| --- | --- | --- |
| P0 – Bedienvertrag, abgeschlossen | Regeln, Auswahl, Bearbeitungskonturen und Beispiele mit dem Nutzer abgestimmt. | [Planungsabschluss](../archive/toolpath-refactoring-completed.md#r3-r1b-plan); Implementierung und GUI-Abnahme folgen separat. |
| P1 – Parameter und Identitäten | Herkunft aller Parameter erfassen; IDs, Referenzen, Gruppen und Resolver im reinen Domain-Modell ergänzen. | Eigene/geerbte Werte eindeutig, keine Qt-/Adapterimporte; keine Verhaltensänderung im bestehenden Einstieg. |
| P2 – Gemeinsame Bearbeitungsgrundlage | Bestehende DrawingModel-/Shape-Daten über einen Adapter in Gruppen/Arbeitsgänge überführen. Pro Kontur zunächst ein Arbeitsgang; getrennte Start-/Richtungswerte. | Vorschau/Export benutzen denselben Resolver; bestehende positive Plan- und Golden-Verträge erhalten. |
| P3 – Persistenz und Reload | Neuen Codec, Altprojektmigration, IDs und Wiederzuordnung implementieren; GUI- und CLI-Projektwege anbinden. | Roundtrip und alte Versionen 1.1–1.5; fehlende/mehrdeutige Referenzen blockieren zuverlässig. |
| P4 – Dritter Tab | Bearbeitungsbaum hinzufügen, Auswahl/Canvas koppeln, Gruppenaktionen, Parameterdarstellung; bestehende Tabs gemäß D4 anbinden. | Datenmodell ist führend, kein zweiter UI-Zustand; DE/FR/RU und Qt5/Qt6. |
| P5 – R1b | Atomare Mehrfachverschiebung, Sortieren, Einfügemarkierungen und alternative Menüaktionen; Kopieren mit eigenständiger Identität gemäß D2/D15; verpflichtendes Undo/Redo gemäß D12. | Verschieben erhält IDs/Anzahl; bewusstes Kopieren erzeugt neue Bearbeitungs-IDs bei gleicher Originalgeometrie; Zielvererbung und Roundtrip stimmen. |
| P6 – Export und Optimierung | Bearbeitungsreihenfolge als verbindlichen Exportvertrag aktivieren; Gruppen-/G-Code-Grenzen, Werkzeuge und Routendarstellung anbinden. | Tatsächlicher G-Code folgt dem sichtbaren Baum; beide Optimierungsmodi bleiben erhalten; kompletter Exportabbruch bei Fehlern. |
| P7 – Stegregionen, später | Manuelle Regionen, Fang und Automatik separat abstimmen; nicht Teil der ersten nutzbaren R3/R1b-Version. Bestehende BREAKS:-Wirkung bereits in P2/P3/P6 erhalten. | Eigener Folgeauftrag mit Region ändern/löschen, Zuordnung, Pass-/Z-Wirkung und Roundtrip. |
| P8 – Integrierte Nutzerabnahme | Referenzprojekte gemeinsam durchgehen; Anleitung ergänzen und alte Übergangssynchronisierung entfernen. | Nachfolgende Matrix bestanden; Grenzen separat dokumentieren. |

P2/P3 sind die Grundlage des neuen Tabs, P4/P5 die erste sichtbare Bedienung.
P6 ist kein nachträglicher Versuch, die GUI zu spiegeln: Der gemeinsame Export-
Adapter wird schon ab P2 mitgeführt; P6 macht den neuen Baum zum verbindlichen
Einstieg und schließt dessen Sonderfälle ab. Vor Freigabe müssen P3–P6 gemeinsam
funktionieren. P7 ist gemäß Nutzerentscheidung aus dieser ersten Freigabe
ausgenommen; P8 prüft zunächst den Grundumfang einschließlich Kopieren. D15
definiert die Werteübernahme beim Kopieren. Manuelle Stege, Fang/Automatik und Teilkonturbedienung erhalten
eigene Folgepakete statt unbeabsichtigt in den Grundumfang zu wachsen.

## 10. Prüf- und Nutzerabnahmematrix

| Fall | Erwarteter Nachweis |
| --- | --- |
| Bestehendes DXF/Projekt laden | Entities/Layers erhalten; Anfangsgruppen und Operationen bilden den bisherigen Auftrag ab. |
| Mehrere Arbeitsgänge zwischen Gruppen verschieben | IDs/Anzahl/Geometrie gleich; Quell- und Ziellisten sowie Einfügeposition stimmen. |
| Werkzeug aus Schritt, Tiefe explizit | Gemäß D8 wirkt das Zielwerkzeug; eigene Tiefe bleibt. Änderungen sind vor/nach dem Verschieben erkennbar. |
| Bewusst in weiteren Schritt kopieren (D2) | Neue Bearbeitungs-ID, gleiche Geometrie-ID; Startpunkt/Richtung/Parameter später unabhängig änderbar; Löschen einer Zuordnung erhält die anderen. |
| Originalkontur mit mehreren Bearbeitungen auswählen | Alle Zuordnungen auffindbar; aktiver Kontext eindeutig; kein unbeabsichtigtes gemeinsames Editieren gemäß D14. |
| Alten Zahlenwert migrieren | Kein Erraten der Herkunft; bisheriges Ergebnis bleibt erhalten. |
| Globale Werkzeugtabelle nach Speicherung ändern | Projekt verwendet weiter gespeicherte Werte; erst bewusste Aktualisierung ändert die betroffenen Schritte gemeinsam und lässt sich rückgängig machen. |
| Gültige Aktion mit geänderten wirksamen Werten | Direkte Ausführung ohne zusätzlichen Bestätigungsdialog; verständliche Änderungsanzeige und Undo verfügbar. |
| Verschieben abbrechen, ungültiger Drop | Kein Teilzustand; echte Qt5-/Qt6-Ereignisse zusätzlich zu Unit-Tests verwenden. |
| Bearbeitungsart wechseln, gemischte Auswahl mit unpassender Kontur | Gesamte Aktion gemäß D10 vor Änderung ablehnen; betroffene Konturen nennen; Quell-/Ziellisten und Undo unverändert. |
| Mehrfachaktion rückgängig/wiederholen | Ein gemeinsamer Undo-Schritt stellt Mitgliedschaft, Reihenfolge, IDs und Parameterherkunft wieder her; Redo erzeugt keine zusätzlichen Kopien. |
| Neue Kontur beim erneuten DXF-Import | Sichtbar und ausdrücklich unzugeordnet; bestehende Verknüpfungen erhalten; keine automatische Erweiterung des Exportauftrags. |
| Arbeitsgangrichtung/Start ändern | Nur Bearbeitung ändert sich; Originalkontur bleibt stabil. Modelltest mit zwei Referenzen bereitet die spätere Mehrfachbedienung vor. |
| Aktivierung und Sichtbarkeit ändern | Exportmenge und Zeichnungsanzeige verhalten sich gemäß abgestimmten Checkbox-Verträgen. |
| Baum sortieren/optimieren | Sichtbare Exportreihenfolge stimmt; Gruppen bleiben fest, beide relativen Optimierungsmodi erhalten. |
| Custom-G-Code und Werkzeugwechsel | G-Code-Position/Rückkehrvertrag stimmen; keine unzulässige Optimierung über Ablaufgrenzen. |
| Speichern, Schließen, Laden | Identitäten, Gruppen, Reihenfolge, Overrides, Stege und Herkunft unverändert. |
| DXF-Transformation oder geänderte Quelle | Eindeutige Referenzen erhalten; Mehrdeutigkeit/Fehlen sichtbar, kein falscher automatischer Ersatz. |
| Pocket-/Drill-/Maschinenkonflikt | A1/B1/B2-Werterhalt und Diagnose; vorhandene Zieldatei bleibt bei Exportfehler erhalten, stdout leer. |
| Stegregion ändern (Folgepaket P7) | Tatsächliche kompensierte Bahn, Z-Höhe und Passauswahl stimmen in Plan, 2D/3D und G-Code; im Grundumfang vorhandene BREAKS:-Semantik unverändert. |
| GUI/CLI dasselbe Projekt exportieren | Gleiche Arbeitsgänge, Parameterauflösung und Reihenfolge; keine zweite CLI-Planung. |

Pro Etappe fokussierte lokale Prüfungen einmal ausführen; keine vollständige
Suite oder Debian-/MSI-Läufe ohne gesonderten Auftrag. Quellcode-/Testcommits
laufen über den verpflichtenden Fast-Hook; volle CI auf Develop/PR gemäß
Repositoryregeln. Übersetzungspflege ist Teil jeder GUI-Etappe. Manuelle
GPU-, Paket-/Debian- und reale Maschinenabnahme bleiben eigene Aufträge.

## 11. Nächster Schritt nach dem freigegebenen Plan

Zunächst den abgestimmten Plan committen, pushen und den aktuellen
Softwarestand als Develop-Prerelease veröffentlichen. Dieser Release enthält
noch keine R3-/R1b-Implementierung. Danach beginnt die Umsetzung mit P1:
Parameterherkunft, Identitäten und reines Domain-Modell. Bestehende
Arbeitsabläufe bleiben in dieser ersten Scheibe unverändert.

## Quellen und Abgrenzung

- [R3-Anforderungen](open-task-details.md#r3), einschließlich des Nutzerwunsches
  zu manuell angelegten Stegen vom 04.11.2026.
- [R1b-Anforderungen](open-task-details.md#r1b) und [Teilkontur-Erweiterung](open-task-details.md#teilkonturen).
- [Architekturverträge](../architecture.md) und [A1-Abschluss](../archive/toolpath-refactoring-completed.md#a1-complete).
- Die Quellen in Abschnitt 2 wurden für diesen Entwurf im aktuellen Checkout
  gelesen. Bestehende Tests wurden eingeordnet, für diese Planung nicht erneut
  ausgeführt. Noch keine feste Zeit-/Aufwandszusage; die Hauptaufwände liegen
  in Parameterherkunft, Reload und Persistenz.
