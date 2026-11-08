# R3 und R1b: gemeinsamer Umsetzungsplan

Stand: **07.11.2026**. **Plan vom Nutzer am 06.11.2026 bestätigt.**
Commit, Push und Develop-Release vor der Umsetzung sind abgeschlossen.
P1–P6 sind implementiert; [P1–P3-Nachweis](../archive/toolpath-refactoring-completed.md#r3-r1b-p1-p3)
und [P4–P6-Nachweis](../archive/toolpath-refactoring-completed.md#r3-r1b-p4-p6).
P8 bleibt die gemeinsame Nutzerabnahme; P7 ist separat zurückgestellt.
Bestätigte Fachregeln und technische Umsetzungsvorschläge sind unterschieden.
[Planungsabschluss](../archive/toolpath-refactoring-completed.md#r3-r1b-plan).

**Arbeitszweig seit 07.11.2026:** `maschining-project`.
Der lokale P1–P3-Commit `5415018` und der fortgef?hrte R3/R1b-Stand
liegen auf diesem Zweig. Weitere Arbeiten erfolgen dort. `develop` und
GitHub-`develop` bleiben auf `4346709`; die spätere Integration ist ein
separater Auftrag. Der neue Zweig ist bislang lokal, ohne Push oder Release.

## 1. Ziel und bereits getroffene Entscheidungen

R3 trennt die importierte Zeichnung von ihrer Bearbeitung. R1b wird als
Verschieben von Konturzuordnungen zwischen Bearbeitungsschritten umgesetzt.
Im bisherigen Entwurf als Bearbeitungsgruppe bezeichnet, ist ein solcher
Schritt ein benannter Container wie Schruppen, Schlichten oder Bohren. Die
Einträge darin sind eigenständige Bearbeitungen mit Geometriereferenz.
Ein Gruppenwechsel verändert nicht den ursprünglichen DXF-Layer.

| ID | Entscheidung | Status |
| --- | --- | --- |
| D1 | Ursprünglich drei Tabs mit getrennten Originalansichten. Die spätere gemeinsame Geometrieansicht nach D24 ersetzt nur diese Anordnung; Auswahlmodelle und Originalstruktur bleiben erhalten. | Durch D24 präzisiert |
| D2 | Eine Originalkontur kann mit mehreren Bearbeitungsschritten verknüpft sein. Kopieren erzeugt eine weitere Bearbeitungszuordnung, keine zweite Originalkontur. | Bestätigt; Verschieben und Kopieren gehören bereits zur ersten nutzbaren Version |
| D3 | Beim Verschieben bleiben eigene Tiefen, Vorschübe und Leads erhalten; geerbte Werte stammen aus dem Zielschritt. Werkzeug folgt verbindlich dem Ziel gemäß D8. | Vom Nutzer bestätigt |
| D4 | Entities und Layers dienen der Geometrieauswahl. Layers zeigt dauerhaft die Originalkonturen und liefert die Ausgangsstruktur des Bearbeitungsbaums. Kein Verschieben zwischen DXF-Layern; Bearbeitungsänderungen brauchen einen aktiven Bearbeitungskontext. | Vom Nutzer präzisiert und bestätigt |
| D5 | Neue versionierte `.d2g`-Struktur; bisherige Versionen 1.1–1.5 weiter lesen, migrierte Dateien zunächst unter neuem Namen speichern. | Vom Nutzer bestätigt |
| D6 | Erste nutzbare Version umfasst Gruppen, Verschieben und Kopieren gemäß D2. Manuelle Stegregionen, Automatik und Fang folgen später; vorhandene BREAKS:-Funktion bleibt erhalten. | Vom Nutzer bestätigt |
| D8 | Jeder Bearbeitungsschritt hat genau ein Werkzeug. Verschieben übernimmt das Zielwerkzeug; alte eigene Werkzeugzuweisungen benötigen getrennte Schritte. | Vom Nutzer bestätigt |
| D14 | Geometrieauswahl zeigt alle Verknüpfungen. Bei Mehrfachverknüpfungen erst Bearbeitungen ausdrücklich im Baum/Canvas auswählen; eindeutig zugeordnete Originalkonturen sind direkt gemeinsam editierbar. Aktiver Kontext steuert Hervorhebung, Mehrfachauswahl aggregiert Parameter gemäß D36. | Vom Nutzer bestätigt; am 08.11.2026 präzisiert |
| D7 | Unklare alte Tiefen-/Vorschubwerte bei Migration als eigene Werte erhalten; bekannte Vererbungszustände bewahren. Später bewusst auf Schrittvorgaben umstellen. | Vom Nutzer bestätigt |
| D15 | Beim Kopieren eigene Tiefen/Vorschübe/Leads kopieren; geerbte Werte und Werkzeug aus dem Ziel übernehmen. Beide Bearbeitungen sind unabhängig änderbar. | Vom Nutzer bestätigt |
| D16 | Je Bearbeitungsschritt genau eine Bearbeitungsart und ein Werkzeug. Schruppen/Schlichten sind freie Namen; Art und Werkzeug werden ausdrücklich eingestellt. | Vom Nutzer bestätigt |
| D9 | Nach erneutem DXF-Import bleiben neue Konturen zunächst ohne Bearbeitungszuordnung; eindeutig wiedererkannte bestehende Verknüpfungen bleiben erhalten. | Vom Nutzer bestätigt |
| D10 | Unpassende Geometrie beim Verschieben/Kopieren vorab erklären und die gesamte Aktion ohne Teiländerung ablehnen. | Vom Nutzer bestätigt |
| D12 | Rückgängig/Wiederholen für die neuen Bearbeitungsaktionen gehört bereits zur ersten Version. | Vom Nutzer bestätigt |
| D17 | Werkzeugdaten und Bearbeitungsvorgaben im Projekt erhalten; Änderungen externer Profile erst durch eine ausdrückliche Aktualisierung übernehmen. | Vom Nutzer bestätigt |
| D19 | Unterschiedliche Werkzeugdefinitionen derselben Ausgabenummer weiterhin erlauben; keine Exportsperre allein wegen unterschiedlicher Durchmesser. Definitionen erhalten eigene Projekt-IDs. | Vom Nutzer am 07.11.2026 bestätigt |
| D20 | Exportcheckboxen ausschließlich in Bearbeitung; Entities/Layers behalten die Originalauswahl. Deaktivierte Zeichnungspfade berücksichtigen die verknüpften Bearbeitungen. | Vom Nutzer am 07.11.2026 bestätigt |
| D21 | Werkzeugwechsel weiterhin nur bei anderer Ausgabenummer. Unterschiedliche Definitionen/Drehzahlen aufeinanderfolgender Schritte derselben Nummer erzeugen keinen erneuten Profilblock und keine zusätzliche Drehzahlausgabe. | Vom Nutzer am 07.11.2026 bestätigt |
| D22 | Die vertrauten Werkzeug-/Konturfelder nach Bearbeitung verschieben und am neuen Modell weiterverwenden; keine Ersatz-Parametertabelle. Kette/Stift zeigen geerbte/eigene Werte, Tooltips erklären die Herkunft, ein Symbolmenü entfernt eigene Konturwerte gemäß D26. | Vom Nutzer am 07.11.2026 beauftragt |
| D23 | Rechtsklick in Layers öffnet zuerst ein Kontextmenü an der Klickposition. Zugehörige bestehende Schritte darin anzeigen und auswählbar machen; den Erstellungsdialog erst über eine ausdrückliche Menüaktion öffnen. | Nach späterer Nutzerfreigabe implementiert; Nachweis R3-UI |
| D24 | Zwei Tabs: Geometrie mit Entities oben und Layers unten, getrennt einklappbar und vertikal verstellbar; Bearbeitung als zweiter Tab. Originalbäume behalten Auswahl und Struktur. Sortierpfeile nur in Bearbeitung, Ein-/Ausklappen rechts an jedem Baum. | Vom Nutzer bestätigt und zur Umsetzung freigegeben |
| D25 | Toolbar-Erstellen behält seinen Dialog: ohne Konturen leer; mit Auswahl Verschieben vorbelegt, alternativ Kopieren oder Auswahl nicht verwenden. Kontextmenüs verwenden stattdessen den gemeinsamen Zuordnungsdialog gemäß D37. | Vom Nutzer bestätigt; am 08.11.2026 präzisiert |
| D26 | Bearbeitungswerkzeug und Konturparameter verwenden gleiche Gruppen-/Einheitsspalten und kompakte Wertebereiche. Jeder Wert behält sein Symbolmenü. Kette/Stift zeigen Herkunft; Rücksetzen ist eine Menüaktion. Gekürzte Zahlenanzeige erhält unveränderte Modellwerte vollständig. | Vom Nutzer bestätigt; kompakte Paare am 08.11.2026 ergänzt |
| D27 | Werkzeugleiste oben: Erstellen, Sortieren, Verlauf, Baumansicht durch Trennlinien gruppiert. Rückgängig/Wiederherstellen ohne verfügbare Aktion deaktiviert. Entfernen/Richtung im Baumkontextmenü; Schritt bearbeiten per Doppelklick/F2, Vorgaben durch Auswahl. Nullpunkt nur im Canvas gemäß D31; keine untere Buttonleiste. | Vom Nutzer bestätigt; am 08.11.2026 präzisiert |
| D28 | Anzeige standardmäßig mm mit 3, inch mit 5 Nachkommastellen; Längen folgen der Einheit; Vorschübe und Winkel jeweils mit eigener Konfiguration und Standard 1, ganze Zahlen bleiben ganzzahlig. Über Config-Menü einstellbar; Anzeige darf Eingabe, gespeicherte und berechnete Genauigkeit nicht reduzieren. | Vom Nutzer bestätigt und implementiert |
| D29 | Zwei Werte je Zeile in vier Group Boxes: Z-Werte, Vorschübe, Lead in/out und Offset. Kurze Labels mit direkt angehängter Einheit; Zahlenfelder ungefähr acht Zeichen, Herkunftssymbol direkt am Feld. Werkzeugauswahl/Drehzahl in gemeinsamer Kopfzeile. Leads/Überfahrt ändern nur Bearbeitungswerte, keinen Werkzeugdatensatz. Maschinenfilter und Altwerterhalt bleiben. | Vom Nutzer beauftragt und implementiert; am 08.11.2026 präzisiert |
| D30 | Kontextmenü für ausgewählte Bearbeitungskonturen bietet Kontur, Bohren, Taschenfräsen sowie G40/G41/G42 wieder an, im Bearbeitungsbaum und Canvas. Artwechsel nutzt zuerst passende bestehende Schritte gemäß D38, sonst neue mit Quellwerkzeug/-vorgaben. Keine Änderung anderer Zuordnungen oder Originalgeometrie; atomar mit Undo. | Implementiert; Wiederverwendung gemäß späterer Nutzerentscheidung D38 ergänzt |
| D31 | Der beanstandete „Startpunkt“ meint den Werkstücknullpunkt. Kein Startpunkt-Eintrag im Kontur-/Bearbeitungsbaum-Menü; „Werkstücknullpunkt hierher …“ ausschließlich im Canvas, unabhängig von der Auswahl. Der Bearbeitungsstart einer Kontur ist ein anderer Wert. | Vom Nutzer klargestellt und umgesetzt |
| D32 | Canvas-Kontextmenü möglichst wie bisher: Nullpunkt; Auswahl umkehren/aus-/einschalten; Richtung und Konturstart; passende Bearbeitungsarten/Kompensation. Gewohnte Reihenfolge und Trennlinien erhalten. „Bearbeitung zuordnen …“ gemäß D37 getrennt am Ende. Originalgeometrie unverändert; Aktionen auf aktive Zuordnungen mit Undo. | Nutzerauftrag anhand Vorher-/Nachher-Screenshots; implementiert und gemäß D37 präzisiert |
| D33 | Nur der Trenner zwischen Baum und gesamtem Eingabebereich bleibt. Inneren Werkzeug-/Konturtrenner und deren Klappbereiche entfernen; ein gemeinsamer Scrollbereich für Kopfzeile und vier Group Boxes. Inhalte oben, Leerraum darunter. Keine Änderung an Modell oder History. | Vom Nutzer beauftragt und implementiert; am 08.11.2026 präzisiert |
| D34 | Originalauswahl zeigt alle zugehörigen tatsächlichen Bearbeitungspläne mit Leads, Start/Ende und Tiefen. Bestehende Bewegungsfarben unverändert; aktive/überfahrene Bearbeitungen nur dicker. Direkte Canvas-Auswahl über Pfad/Label, Strg-Mehrfachauswahl und Trefferwahl bei Überlagerung; Teilauswahl punktiert das Original mit k/n. Kein künstlicher Geometrieversatz, manuelle Exportrouten unabhängig. | Vom Nutzer beauftragt und implementiert |
| D35 | Beim Hauptfenster-Skalieren bleiben linke Breite und Meldungshöhe konstant; Canvas wächst, innerhalb Bearbeitung der Baum. Manuelle Trennergrößen und Geometrie-Klappzustände über Neustarts speichern; alte Parameter-Trennerzustände ignorieren. Mindestfenster schützt Canvas. | Vom Nutzer beauftragt und implementiert; am 08.11.2026 präzisiert |
| D36 | Gemeinsame Parameterbearbeitung: gleich/geerbt grau, gleich mit eigenen Werten normal, verschieden als editierbares „Unterschiedlich“. Herkunft aus gespeichertem Vertrag, nicht Zahlenvergleich. Nur nicht gemeinsam anwendbare Felder sperren. Änderung/Rücksetzen für ganze Auswahl atomar, unveränderte Bestätigungen und Platzhalter schreiben nichts. Rückzug/Sicherheit bleiben Schrittwerte mit Wirkungshinweis. | Vom Nutzer beauftragt und implementiert |
| D37 | Variante 2: Gemeinsamer Dialog „Bearbeitung zuordnen …“ aus Canvas und Bäumen. Aktion Kopieren/Verschieben, Ziel vorhandener/neuer Schritt; alle Felder sichtbar, nur passende Eingaben aktiv gemäß D39. Einzelne Kontextaktionen Kopieren/Verschieben/Erstellen ersetzen. Schritt bearbeiten und Vorgaben bearbeiten aus Menüs entfernen; Doppelklick/F2 und Auswahl bleiben. Profilaktualisierung/G-Code unter Erweitert. Atomar mit Undo, explizite Referenzauswahl und Zielvererbung erhalten. | Vom Nutzer gewählt und zur Umsetzung freigegeben; implementiert |
| D38 | Vor automatischer Neuanlage bei Art-/Konturwerkzeugwechsel vorhandene Schritte prüfen: Zielart, komplette Werkzeugdefinition und gespeicherte Schrittvorgaben müssen übereinstimmen; Namen allein unterscheiden nicht. Ein Treffer wird verwendet, bei mehreren Ziel auswählen. Abbruch ohne Teiländerung, bestehende Zielwerte unverändert, Zuordnungen hinten anfügen. Explizit neuer Schritt bleibt neu. | Vom Nutzer beauftragt; bei mehreren Treffern ausdrücklich Zielauswahl gewählt; implementiert |
| D39 | Zuordnungsdialog mit fester Größe und festen Feldpositionen. Alle Eingaben sichtbar lassen, nur nach vorhandenem/neuem Ziel aktivieren. Aktion einmal beim Öffnen vorbelegen; Zielwechsel ändert keine Werte, auch keine unberührte Vorbelegung. Name, Art, Werkzeug und vorhandenes Ziel beim Hin-/Herwechsel erhalten. | Vom Nutzer bestätigt und beauftragt; implementiert |
| D40 | Variante 1: Importierte BREAKS-Regionen als besondere Haltesteg-Gruppe bei tatsächlich betroffenen Schritten anzeigen. Keine normale Kontur-/Werkzeug-/Exportreihenfolgeauswahl. Eigener Stegmodus für Regionseigenschaften, Aktivierung und Entfernen mit Undo. Globale Wirkung und bestehender Speichervertrag bleiben erhalten. Regionen und wirksame Stegabschnitte unterscheiden; manuelles Zeichnen und lokale Zuordnungen später in P7. | Vom Nutzer bestätigt und beauftragt; implementiert |
| D41 | Einheitlicher Stegbezug bei interner und maschinenseitiger Radiuskorrektur: BREAKS gegen die Originalkontur schneiden. Bei interner Korrektur diese Konturstellen auf die korrespondierenden Stellen der Werkzeugmittelpunktbahn übertragen; bei Maschinenkorrektur dieselben Originalkonturstellen programmieren. Keine tangentiale Erweiterung um den Werkzeugradius. Nicht eindeutig übertragbare Stege dort vollständig auslassen und warnen, Export zulassen. Eckübergreifende Stege halten die gesamte Offsetverbindung auf Steghöhe. | Vom Nutzer beauftragt und Sonderfälle entschieden; implementiert und lokal geprüft, fachliche Abnahme P8 offen |
| D18 | Gültige Verschiebe-/Kopieraktionen direkt ausführen, wirksame Änderungen in der zentralen Meldungsausgabe anzeigen und Undo über den Buttonzustand anbieten; keine zusätzliche Bestätigungsabfrage oder Meldungsfläche im Bearbeitungstab. | Vom Nutzer bestätigt; Anzeigeort am 08.11.2026 präzisiert |
| D13 | Bei der ersten Übernahme entspricht die Bearbeitungsstruktur dem Layerbaum; spätere Änderungen bleiben ausschließlich in Bearbeitung. | Bestätigt; Werkzeugtrennung nach D8 erfordert bei gemischten Alt-Layern getrennte Schritte |

Ein eigener Drehzahlblock bei gleicher Werkzeugnummer ist als spätere,
separate Erweiterung [PP1](../todo.md#pp1) vorgemerkt (Nutzeranregung vom
07.11.2026). D21 bleibt für den aktuellen Umfang gültig.

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
Werkzeugtabelle, auf die die Schritte über Definitions-IDs verweisen.
Gemäß D19 dürfen verschiedene Definitionen dieselbe Ausgabenummer tragen,
auch mit unterschiedlichen Durchmessern. Nur Schritte mit derselben
Definitions-ID teilen ihre Werkzeugdaten. Eine bewusste Aktualisierung zeigt alle betroffenen Schritte und
übernimmt die Werkzeugdefinition gemeinsam. Eigene Bearbeitungswerte werden
dabei nicht zu geerbten Werten umgedeutet oder still zurückgesetzt.

„Vorgaben aktualisieren“ ist eine ausdrückliche Aktion mit nachvollziehbaren
Änderungen und Undo. Fehlt das ursprüngliche Werkzeug inzwischen in der
globalen Tabelle, bleiben seine gespeicherten Projektdaten erhalten; kein
automatischer Ersatz durch Werkzeug 1. Diese Regel betrifft Bearbeitungs-
und Werkzeugvorgaben, nicht allgemeine UI-Einstellungen wie Farben/Layout.
Die Datenfelder und Herkunftsregeln sind in der
[P1–P3-Zuordnungstabelle](../documentation-notes/machining-project-format.md) festgehalten.

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
Eine aktive Bearbeitung bestimmt die hervorgehobene Vorschau. Parameter folgen
der vollständigen ausdrücklich gewählten Bearbeitungsauswahl gemäß D36.
Eindeutige Originalzuordnungen sind direkt gemeinsam editierbar. Besitzt eine
ausgewählte Originalkontur mehrere Referenzen, bleibt der Editor einschließlich
Werkzeugwahl gesperrt, bis die gewünschten Bearbeitungen im Baum/Canvas
ausdrücklich gewählt sind. Keine willkürliche Aktivierung oder automatische
Änderung aller verknüpften Zuordnungen durch die Originalauswahl.

Zeichnungssichtbarkeit, Auswahl und Exportaktivierung sind getrennte Zustände.
Die bisherigen Checkboxen müssen einzeln zugeordnet und erklärt werden;
sie dürfen nicht im Zuge des Umbaus unbemerkt ihre Wirkung wechseln.

<a id="r3-menu"></a>

### R3-MENU – Kontextmenü der Originalbäume, implementiert

**Stand 07.11.2026: umgesetzt nach späterer Nutzerfreigabe.**
Die anfängliche Anweisung „nur planen“ wurde durch den Umsetzungsauftrag
abgelöst. Der Vertrag gilt für Layers und Entities.
[Abschluss und Prüfgrenzen](../archive/toolpath-refactoring-completed.md#r3-ui).

Bedienvertrag gemäß D23 und D25:


- Rechtsklick auf Layer oder Kontur öffnet ein normales Kontextmenü direkt
  an der Klickposition. Die Position wird aus dem tatsächlichen Baum-
  Viewport in Bildschirmkoordinaten umgerechnet.
- Das angeklickte Objekt bestimmt den Kontext. Gehört es bereits zur
  Mehrfachauswahl, bleibt diese erhalten; andernfalls wird die angeklickte
  Kontur beziehungsweise der angeklickte Layer zur Auswahlbasis.
- Ein Bereich „Zugehörige Bearbeitungsschritte“ zeigt die bereits mit diesen
  Originalkonturen verknüpften Schritte in Bearbeitungsreihenfolge, mit Name,
  Bearbeitungsart und Werkzeug. Schritte werden anhand ihrer Identität
  zusammengefasst, nicht nur anhand gleicher Namen oder Werkzeugnummern.
- Auswahl eines bestehenden Schritts springt im Bearbeitungstab zu dessen
  passenden Einträgen. Eine eindeutige Bearbeitung kann aktiviert werden;
  bei mehreren passenden Einträgen bleibt die Wahl der aktiven Kontur gemäß
  D14 ausdrücklich. Die Navigation erzeugt oder verschiebt keine Zuordnung.
- „Bearbeitungsschritt erstellen …“ öffnet den vorhandenen
  Dialog erst nach ausdrücklicher Auswahl. Bei Aufruf aus diesem Menü soll
  der Dialog nahe der Klickposition und innerhalb der verfügbaren
  Bildschirmfläche erscheinen. Seine bisherigen Verschiebe-/Zusatzbearbeitungs-
  Optionen bleiben erhalten.
- Menü schließen oder abbrechen ändert weder Bearbeitungsdaten noch
  Reihenfolge oder Undo-Verlauf. Bei fehlender Verknüpfung ist dies im Menü
  erkennbar; ein leerer Baumbereich erzeugt keinen überraschenden Dialog.

Automatisierte Qt5-/Qt6-Prüfungen decken Popup-Position, Navigation,
Abbruch, alle Zuordnungsarten, ganze Layer und beide Originalbäume ab.
Die tatsächliche Wahrnehmung von Größe und Position bei verschiedenen
Monitoren bleibt Teil der [Nutzerabnahme](#r3-ui-user-check).

<a id="r3-ui-user-check"></a>

### R3-UI – konkrete Aufgaben für die Nutzerabnahme

1. Eine eigene mehrlagige DXF öffnen. Im Tab Geometrie beide Gruppen einzeln
   ein-/ausblenden, Trennlinie verschieben und beide Bäume ein-/ausklappen.
   Erwartet: Auswahl bleibt gekoppelt; keine Layers-Sortierpfeile.
2. Einen ganzen Layer rechts anklicken. Vorhandene Schritte im Menü anspringen;
   dann „Bearbeitung zuordnen …“ öffnen. In vorhandenen Schritt kopieren und
   verschieben; neuen Schritt mit Name/Art/Werkzeug erstellen. Bei vorhandenem
   Ziel sind diese drei Felder sichtbar, aber gesperrt. Mehrfach umschalten:
   Größe, Feldpositionen, Aktion und alle Eingaben bleiben erhalten.
   Toolbar-Erstellen separat mit leerem
   Schritt prüfen. Erwartet: Original-Layer bleiben unverändert, ein Undo pro
   Aktion, Abbruch ändert nichts. Schritt-Doppelklick und Auswahl prüfen.
3. Eine Konturbearbeitung wählen. Werkzeug-/Konturfelder, Einheiten und
   Symbolmenüs bei üblicher Fensterbreite prüfen. Eine Tiefe ändern und über
   das Symbolmenü auf Schrittvorgabe zurücksetzen. Erwartet: bündige Spalten,
   verständliche Herkunft und kein ungewolltes Überschreiben eigener Werte.
4. Zwei Bearbeitungen umsortieren, Rückgängig und Wiederherstellen benutzen;
   Export-/Optimierungscheckboxen betätigen. Erwartet: Baum, Vorschau und
   exportierte Reihenfolge passen zusammen. Nicht verfügbare Aktionen sind grau.
5. Anzeige in mm/inch auf 3/5 Stellen prüfen; unter Konfiguration die
   Zahlenanzeige ändern und übernehmen. Einen Wert mit mehr Stellen eingeben,
   Feld verlassen und erneut aktivieren. Erwartet: gerundete Anzeige, volle
   Eingabe beim Bearbeiten, unveränderte Werte durch bloßes Bestätigen.
6. Linken Bereich vergrößern/verkleinern. Erwartet: beide Formulare skalieren
   bündig, Einheiten gleich ausgerichtet, Symbolknöpfe bleiben sichtbar und
   gleich breit; nötigenfalls mehrzeilige Beschriftungen.
7. Eine Kreis-Bearbeitung rechts anklicken und Bohren wählen. Erwartet:
   eigener neuer Schritt mit gleichem Werkzeug, G40 und gleicher Konturreferenz;
   andere Zuordnungen bleiben erhalten. Mit Undo zurücknehmen. Für eine
   geschlossene Fräskontur mit interner Kompensation Taschenfräsen sowie
   G40/G41/G42 prüfen, auch im Canvas bei ausdrücklich aktivierter Zuordnung.
8. Canvas-Menü mit dem bisherigen Ablauf vergleichen: Nullpunkt oben,
   Auswahlaktionen und Richtung/Konturstart in getrennten Gruppen,
   Bearbeitungsarten/Kompensation darunter, Zuordnen getrennt am Ende.
   Erwartet: gewohnte Beschriftungen/Trennlinien; Richtungs-/Startänderungen
   betreffen nur aktive Zuordnungen und schalten manuelle Exportrouten nicht ein.
9. Den Trenner zwischen Baum und gesamtem Eingabebereich ziehen. Erwartet:
   vier Group Boxes (Z-Werte, Vorschübe, Lead in/out, Offset), zwei Werte je
   Zeile, kurze Beschriftung mit Einheit und Herkunftssymbol direkt am Feld.
   Ein gemeinsamer Scrollbereich, kein innerer Trenner und keine separaten
   Werkzeug-/Kontur-Klappbereiche. Keine Parameter-/History-Änderung durch Ziehen.
10. Projekt unter neuem Namen speichern und öffnen. Erwartet: Zuordnungen,
   Reihenfolge und Werte bleiben erhalten. Rückmeldung mit Bildschirmauflösung,
   Skalierung und betroffener Ansicht, falls Beschriftungen abgeschnitten sind.
11. Eine Originalkontur mit zwei Bearbeitungen wählen: beide Vorschauen mit
    Leads/Start/Ende sehen, einen Pfad oder sein Label aktivieren und per Strg
    erweitern. Überlagerte Treffer auswählen beziehungsweise abbrechen.
    Erwartet: richtige aktive Parameter, Teilauswahl gepunktet mit k/n,
    unveränderte Farben und keine unbestellte Exportroute. Zoomen und schieben:
    G40 ohne Zusatz-Offset bleibt deckungsgleich, Kompensation bleibt fachlich.
12. Fenster vergrößern und neu starten: linke Breite, Meldungshöhe, manuelle
    Trenner und Klappzustände bleiben erhalten. Werte stehen auch breit nur
    paarweise nebeneinander; Lead-/Überfahrtwerte im Konturbereich, Messerparameter
    nur bei Dragknife. Ausgeblendete Zeilen hinterlassen keine Beschriftungen.

Das ist P8-Nutzerabnahme; keine Paket-, Linux-/Debian- oder Maschinenabnahme.

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

**Umgesetzte Migrationsregel P1–P3:** Ein alter Layer kann mehrere eigene
Shape-Werkzeuge und Bearbeitungsarten enthalten. Strikte Trennung nach Tool
und Art und gleichzeitig exakt identischer Anfangsbaum sind dafür nicht
ohne Ausnahme erfüllbar. Umsetzung gemäß
den bestätigten Regeln D8/D16: im Bearbeitungsbaum getrennte, nach
Werkzeug und Bearbeitungsart benannte Schritte anlegen und die Ausnahme anzeigen; Original-Layers unverändert
lassen. Dabei zusammenhängende Werkzeugabschnitte erhalten, damit etwa die
Reihenfolge T2 → T4 → T2 nicht zu T2 → T2 → T4 umsortiert wird. Diese Übernahme
ist in P1–P3 umgesetzt; Werkzeug/Art stehen in eigenen Spalten des neuen Baums.

**Sonderlayer:** IGNORE:-, BREAKS:- und andere Importkonventionen werden beim
Import ausgewertet; sie sind keine frei austauschbaren Bearbeitungsgruppen.
Break-Regionen und G-Code-Einträge benötigen eigene zulässige Ziele und dürfen
nicht als normale Kontur in einen Fräs-/Bohrvorgang verwandelt werden.

**Manuelle Haltestege: gemäß D6 ausdrücklich späteres Folgepaket.**
Bestehende BREAKS:-Layer, Z-Werte und Passauswahl werden schon in der
Grundversion unverändert übernommen. Gemäß D40 erscheinen sie jetzt als
Haltesteg-Gruppe unter den tatsächlich betroffenen Schritten, mit derselben
globalen Region an mehreren Stellen als Referenz. Zuordnung und Anzahl der
wirksamen Abschnitte stammen aus den geplanten Stegbewegungen; Tiefenpass-
Wiederholungen werden nicht mehrfach gezählt. Der Stegmodus erlaubt Höhe,
Vorschübe, Aktivierung und Entfernen mit Undo, ohne normale Konturauswahl.
Regionumrisse erscheinen nur dort in bestehendem Magenta; unwirksame Regionen
bleiben in einer eigenen Gruppe erreichbar. Für das spätere Paket ist vorgesehen:

**Einheitlicher Stegbezug gemäß D41, implementiert.** Die Steggrenzen werden
unabhängig von der Zuständigkeit der Radiuskorrektur auf der Originalkontur
bestimmt. Bei G40 sind dies direkt die programmierten Werkzeugmittelpunkte.
Bei intern berechnetem G41/G42 müssen die Konturstellen auf die zugehörige
Werkzeugmittelpunktbahn übertragen werden; der Schnitt der Region mit der
Offsetbahn darf dafür nicht erneut die Steggrenzen bestimmen. Bei maschinellem
G41/G42 werden die gleichen Originalkonturstellen ausgegeben, die Steuerung
übernimmt den Versatz. Die Region muss dadurch nicht zusätzlich die Offsetbahn
erreichen. Es gibt keine Vorverlegung des Anhebens oder Nachverlegung des
Absenkens aufgrund tangentialer Werkzeugberührung: Bezug bleibt der Mittelpunkt
an der korrespondierenden Bahnposition, keine garantierte Materialstegbreite.

Globale Zuordnung, Steg-Z und Passauswahl bleiben erhalten. Polygonale Regionen
werden auf Geraden/Bögen der Originalkontur ausgewertet; die Übertragung nutzt
Geradennormalen und konzentrische Bogenradien. Reicht ein Steg über eine Ecke,
bleibt die vollständige dazwischenliegende Offsetverbindung auf Steghöhe, ohne
kurzen Zustich an Teilstückgrenzen. Bögen bleiben auch im Stegabschnitt Bögen.
Bei verschwundenen, getrennten oder mehrdeutigen Gegenstücken wird der betroffene
zusammenhängende Steg für diese Bearbeitung vollständig ausgelassen und eine
Warnung ausgegeben. Das blockiert gemäß Nutzerentscheidung den Export nicht;
andere gültige Stege derselben Region bleiben erhalten. Eine Grenze genau auf
einem Eckpunkt mit mehreren möglichen Offsetpositionen ist ebenfalls mehrdeutig.
Nicht geschlossene oder nicht polygonale Regionen können nicht eindeutig
übertragen werden und werden mit Warnung ausgelassen.

Taschen-Randkonturen verwenden denselben Bezug. Die Rasterfüllung einer Tasche
besitzt keine 1:1-Entsprechung auf der Originalkontur und behält ihre bisherige
räumliche Regionsauswertung; Schleppmesser verwenden weiterhin ihre bisherige
Stegverarbeitung. Zeichnen/Fang/lokale Zuordnung bleiben P7. Vorschau und Export
verwenden denselben Plan. Abnahmefälle: Gerade/Bogen, G40/G41/G42, beide
Richtungen, Radien/Aufmaß, schmale/schräge Regionen, Eckverbindungen und
Warnungsfälle. [Lokaler Nachweis](../archive/toolpath-refactoring-completed.md#d41).
Das reale Korrekturverhalten einer Steuerung benötigt eine gesonderte Abnahme.

**Stegmodus-Symbol:** Nutzerwahl Variante 2, gestrichelte Region mit Stift.
Direkt rechts neben „Erstellen“ bei den linken Bearbeitungsaktionen anordnen;
Baumdarstellung/Ein- und Ausklappen bleiben rechts. Aktiver Modus bleibt am
gedrückten Button erkennbar, Tooltip und Umschaltverhalten bleiben erhalten.

**Weitere manuelle Funktionen:**

- Rechteck im Canvas anlegen, auswählen, verschieben, Größe/Z-Höhe ändern und
  löschen. Neue Regionen zunächst ausgewählten Arbeitsgängen zuordnen.
- Bestehende globale BREAKS:-Wirkung als ausdrückliche Kompatibilitätszuordnung
  übernehmen. Ein Gruppenwechsel verliert diese Zuordnung nicht.
- Absolute Steg-Z-Höhe und „Process breaks from“ erhalten; Regionen wirken
  auf die tatsächlich geplante Bahn, künftig mit Originalkonturbezug gemäß D41.
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
auswählen. Über „Bearbeitungsschritt erstellen …“ Name, Art und
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

### Skizze des Bearbeitungstabs

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

**Codec in P3 umgesetzt:** validiertes UTF-8-JSON mit expliziter Version 2.0
unter der weiterverwendeten `.d2g`-Endung. Der sichere Legacy-Leser bleibt
erhalten; Projektinhalt wird nicht ausgeführt.

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
| P1 – Parameter und Identitäten, implementiert | Herkunft, IDs, Referenzen, Gruppen und Resolver im reinen Domain-Modell. | [Nachweis](../archive/toolpath-refactoring-completed.md#r3-r1b-p1-p3); [Zuordnungstabelle](../documentation-notes/machining-project-format.md). |
| P2 – Gemeinsame Bearbeitungsgrundlage, implementiert | Legacy-Migration und getrennte Shape-/Layer-Projektionen mit eigenen Starts/Richtungen. | Gemeinsamer Resolver für Vorschau/Export; [Nachweis und Übergangsgrenzen](../archive/toolpath-refactoring-completed.md#r3-r1b-p1-p3). |
| P3 – Persistenz und Reload, implementiert | JSON 2.0, Altprojektmigration, IDs, Referenzbindung und GUI-/CLI-Projektwege. | Roundtrip, Versionen 1.1–1.5 und Exportabbruch bei ungelösten Referenzen [geprüft](../archive/toolpath-refactoring-completed.md#r3-r1b-p1-p3). |
| P4 – Bearbeitungstab, implementiert | Bearbeitungsbaum, Auswahl/Canvas, Gruppenaktionen, Parameterherkunft und Originalauswahl gemäß D20. | DE/FR/RU und echte Qt5-/Qt6-Abläufe [geprüft](../archive/toolpath-refactoring-completed.md#r3-r1b-p4-p6). |
| P5 – R1b, implementiert | Atomare Mehrfachaktionen, Drop-Markierung, Menü/Sortierung, neue IDs beim Kopieren sowie Undo/Redo. | Eigene Werte/Zielvererbung, Rückgängig und stabile Redo-IDs [geprüft](../archive/toolpath-refactoring-completed.md#r3-r1b-p4-p6). |
| P6 – Export und Optimierung, implementiert | Sichtbare Bearbeitungsreihenfolge, Schritt-/G-Code-Grenzen, Werkzeugnummernvertrag D21 und geplante Routenendpunkte. | GUI/CLI-Ausgabe, beide Optimierungsmodi und Fehlerabbruch [geprüft](../archive/toolpath-refactoring-completed.md#r3-r1b-p4-p6). |
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
| Importierte Stegregion ändern; neue Regionen später P7 | Globale Wirkung, Aktivierung, Entfernen und Undo prüfen; tatsächliche kompensierte Bahn, Z-Höhe und Passauswahl stimmen in Plan und G-Code. Manuelles Zeichnen/Fang/lokale Zuordnung bleiben P7; reale GPU-Abnahme getrennt. |
| GUI/CLI dasselbe Projekt exportieren | Gleiche Arbeitsgänge, Parameterauflösung und Reihenfolge; keine zweite CLI-Planung. |

Pro Etappe fokussierte lokale Prüfungen einmal ausführen; keine vollständige
Suite oder Debian-/MSI-Läufe ohne gesonderten Auftrag. Quellcode-/Testcommits
laufen über den verpflichtenden Fast-Hook; volle CI auf Develop/PR gemäß
Repositoryregeln. Übersetzungspflege ist Teil jeder GUI-Etappe. Manuelle
GPU-, Paket-/Debian- und reale Maschinenabnahme bleiben eigene Aufträge.

## 11. Nächster Schritt nach P1–P6

P1–P3 liefern das reine Modell, gemeinsame Bearbeitungsprojektionen und
JSON-Projekte der Version 2.0 einschließlich Legacy-Migration und Reload.
P4–P6 ergänzen den Bearbeitungstab, atomare Befehle mit Undo und die verbindliche
Reihenfolge bis zur Ausgabe. Die anschließende R3-UI-Korrektur einschließlich
[R3-MENU](#r3-menu) ist implementiert. P8 umfasst die gemeinsame Abnahme
mit den [konkreten UI-Aufgaben](#r3-ui-user-check): echte
Referenzprojekte bedienen, fachliche Rückmeldungen und aktuelle Screenshots
einpflegen und verbliebene Legacy-Kompatibilitätsaufrufer vor deren Entfernung
prüfen. Manuelle Stegregionen P7 sind weiterhin ein eigener Folgeauftrag.

<a id="r3-ui-followups"></a>

## 12. Vorgemerkte UI-Nacharbeiten und Untersuchung

Nutzerrückmeldungen vom 07.11.2026: Werkzeugmenü zunächst vorgemerkt und
anschließend ausdrücklich beauftragt; Leerraum weiterhin für später:

- **R3-TOOLS, umgesetzt und anschließend präzisiert:** Beide Werkzeugauswahlen
  verwenden eine gemeinsame Liste ohne Quellgruppen. Vollständig gleiche
  Definitionen erscheinen nur einmal; beim Projektladen werden entsprechende
  Projektidentitäten vereinheitlicht. Werkzeugnummer und sämtliche Werkzeugwerte
  nach Einheitenumrechnung müssen übereinstimmen; gerundete Anzeigegleichheit
  genügt nicht. Abweichende gespeicherte Werte bleiben als „Projektabweichung“
  neben der Tabellenvariante sichtbar. Beim bewussten Ersatz durch die passende
  Tabellenvariante werden gemäß Nutzerentscheidung alle Schritte mit genau
  dieser Projektdefinition gemeinsam geändert; andere Definitionen derselben
  Nummer bleiben erhalten. Auswahl einer anderen Werkzeugnummer ändert weiter
  nur den ausgewählten Schritt. Gemeinsamer Ersatz und Zusammenführung lassen
  sich atomar rückgängig machen. Projektwerte bleiben gespeichert und folgen
  späteren Tabellenänderungen nicht automatisch.
  Präzisierung zur Mehrfachauswahl vom 08.11.2026: Werkzeugwechsel dort betreffen
  ausschließlich die ausgewählten Bearbeitungszuordnungen. Vollständig
  ausgewählte Schritte behalten ihre Identität; für Teilauswahlen entstehen
  ohne kompatibles bestehendes Ziel neue Schritte gleicher Art/Vorgaben
  unmittelbar hinter der jeweiligen Quelle (Wiederverwendung/Zielwahl gemäß D38).
  Nicht ausgewählte Zuordnungen und andere Benutzer der Werkzeugdefinition
  bleiben unverändert. Ein gemeinsamer Undo-Schritt für den gesamten Wechsel.
  Ergänzende Korrektur: Auch eine einzeln ausgewählte Kontur verwendet diese
  Auswahlregel. Nur die ausdrücklich gewählte Schrittzeile beziehungsweise
  ein expliziter Profilaktualisierungsbefehl verwendet weiterhin den
  vereinbarten schritt-/definitionsweiten Ersatz.
  Ergänzende Nutzerentscheidung vom 08.11.2026: Vor dem Export müssen die
  tatsächlich verwendeten Werkzeugdefinitionen mit der aktuellen Tabelle
  übereinstimmen. Fehlende Nummern und abweichende Werte sperren den gesamten
  GUI-/CLI-Export vor der Ausgabe. Leere/deaktivierte, ignorierte und reine
  Steg-Schritte bleiben ausgenommen. Die Meldung nennt Nummer, Schritte und
  Projekt-/Tabellenwerte und schlägt Anlegen/Korrigieren in der Tabelle oder
  Zuweisen eines bestehenden Werkzeugs vor. Kein automatisches Anlegen und keine
  automatische Wertänderung beim Laden. Vorhandene Zieldateien bleiben erhalten,
  stdout bleibt bei Sperre leer. Historische Projektdateien haben dieselbe Sperre.
  [Ergebnis und Prüfnachweis](../archive/toolpath-refactoring-completed.md#r3-tools).
- **R3-ROWS:** Mit D29 erledigt: Kopfzeile enthält Werkzeugauswahl samt
  Durchmesser und Drehzahl. Versteckte Felder blenden vollständige Zeilen aus; natürliche
  Gruppenhöhe statt Auffüllen. [Nachweis](../archive/toolpath-refactoring-completed.md#r3-preview-layout).
- **R3-IGNORE:** Fokussierte Untersuchung bestätigt: `ignored` übernimmt die
  Ausschlusswirkung importierter `IGNORE:`-Layer. Die Materialisierung setzt
  deren Konturen unabhängig von `entry.enabled` auf deaktiviert und nimmt sie
  nicht in die Exportreihenfolge auf. Der Dialog bietet die Art jedoch auch
  für neue Schritte an. Ein leerer solcher Schritt ist zulässig; normale
  Konturen lassen sich wegen der Sonderlayer-Sperre nicht hineinverschieben.
  Die Exportcheckbox zeigt nur `entry.enabled` und kann deshalb eine Aktivierung
  suggerieren, die bei dieser Art keine Ausgabe bewirkt.
  Empfehlung zur Abstimmung: Art beim Anlegen normaler Schritte ausblenden,
  vorhandene Sonderzuordnungen und Dateikompatibilität erhalten und ihre
  Exportdarstellung eindeutig machen. Für normales vorübergehendes Ausschließen
  weiter die Exportcheckbox verwenden. Noch kein Umsetzungsauftrag für diese
  Empfehlung; insbesondere keine Umdeutung gespeicherter ignorierter Schritte.

Untersuchungsnachweis R3-IGNORE: lokaler Modell-/Befehlsversuch mit bestehender
Testfixture; leeres Anlegen erfolgreich, Verschieben einer normalen Kontur
atomar abgelehnt, `IGNORE:`-Import als `ignored` mit deaktivierter Projektion
und leerer Exportreihenfolge bestätigt. Dies ist keine neue GUI-/Paketabnahme.

## Quellen und Abgrenzung

- [R3-Anforderungen](open-task-details.md#r3), einschließlich des Nutzerwunsches
  zu manuell angelegten Stegen vom 04.11.2026.
- [R1b-Anforderungen](open-task-details.md#r1b) und [Teilkontur-Erweiterung](open-task-details.md#teilkonturen).
- [Architekturverträge](../architecture.md) und [A1-Abschluss](../archive/toolpath-refactoring-completed.md#a1-complete).
- Die Quellen in Abschnitt 2 wurden für diesen Entwurf im aktuellen Checkout
  gelesen. Bestehende Tests wurden eingeordnet, für diese Planung nicht erneut
  ausgeführt. Noch keine feste Zeit-/Aufwandszusage; die Hauptaufwände liegen
  in Parameterherkunft, Reload und Persistenz.
