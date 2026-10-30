# DXF2GCODE: Ziele, Aufgaben und Prüfergebnisse

Dieses Dokument vereint Zielarchitektur, Aufgaben, Entscheidungen und
Prüfergebnisse für Werkzeugweg, Bearbeitung, Konfiguration, GUI und
Versionsmetadaten. Die bisherigen separaten Werkzeugweg- und Metadatenpläne
sind hier zusammengeführt; ihre Vorgaben werden nur noch hier gepflegt.
Der semantische `ToolpathPlan`, der Exportpfad und die Vorschau-Anbindung
sind vorhanden. Die Planerzeugung verwendet reine Strategien und
explizite Eingaben. Vorbereitete Geometrie und Teile der Vorschau verwenden
weiterhin bestehende Algorithmen; deren vollständige Entkopplung bleibt offen.

## Orientierung

- [Zielarchitektur und verbindliche Regeln](#zielarchitektur-und-verbindliche-regeln)
- [Aufgabenauswahl und Prioritätsvorschlag](#neue-aufgaben-zur-auswahl--untersuchung-vom-30102026)
- [Umsetzungsstand des Werkzeugweg-Refactorings](#stand)
- [Arbeitsschritte: Refactoring und Funktions-/GUI-Aufgaben](#nächste-arbeitsschritte)
- [Abschnitt 13: Versionsmetadaten und offene Paketabnahme](#13-versions--und-build-metadaten)
- [Abschnitt 14: Importqualität und Layerfilter](#14-importqualität-und-layerfilter--weitere-wünsche-aus-ticket-157)
- [Zurückgestellte Teilkontur-Erweiterung](#zurückgestellte-erweiterung-mehrere-konturen-einer-operation)
- [Zurückgestelltes Bedienkonzept R3](#zurückgestelltes-bedienkonzept-r3-geometrie-und-bearbeitung-trennen)
- [Teststrategie](#teststrategie-für-die-neuen-aufgaben), [Abnahmetore](#abnahmetore)
- [Historische Ausgangslage und Etappen](#historische-ausgangslage-und-ursprüngliche-etappen)
- [Bisherige Prüfergebnisse](#prüfstand-nach-abschnitt-2) und [Arbeitsweise](#arbeitsweise)

Zielvorgaben sind keine Fertigmeldungen. Erledigte Aufgaben sind mit `[x]`,
offene mit `[ ]` markiert; Vorschläge und noch zu treffende Entscheidungen
sind im jeweiligen Thema ausdrücklich benannt. Historische Zahlen sind keine
aktuelle Testfreigabe. Der übergeordnete Architekturrahmen bleibt im
[Architekturbericht](dxf2gcode-architecture-review.md) dokumentiert.

## Neue Aufgaben zur Auswahl – Untersuchung vom 30.10.2026

Die Abschnitte 7–12 und 14 enthalten die neu gemeldeten Punkte mit Codebefund,
gewünschtem Verhalten und vorgeschlagenen Regressionen. **U1, U2 und die
Konfigurationsoption U4 sowie die Importfilter I2 sind umgesetzt; weitere
Wünsche bleiben vorgemerkt.**
Die Prioritäten sind ein
Vorschlag; die Auswahl des nächsten Abschnitts erfolgt nach dem Review.
Abschnitt 3 bleibt der nächste offene Schritt innerhalb des bestehenden
Werkzeugweg-Refactorings. Die Fehlerbehebungen können getrennt davon erfolgen.

| Kennung | Thema | Empfohlene Einordnung |
| --- | --- | --- |
| R1 | Absturz bei Drag-and-drop; Shape-Zuordnung zwischen Layern | Zuerst Absturz reproduzieren und absichern; Verschieben danach als eigenen Teil abnehmen |
| B1 | Bohren gegenüber Pocketing/Kompensation ausschließen | Hohe Priorität: widersprüchliche Bearbeitungszustände verhindern |
| B2 | Bohren bei Maschinenkompensation anbieten | Gemeinsam mit B1 prüfen und gezielt absichern |
| K1 | Konfigurationsfenster übersetzen | Anschließend oder unabhängig als begrenzte Korrektur |
| K2 | Bedeutung von „default“ und neue Profile | Nach K1 Beschriftungen und tatsächliche Standardwerte abgleichen |
| K3 | Zollwerte: Rundungsverlust in Konfiguration/GUI und Export verhindern | Hohe Priorität wegen veränderter Bearbeitungstiefen; unabhängig von K1/K2 bearbeitbar |
| U1 | Werkzeug-Dropdown auf Höhe des Durchmessers | Erledigt; Qt5/Qt6 und 100 %/150 % Skalierung geprüft |
| U2 | Ein-/Ausklappbuttons nach Baumzustand aktivieren | Erledigt; beide Bäume mit automatischen Regressionen geprüft |
| U3 | Nullpunkt per Kontextmenü wählen und im Dialog bearbeiten | Bestehende Nullpunktverschiebung um eine grafische Punktauswahl ergänzen |
| U4 | Ticket #157: Layer beim Laden wahlweise zuklappen | Konfigurationsoption umgesetzt; Standard bleibt aufgeklappt |
| U5 | Ticket #157: Tastenkürzel für Ein-/Ausklappen | Gesonderter offener Wunsch aus dem Ticket |
| V1 | Werkzeugkreis unabhängig vom Lead-in anzeigen | Mit gemeinsamer Vorschauquelle aus Abschnitt 5 abstimmen |
| R2 | Verbindliche Bearbeitungs-/Exportreihenfolge und Optimierung | Auf R1 aufbauen; Reihenfolge zuerst als Vertrag testen |
| R3 | Eigener Bearbeitungsbaum statt Zweckentfremdung der DXF-Layer | Bedienkonzept zunächst entscheiden; größere Erweiterung zurückstellen |
| R4 | Ticket #157: alphanumerische Layersortierung | Entfallen: ausdrücklich nicht gewünscht |
| P1 | ATC-Werkzeugwechsel, Z-Positionierung und Werkzeuglängenkorrektur | Exportvertrag und Maschinenprofil zuerst klären; keine pauschale Verschiebung einer G-Code-Zeile |
| D1 | Schleppmesser: Schnittlücke am Konturstart/-ende untersuchen | Vorhandene Überfahrt am aktuellen Stand prüfen; Ursache noch nicht bestätigt |
| D2 | Schleppmesser: zweiter Konturdurchlauf ohne Zwischenrückzug | Optionalen Ablauf nach D1 spezifizieren; Eckenschleifen beibehalten |
| M1 | Herkunftsanzeige in fertigen Paketen abnehmen | Implementierung vorhanden; vollständige Paket-/Debian-Prüfung nur nach gesonderter Freigabe |
| I1 | Ticket #157: kurze Segmente sichtbar markieren | Entfallen: ausdrücklich nicht gewünscht |
| I2 | Ticket #157: optionale Importfilter für Layer 0 und IGNORE | Erledigt; zwei unabhängige Optionen, standardmäßig beide aus |

**Abgeschlossene Bereinigung:** `.kilo/` und die erzeugte Datei `.coverage`
sind entfernt. Der frühere Plan bleibt unter
[archive/machine-comp-radius-leadin-plan.md](archive/machine-comp-radius-leadin-plan.md)
als ausdrücklich historische Referenz erhalten. `.coverage` ist bereits
ignoriert und kann durch einen späteren Coverage-Lauf erneut entstehen.

## Zielarchitektur und verbindliche Regeln

### Ziel und Zuständigkeiten

Erzeugte Geometrie, vollständiger Werkzeugweg und G-Code-Ausgabe haben
getrennte Aufgaben. Darstellung und Export werden aus demselben geplanten
Weg abgeleitet. Der Umbau erfolgt schrittweise mit erhaltenem Verhalten für
bestehende Projekte; eine absichtliche fachliche Änderung wird gesondert
beschlossen und getestet.

```text
Shape + aufgelöste Einstellungen + Maschinenfähigkeiten
                         |
                         v
              Werkzeugwegplanung (domain/toolpath)
          Offset, Leads, Passfolge, Tabs, Pocket, Tipweg
                         |
                         v
             ToolpathPlan (gemeinsame Quelle)
                  /                 \
                 v                   v
       2D-/3D-Projektion       G-Code-Exporter
                                     |
                                     v
                    Postprocessor / Steuerungsdialekt
```

- **Geometrie:** Algorithmen erhalten explizite Eingaben und liefern Geometrie
  zurück. Geometrieklassen kennen weder Postprocessor noch G-Code und greifen
  nicht auf globale GUI-/Konfigurationswerte zu.
- **Planung:** legt die vollständige Reihenfolge je Tiefenpass fest:
  Positionierung, Zustellung, Kontur-/Pocket-Schnitt, Tabs, Richtungswechsel
  und Rückzug. Sie beschreibt Zustände semantisch, erzeugt keine G-Code-Texte
  und zeichnet nicht. Die Verwendung bestehender StMove-Algorithmen ist ein
  Migrationsstand, keine dauerhaft vorgeschriebene Übergangsfassade.
- **Exporter:** serialisiert fertige Bewegungs- und Zustandsaktionen. Er
  berechnet keine Offsets, Passreihenfolgen oder Taschenbahnen.
- **Postprocessor:** formatiert für die konkrete Steuerung und verwaltet
  modale Ausgabezustände wie Zahlenformat, Vorschub und Koordinatenmodus.
  Unterschiede werden über Fähigkeiten oder begrenzte Dialektmethoden
  behandelt, nicht über Maschinenart-Abfragen in Geometrieklassen.

### Planaktionen und Diagnosevertrag

Der kanonische `ToolpathPlan` ist geordnet und unveränderlich; G-Code und Qt
sind kein Bestandteil seines Vertrags. Bewegungsart und fachliche Rolle
bleiben getrennt, etwa Z-Bewegung mit Rolle `plunge`.

| Aktion | Inhalt des Plans |
| --- | --- |
| `rapid_xy`, `rapid_z` | Zielposition für Eilfahrten |
| `linear_z` mit Rolle `plunge`/`retract`, `feed` | Z-Ziel, Vorschub, Bezug auf Oberfläche/Sicherheitsabstand |
| `linear_xy`, `arc` | Start/Ende; bei Bögen Mittelpunkt, Richtung und Öffnungswinkel |
| `compensation_on`/`compensation_off` | Kompensationszustand G40/G41/G42 und Wechselpunkt |
| XY-/Z-Bewegungen mit Rolle `tab` | Betroffener Konturabschnitt, Pass und Tab-Höhe |
| `drill`, `drill_retract` | Bohrposition und geordnete Zustell-/Rückzugstiefen |
| Bewegungen mit Rolle `drag_swivel`/`ramp` | Messer-Schwenken/Rampe samt Messerspitzenweg |
| `pre_cut`, `post_cut` | Bestehende Profilaktionen vor/nach der Kontur |
| `literal` | Expliziter benutzerdefinierter G-Code für CustomGCode; kein Ersatz für Geometrieplanung |

Ein Planlauf liefert `ToolpathPlanningResult`: einen vollständigen Plan oder
Diagnosen ohne exportierbaren Plan. `ToolpathDiagnostic` enthält stabilen
Code, Schweregrad, menschenlesbare Meldung und optional Shape-/Geometriebezug.
Warnungen dürfen einen gültigen Plan begleiten. Die Planung zeigt keine
Dialoge und schreibt keine Diagnosen in G-Code. GUI/CLI übernehmen die
Präsentation; der Exportadapter übernimmt Übersetzung, Anzeige und Logging.
Der Vertrag liegt in `domain/toolpath/plan.py`. Extraktionsmarker machen
Übersetzungsquellen für Qt Linguist auffindbar, ohne Qt im Fachkern zu laden.

### Maschinenart, Kompensation und Steuerungsfähigkeiten

Diese drei Aspekte bleiben unabhängig modelliert:

1. Maschinenart: Fräse, Drehmaschine oder Schleppmesser.
2. Kompensationsverantwortung: Softwareoffset oder G41/G42 durch die Steuerung.
3. Steuerungsdialekt/Fähigkeiten: etwa Bogenbefehle und Kompensationswechsel
   zwischen Pässen.

Strategien bilden die unterstützten Maschinenarten ab. Gemeinsame Bewegungen
können gemeinsam ausgegeben werden; Bohren und Messerschwenken bleiben
fachlich unterscheidbar. Ungültige Kombinationen werden im Planer validiert
und verständlich diagnostiziert, nicht nur durch Menü-Sperren verhindert.

Bei Maschinenkompensation enthält der Plan die programmierte Kontur und
explizite G41-/G42-Übergänge. Bei Softwarekompensation enthält er den
berechneten Werkzeugmittelpunktweg und verwendet G40. Programmierte Bahn und
erwarteter Werkzeugmittelpunktweg dürfen bei gemeinsamer Darstellung nicht
verwechselt werden.

### Tiefenpässe, offene Konturen und Pocketing

- Der Planer berechnet die geordnete Tiefenfolge. Bei offenen Konturen
  bestimmt er die Passrichtung und kehrt die Geometrie bei Bedarf um.
- Bei Richtungsumkehr berücksichtigt er G41-/G42-Seitenwechsel. Ob zwischen
  Pässen ein Zurücksetzen nötig ist, wird als Steuerungsfähigkeit übergeben.
- Tabs/Breaks werden nur für ihre tatsächlichen Pässe in denselben Plan
  aufgenommen. Export und Ansichten treffen keine zweite Passauswahl.
- Pocketing liefert Bahnen als Geometrie-/Planungsergebnis, statt dauerhaft
  `StMove.geos` als gemeinsame veränderliche Ergebnissammlung zu verwenden.
  Kontur, Werkzeug, Offsetstrategie, Richtung, Wandreferenz und Freiraum sind
  explizite Eingaben.
- G40/G41/G42 bestimmen auch bei Taschen die Richtung. `always_inward`
  bleibt entfernt; ältere Profile bleiben ladbar. Die bisherige GUI-Sperre
  für Pocketing bei Maschinenkompensation bleibt zunächst bestehen; siehe B2.
  Die Gültigkeit ist zusätzlich im Planer zu prüfen.

### Vorschau aus demselben Plan

- **2D:** jede unterschiedliche XY-Bahn einmal darstellen; keine
  deckungsgleichen Mehrfachlinien aufgrund wiederholter Tiefenpässe oder
  Richtungsumkehr. Tabs, Eilwege, Leads und Pocket-Bahnen bleiben erkennbar.
- **3D:** XY und Z aus demselben Plan übernehmen. Die bestehende Darstellung
  zwischen Start- und Endtiefe bleibt zunächst erhalten. Werden einzelne
  Pass-Ebenen sichtbar gemacht, stammen auch diese direkt aus dem Plan.
- Programmierte und erwartete kompensierte Bahn eindeutig kennzeichnen.
- Änderungen an Tiefe, Werkzeug, Offset, Tabs, Kompensation und Leads
  invalidieren Plan und beide Projektionen gemeinsam. Keine zweite
  Berechnung von Passfolge, Tabs, Leads oder Rückzügen in den Ansichten.
- Ursprungs-Shape, Operation, resultierende Teilkontur und Tiefenpass bleiben
  unterscheidbar. Eigene Startpunkte/Leads/Overcuts je Teilkontur sind als
  [zurückgestellte Erweiterung](#zurückgestellte-erweiterung-mehrere-konturen-einer-operation)
  vorgesehen, keine jetzt beschlossene Zusatzimplementierung.

## Stand

- [x] Semantisches Planmodell unter `domain/toolpath/plan.py` eingeführt.
- [x] Anwendungsfall `PlanToolpath` und gemeinsamer G-Code-Exporter eingeführt.
- [x] Vorschau und Export an den Planpfad angeschlossen.
- [x] Einen eng begrenzten Fräsfall in `SimpleMillingStrategy`
  abgebildet.
- [x] Die bisherige Shape-Exportlogik als Quelle des Plans ablösen.
- [ ] Planungslogik von Qt und globalem Laufzeitzustand entkoppeln.
- [ ] Alte doppelte Export- und Vorschaupfade entfernen.

## Nächste Arbeitsschritte

### 1. Verhalten und Planvertrag vervollständigen

- [x] Die gültigen Fälle aus der Verhaltensmatrix des Zielplans den konkreten
  Tests und Golden-Dateien zuordnen; Lücken je Maschinenart und
  Kompensationsmodus festhalten.
- [x] Für `ToolpathPlan` die benötigten semantischen Aktionen festlegen:
  Zustellung, Rückzug, Eilfahrt, Schnittbewegung, Kompensationswechsel,
  Tab-/Break-Abschnitt, Bohren und Schleppmesser-Schwenken.
- [x] Den GUI-unabhängigen Diagnosevertrag mit
  ToolpathDiagnostic/ToolpathPlanningResult festlegen und im
  PlanToolpath-Anwendungsfall für bestehende Planer normalisieren.
- [x] Alle Legacy-Planer so umstellen, dass sie Diagnosen zurückgeben und
  keine GUI-Dialoge oder direkten Postprocessor-Fehlermeldungen auslösen.
- [x] Vertragstests ergänzen, die Planinhalt und bisheriges G-Code-Ergebnis
  für denselben Fall vergleichen.

#### Vorhandene Verhaltensabdeckung

| Fall | Vorhandene Regressionen | Golden-G-Code | Planvertrag-Lücke |
| --- | --- | --- | --- |
| Fräsen, Maschinenkompensation G41/G42, geschlossene Kontur | `dxf2gcode_leadmove_golden_test.py` | `g41_closed.gcode`, `g42_closed.gcode` | Native Aktionen vorhanden; gezielte Planprüfungen pro Profil erweitern |
| Fräsen, Maschinenkompensation, offene Kontur und Richtungswechsel | `dxf2gcode_leadmove_golden_test.py` | `g41_open.gcode`, `g41_lead_out_radius_open.gcode` | Pass-/Kompensationswechsel als Aktionen; weitere Kombinationen gezielt absichern |
| Fräsen, Softwarekompensation G40, offen/geschlossen | `dxf2gcode_leadmove_golden_test.py`, `dxf2gcode_pocket_compensation_test.py` | `software_closed.gcode`, `software_open.gcode` | Vorbereitete Offset-Geometrie wird eingefroren; Offset-Algorithmus selbst noch in StMove |
| Tiefenpässe und Export-/Vorschauübereinstimmung | `dxf2gcode_toolpath_depths_test.py`, `dxf2gcode_toolpath_contract_test.py`, `dxf2gcode_stmove_gcode_test.py` | nur über andere Fälle indirekt | Native Tiefenfolge, Richtungswechsel und unveränderte Eingaben geprüft; Sonderfälle erweitern |
| Leads und Overcut, beide Kompensationsarten | `dxf2gcode_leadmove_*_test.py` | `g41_lead_*`, `software_lead_in_radius.gcode`, `*_overcut.gcode` | Native Aktionen mit Lead-Rolle und Diagnosen; bisheriger Geometriealgorithmus über expliziten Port |
| Tabs/Breaks mit Passauswahl | `dxf2gcode_breaks_pass_test.py` | keine dedizierten Golden-Dateien | Native Tab-Aktionen; zusätzliche bytegenaue Fallmatrix fehlt |
| Pocketing, Kompensation und Richtungsmodi | `dxf2gcode_pocket*_test.py`, `dxf2gcode_pocketmill_zigzag_test.py` | keine dedizierten Golden-Dateien | Native Pocket-Bewegungen und Tiefen; vorbereitete Geometrie weiterhin aus bestehendem Algorithmus |
| Bohren/Hole-Geometrien | Hole-Vorschau/-Hit-Test vorhanden | keine | Native Bohraktionen übernommen; gezielte Plan-/Golden-Abdeckung ergänzen |
| Schleppmesser: offen/geschlossen, Overcut, Rampeneinfahrt | `dxf2gcode_leadmove_golden_test.py` | `drag_knife_*.gcode` | Eigene native Strategie mit Drag-/Rampenrollen; weitere Planinhaltstests ergänzen |
| Drehmaschine | `dxf2gcode_leadmove_function_test.py` prüft Lead-Einschränkung | keine | Gemeinsame Konturstrategie übernimmt bisherigen Pfad; vollständige gültige Fälle/-grenzen nicht dokumentiert |
| Postprocessor-Bogenexport und Kompensationsregeln | `dxf2gcode_stmove_gcode_test.py`, Lead-Golden-Tests | Bogenverhalten nicht als eigene Golden-Matrix | Explizite MachineCapabilities; zusätzliche Profil-/Koordinatenkombinationen absichern |

Die Matrix dokumentiert bestehende Regressionen, nicht vollständige
Planabdeckung. Neue native Strategien benötigen für ihre vertikale Scheibe
gezielte Planinhaltstests und weiterhin bytegenaue G-Code-Vergleiche.

Der Diagnosevertrag ist als ToolpathDiagnostic und ToolpathPlanningResult in
domain/toolpath/plan.py festgelegt. Der Anwendungsfall übergibt einen
unveränderlichen ToolpathRequest an den reinen Planer und erhält diesen
Ergebnisvertrag direkt zurück. Ungültige Start-/Exit-Leads
und fehlende Kompensationsanfahrten liefern keinen exportierbaren Plan;
Tiefenwarnungen begleiten den bisherigen Plan. Die Planung öffnet keine
Dialoge und verändert keine Diagnose-Sammlung des Postprocessors. Erst beim
Export übernimmt der Adapter die Meldungen in den vorhandenen Anzeige- und
Logging-Kanal für GUI und CLI.

### 2. Planer von der Shape-Exportlogik lösen

- [x] `ToolpathPlanner` aus `adapters/toolpath/simple_milling.py` in einen
  klar benannten Planer verschieben; keine Strategie darf als
  `ShapeToolpathCommandBuilder`-Fallback exportieren.
- [x] `ShapeToolpathCommandBuilder` schrittweise in reine Planungsstrategien
  überführen. Während der Migration die vorhandenen Geometriealgorithmen
  wiederverwenden, aber deren Ausgabe als semantische Pläne erfassen und nicht
  durch Aufruf des Postprocessors simulieren.
- [x] Für die Strategien explizite Eingaben übergeben: Shape-/Geometriedaten,
  aufgelöste Bearbeitungseinstellungen und Maschinen-/Steuerungsfähigkeiten.
- [x] Mutationen wie Umkehren offener Konturen oder Ändern von Pocket-Tiefen
  aus dem Projektmodell entfernen; Planung muss wiederholbar sein und darf
  Eingaben nicht verändern.
- [x] Den einfachen geschlossenen Fräsfall als erste vollständig native
  Strategie behalten und die Abdeckung mit den folgenden Fällen erweitern.

Die Orchestrierung liegt jetzt in domain/toolpath/planner.py mit separaten
Strategien für einfache Fräsfälle, Konturen und Schleppmesser. inputs.py
definiert unveränderliche Geometrie-, Bearbeitungs- und Fähigkeitswerte;
movements.py erzeugt semantische Aktionen einschließlich Tabs und
Pocket-Verbindungsbewegungen. adapters/toolpath/planning.py friert die
bestehenden Modelldaten ein und adaptiert die bisherigen Lead-/Overcut-
Geometriealgorithmen. Kein Planer führt einen Postprocessor aus oder verändert
das Projektmodell. Der G-Code-Adapter serialisiert ausschließlich Aktionen.

Die alten Module adapters/toolpath/simple_milling.py,
shape_plan_builder.py und geometry_gcode.py sind entfernt. Abschnitt 3
vervollständigt als Nächstes die gezielte fachliche Plan- und Exportmatrix,
insbesondere für Bohren, Drehmaschine und weitere Kombinationen. Die
Weiterverwendung vorhandener StMove-/Offset-/Pocket-Geometriealgorithmen
bedeutet weiterhin keinen vollständigen Abschluss des gesamten Refactorings.

### 3. Fälle in kleinen vertikalen Scheiben migrieren

Jede Scheibe umfasst Planer, Export, Vorschauprojektionen und Regressionen.
Die Reihenfolge minimiert Abhängigkeiten zwischen den Fällen.

- [ ] Geschlossene Kontur, Softwarekompensation, mehrere Tiefenpässe.
- [ ] Offene Kontur mit alternierender Passrichtung und Softwarekompensation.
- [ ] Maschinenkompensation G41/G42 einschließlich Ein-/Ausschalten und
  Richtungswechselregeln des Postprocessors.
- [ ] Leads, Overcut und ungültige Lead-Geometrie mit Diagnosen.
- [ ] Tabs/Breaks mit Auswahl der betroffenen Pässe.
- [ ] Pocketmilling mit frei wählbarer Kompensationsrichtung G40/G41/G42.
- [ ] Bohren und Hole-Geometrien.
- [ ] Schleppmesser einschließlich Tipweg, Drag-Hops und Rampeneinfahrt.
- [ ] Drehmaschine: vorhandene unterstützte Formen und Einschränkungen
  explizit abbilden.

### 4. G-Code-Serialisierung auf semantische Bewegungen umstellen

- [x] `ToolpathGCodeExporter` serialisiert alle Planaktionen; er berechnet
  keine Konturen, Offsets, Passfolgen oder Pocket-Bahnen.
- [ ] Postprocessor-Dialekte formatieren nur Bewegungs- und Steuerungsaktionen
  und verwalten ihren modalen Ausgabestatus.
- [x] Direkte Postprocessor-Aufrufe aus `ShapeToolpathCommandBuilder`,
  Geometrieklassen und Planungslogik entfernen.
- [ ] Alle vorhandenen Golden-G-Code-Ausgaben bytegenau erhalten.

### 5. Vorschau und gemeinsame Planquelle abschließen

- [ ] 2D-Projektion zeigt gleiche XY-Bahnen einmal und kennzeichnet Tabs,
  Leads, Eilwege sowie programmierte beziehungsweise kompensierte Bahn
  eindeutig.
- [ ] 3D-Projektion übernimmt Z und Passfolge aus demselben Plan.
- [ ] 2D/3D-Vorschau berechnet weder Passfolge noch Tabs, Leads oder
  Rückzüge unabhängig vom Export neu.
- [ ] Änderungen an Werkzeug, Tiefe, Kompensation, Leads, Tabs und
  Pocket-Einstellungen invalidieren den Plan und beide Projektionen zusammen.

### 5a. Werkzeugänderung auf eine Shape begrenzen

- [x] In der GUI prüfen und korrigieren, dass ein Werkzeugwechsel für eine
  einzelne Shape nicht auf andere Shapes oder deren Layer-Einstellungen
  übertragen wird.
- [x] Den Anwendungsfall für eine Shape-Änderung klar von einer absichtlichen
  Layer-/Mehrfachauswahl-Änderung trennen; nur die betroffene Shape und ihr
  Werkzeugweg werden aktualisiert.
- [x] Regressionstest ergänzen: Bei mehreren Shapes ein Werkzeug an einer
  Shape wechseln und sicherstellen, dass Werkzeugnummer und Werkzeugwerte
  aller übrigen Shapes unverändert bleiben; Vorschau und Export der geänderten
  Shape verwenden das neue Werkzeug.
- [x] Bei unterschiedlichen Werkzeugen in der Auswahl „Verschiedene Werkzeuge“
  und „—“ für die Werkzeugwerte anzeigen; eine bewusste Werkzeugauswahl gilt
  weiterhin für alle ausgewählten Shapes.

Die optionale Shape-Werkzeugzuordnung wird zusätzlich in Projektdateien
gespeichert. Alte Projekte ohne diese Angabe übernehmen weiterhin das
Layer-Werkzeug. Vorschau, Kompensation und Export verwenden dieselben
effektiven Werkzeugwerte; der Export berücksichtigt Werkzeugwechsel innerhalb
eines Layers in der bestehenden Shape-Reihenfolge. Die Regressionen stehen
in tests/dxf2gcode_shape_tool_test.py.

### 6. Kopplungen und alte Pfade entfernen

- [ ] `domain/toolpath` und `domain/geometry` benötigen weder Qt noch
  `bootstrap.runtime_state` oder Postprocessor-Module.
- [ ] Globale Werte wie `g.config` und Maschinenart in der Planungslogik durch
  explizite Einstellungen und Fähigkeiten ersetzen.
- [x] GUI-spezifische Fehleranzeige aus Planern entfernen; GUI und CLI
  präsentieren dieselben Diagnosen jeweils passend.
- [ ] Entfernen der alten Shape-basierten G-Code-Ausgabe und aller
  Übergangspfade erst nach Migration sämtlicher Aufrufer.

### 7. Bearbeitungsarten und Kompensation konsistent auswählen

#### B1 – Bohren schließt Pocketing und aktive Fräsradienkompensation aus

**Codebefund:** `MyDropDownMenu` in
`presentation/qt/canvas.py` verändert in `setDrill`, `setPocket` und den
Kompensationsaktionen jeweils nur den eigenen Wert. Eine gemeinsame Regel
fehlt; `Drill`, `Pocket` und `cut_cor` können widersprüchlich gesetzt sein.
`domain/toolpath/strategies/contour.py` wertet diese Werte an mehreren Stellen
aus. Der Export darf die widersprüchliche Auswahl nicht erst auflösen müssen.

- [ ] Die zuletzt bewusst ausgewählte Aktion bestimmt den Zustand aller
  betroffenen Shapes. Bohren einschalten setzt `Drill=True`, `Pocket=False`
  und `cut_cor=40`. G40 ist dabei der technische Neutralzustand, keine aktive
  G41-/G42-Kompensation.
- [ ] Pocketing einschalten oder G40/G41/G42 ausdrücklich auswählen schaltet
  Bohren aus. Pocketing und die drei Kompensationsauswahlen bleiben
  kombinierbar; kein Modus „immer nach innen“ wird wieder eingeführt.
- [ ] Das bloße Ausschalten einer Bearbeitungsart stellt keinen früheren
  Zustand wieder her. Bei Mehrfachauswahl gilt eine gemeinsame Zielaktion;
  keine unabhängige Umkehr jedes einzelnen Ausgangszustands.
- [ ] Die Zustandsänderung über einen gemeinsamen Anwendungsfall und eine
  fachliche Regel ausführen. Menühaken, Parameteranzeige, Plan und Vorschau
  müssen anschließend denselben Zustand darstellen. Die Regel nicht als
  getrennte Sonderlogik in mehreren Qt-Slots implementieren.
- [ ] Beim Laden bereits widersprüchlicher Projekte den Konflikt erkennen.
  **Vor Umsetzung festlegen:** Warnung und explizite Auswahl oder eine
  dokumentierte Vorrangregel. Ohne Aktionshistorie ist „zuletzt gewählt“
  aus einer alten Datei nicht rekonstruierbar; nichts stillschweigend raten.

**Abnahme und Tests:** Alle Übergänge von/nach Bohren mit Pocket an/aus und
G40/G41/G42 prüfen, einschließlich gemischter Mehrfachauswahl und erneutem
Öffnen des Menüs. Fachregel ohne Qt testen; vorhandene
`dxf2gcode_pocket_multiselect_test.py` und
`dxf2gcode_pocket_comp_mode_test.py` um GUI-Aktionen ergänzen. Projekt-Roundtrip
und Plan-/G-Code-Regression belegen, dass Bohren keine Taschenbewegungen oder
aktive Fräskompensation hinterlässt. Bewusst geändertes Verhalten zuvor
ungültiger Kombinationen getrennt vom unveränderten Golden-Bestand behandeln.

#### B2 – Bohren unabhängig vom Ort der Kompensationsberechnung anbieten

**Codebefund:** Der aktuelle Bohren-Menüeintrag in `canvas.py` ist an
`allClosed` und `allArcs` gebunden, bereits **ohne** Prüfung von
`Cutter_Compensation.done_by_machine`. Nur Pocketing hat dort eine zusätzliche
Sperre bei Maschinenkompensation. Die gemeldete Einschränkung des Bohrens ist
somit im aktuellen Quellstand noch nicht bestätigt. Zusätzlich enthält die
Geschlossenheitsprüfung `allClosed == False` statt einer Zuweisung; sie ist
bei der Untersuchung der Menüverfügbarkeit mitzuberücksichtigen.

- [ ] Mit derselben gültigen Bohrkontur, ausgewähltem Profil und derselben
  Version beide Werte von `done_by_machine` reproduzieren. Geometrieauswahl
  und gegebenenfalls einen veralteten installierten Stand unterscheiden.
- [ ] Bohren bei geeigneter Geometrie sowohl bei Software- als auch bei
  Maschinenkompensation auswählbar halten. Die globale Einstellung bestimmt,
  wer eine Fräsbahn kompensiert; sie aktiviert keine Kompensation für Bohren.
  Die gegenseitigen Ausschlüsse aus B1 gelten in beiden Konfigurationen.
- [ ] Die Geometrieprüfung einschließlich offener und gemischter Auswahl
  korrekt absichern. Die Pocketing-Sperre bei Maschinenkompensation ist eine
  gesonderte bestehende Einschränkung und wird durch diesen Punkt nicht
  automatisch aufgehoben.

**Abnahme und Tests:** Parametrisierte Menü-/Workflowtests für beide
Konfigurationen mit gültiger geschlossener Kreisgeometrie sowie ungültiger
und gemischter Auswahl; mindestens ein Plan-/Exportfall pro Konfiguration.
Falls der Fehler nur in einem älteren Wheel auftritt, den Versionsunterschied
dokumentieren und keine unnötige Änderung am aktuellen Code vornehmen.

### 8. Konfiguration, Standardwerte und Übersetzungen

#### K1 – Übersetzung des Konfigurationsfensters wiederherstellen

**Codebefund:** `presentation/qt/configuration_widgets.py` verwendet
`config.tr`; `adapters/config/runtime_config.py:MyConfig.tr` fragt den
Qt-Kontext `MyConfig` ab. Die untersuchten Beschriftungen stehen in allen
drei TS-Katalogen unter `@default` als `unfinished`; ihre alten Einträge unter
`MyConfig` sind `obsolete`. Dieser Kontextbruch erklärt den englischen
Rückfall. Der tatsächliche Dialog mit geladenen QM-Dateien ist noch zu prüfen.

**Weiterer bestätigter Übersetzungsfehler:** Im Menü „Maschinen Typ“ ist
`&Lathe` im deutschen `MainWindow`-Katalog fälschlich als `&Hilfe` übersetzt.
Gemeint ist „Drehmaschine“. Die Aktion ist in `application.py` korrekt mit
`setMachineTypeToLathe` verbunden und setzt `machine_type='lathe'`; der
Menütext ist falsch, nicht die Zuordnung der Aktion. Diesen Eintrag bei K1
korrigieren und die Maschinenbezeichnungen in allen drei Katalogen prüfen.

- [ ] Einen eindeutigen Übersetzungskontext für die ausgelagerten
  Widget-Definitionen festlegen und die Extraktion darauf abstimmen, damit
  spätere Übersetzungsläufe den Fehler nicht erneut erzeugen.
- [ ] Anwendungs- und Postprozessorkonfiguration einschließlich Überschriften,
  Hilfetexten und Auswahleinträgen prüfen. Technische Profil-/Dateischlüssel
  bleiben unabhängig von übersetzten Anzeigenamen stabil.
- [ ] Deutsch, Französisch und Russisch gemeinsam aktualisieren, QM-Dateien
  neu erzeugen und den geöffneten Dialog mit diesen Dateien prüfen.

**Abnahme und Tests:** Kontext-/Katalogprüfung und fokussierter Qt-Test, der
einen echten Translator lädt und repräsentative Labels im aufgebauten Dialog
prüft. Auch nach erneutem Extrahieren/Kompilieren müssen diese Labels
übersetzt bleiben. Bestehende Nutzereinstellungen werden dabei nicht verändert.
Zusätzlich die drei Maschinentypen im übersetzten Menü prüfen: „Fräsen“,
„Drehmaschine“ und „Schleppmesser/Drag Knife“ müssen auf die zugehörigen
internen Werte zeigen; der Hilfemenütext darf nicht als Maschinentyp erscheinen.

#### K2 – „default“ gegenüber tatsächlichen Vorgabewerten klären

**Codebefund:** Die Texte in `configuration_widgets.py` tragen pauschal
„(default)“. `CONFIG_SPEC` in `runtime_config.py` legt dagegen Folgendes fest:

| Einstellung | Derzeitige Vorgabe für ein neues Profil |
| --- | --- |
| Deaktivierte Pfade anzeigen | `True` |
| Exportroute live aktualisieren | `False` |
| Liniensegmente teilen | `False` |
| Automatische Fräsradienkompensation | `False` |
| Maschinentyp | `milling` |

`MainWindow.initializeConfigProfile` erzeugt ein neues Profil über die
Konfigurationsklassen mit deren Vorgaben; es kopiert absichtlich nicht das
aktuelle Profil. Mehrere `False`-Werte entsprechen damit dem Schema. Ob
zusätzlich ein Fehler beim tatsächlichen Anlegen/Laden vorliegt, ist mit
isolierten Profilen noch zu prüfen.

- [ ] Schema, frisch erzeugte Datei, geladene Werte, Checkboxanzeige und
  Wirkung beim Programmstart je betroffener Option vergleichen.
- [ ] Den Unterschied zwischen Werkseinstellung, gespeichertem Profilwert
  und Vorgabe für neue/importierte Shapes verständlich benennen.
  **Beschriftungsvorschlag:** den pauschalen Zusatz entfernen und den
  konkreten Standardwert in Hilfe/Tooltip nennen, etwa „Standard: Aus“.
- [ ] Vor einer Änderung der fachlichen Standardwerte die gewünschten Werte
  einzeln abstimmen. „(default)“ ist kein Auftrag, alle Optionen einzuschalten;
  vorhandene Profile dürfen nicht überschrieben werden.

**Abnahme und Tests:** Neue temporäre Profile, Speichern/Laden und erneuter
Start verwenden die vereinbarten Werte; bestehende individuelle Profile
behalten ihre Werte. Vorhandene Profil-/Konfigurationsworkflowtests erweitern;
alle geänderten Texte gemäß K1 in den drei Sprachen pflegen.

#### K3 – Dezimalpräzision und Werterhaltung insbesondere im Zollmodus

**Forumsbericht:** Im Screenshot vom 16./27. Juni 2026 beschreibt Randy
zunächst einen Anzeigefehler, später ausdrücklich gerundete Werte im G-Code.
Gewünscht sind etwa 0,015 Zoll Schneidtiefe und 0,005 Zoll Schwenk-/Slice-Tiefe.
Als Umgehung wurden andere Werte eingegeben und die Ausgabe nachträglich
ersetzt. Gewünscht werden vier Nachkommastellen in der Zolloberfläche.
Dieser Punkt war bislang weder durch K1 (Übersetzung) noch K2 (Vorgabewerte)
oder D1/D2 (Schleppmesserbahnen) ausdrücklich erfasst.

**Codebefund und fokussierte Prüfung:** `CfgDoubleSpinBox` in
`presentation/qt/configwindow.py` setzt die Präzision nur bei explizitem
`precision`-Argument. Die Tiefenfelder in `configuration_widgets.py` übergeben
dieses nicht. Ein isolierter Offscreen-Test des aktuellen Widgets am
30.10.2026 ergab `decimals() == 2`: Beim Setzen von 0,015 und 0,005 lieferte
`getValue`/`spinbox.value()` jeweils 0,01; auch die negativen Gegenstücke
wurden auf -0,01 reduziert. Das Widget verändert also seinen Zahlenwert,
nicht nur den dargestellten Text. Die konkrete Rundungsrichtung ist nicht
in jedem Fall identisch mit der älteren Meldung; der Präzisionsverlust ist
jedoch im aktuellen Stand reproduziert. Der Test legte kein Profil an und
veränderte keine Benutzerkonfiguration.

Die Shape-Parameteranzeige in `treehandling.py` verwendet an mehreren Stellen
bereits vier Nachkommastellen. Die G-Code-Formatierung in
`postprocessor.py:fnprint` verwendet dagegen die Profilvorgabe
`Number_Format.post_decimals` (Schema-Standard: drei). GUI-, Modell- und
Ausgabepräzision sind deshalb getrennt zu untersuchen. Der vollständige
Dialog→Speichern→Plan→G-Code-Fehlerpfad wurde hier noch nicht ausgeführt.

- [ ] Zollwerte mit mindestens vier Nachkommastellen in den betroffenen
  Eingabefeldern nutzbar machen. Alle relevanten Felder prüfen, darunter
  Tiefen, Werkzeug-/Spitzenversatz, Leads und Start-/Rückzugskoordinaten;
  nicht nur die Schleppmesser-Shapeanzeige ändern.
- [ ] Das Öffnen und unveränderte Bestätigen eines Dialogs darf gültige
  Konfigurationswerte nicht quantisieren. Anzeigeformatierung, interne
  Genauigkeit und bewusst angeforderte Eingabeänderung klar trennen.
  **Vor Umsetzung klären:** Umgang mit vorhandenen Werten, die mehr Stellen
  besitzen als die gewünschte Standardanzeige; diese nicht still runden.
- [ ] Gesamten Weg von frischer Eingabe beziehungsweise direkt geladener
  `config.cfg` über Profilwechsel, Shape-/Layerwerte, Projektpersistenz und
  Toolpath-Eingaben bis zur Ausgabe mit denselben Werten prüfen. Unverändertes
  Öffnen/Bestätigen auch bei mm/in-Wechsel und Dezimalkomma berücksichtigen.
- [ ] Zahlenformat des Postprozessors separat absichern: 0,015 und 0,005
  sind bereits mit drei Nachkommastellen darstellbar. Ihr Verlust ist nicht
  allein durch diese Ausgabevorgabe erklärbar. Für Werte wie 0,0005 Zoll
  eine ausreichend genaue Profilvorgabe beziehungsweise einen verständlichen
  Hinweis vereinbaren; vorhandene Profile und Goldens nicht pauschal ändern.
- [ ] Bereits gerundete gespeicherte Werte können nicht automatisch
  rekonstruiert werden. Den Fix auf zukünftige Werterhaltung begrenzen und
  betroffene Nutzer auf eine Prüfung ihrer Tiefen/Profilwerte hinweisen.

**Abnahme und Tests:** Automatische Regression für tatsächlichen Widgetwert
und unverändertes Dialog-Bestätigen; positive/negative Werte 0,015, 0,005 und
0,0005 sowie repräsentative mm-Werte verwenden. Neue und vorhandene Profile,
Projekt-Roundtrip, Layer-/Shape-Overrides und Einheitenwechsel einbeziehen.
Für Schleppmesser Schneid- und Schwenktiefe im Plan und ausgegebenen Z-Code
prüfen; Ausgabepräzision dabei explizit festlegen. Ein Anzeige-only-Test oder
ein bloßer Vergleich der Stringlänge genügt nicht. Nur der oben beschriebene
Widget-Test wurde ausgeführt; die Behebung und weitergehenden Regressionen
sind zur Freigabe vorgemerkt.

### 9. GUI-Anordnung, Baumzustand und Werkzeugdarstellung

#### U1 – Werkzeugauswahl an der Durchmesserzeile ausrichten

**Ursprünglicher Befund:** In `presentation/qt/resources/dxf2gcode.ui` lag
`toolDiameterComboBox` neben dem gesamten mehrzeiligen Werkzeugwerteblock.
Das führte zur vertikalen Zentrierung. Die Auswahl liegt jetzt im gemeinsamen
`toolValuesGrid` in derselben Zeile wie der Durchmesser.

- [x] Die Auswahl oben auf Höhe der Durchmesserzeile anordnen. Die `.ui`
  bleibt die Quelle; generierte Dateien über den vorhandenen Buildweg erzeugen.
- [x] Leere und gemischte Auswahl, deaktivierte Anzeige sowie lange
  Werkzeugnamen bei schmalem Fenster und anderer Skalierung berücksichtigen.

**Abnahme und Tests:** Gezielte Sichtprüfung bei normaler und hoher
DPI-Skalierung; bestehende Auswahltests weiterverwenden. Kein zusätzlicher
Pixelvergleichstest nur für die Verschiebung des Widgets.

**Prüfung am 30.10.2026:** Offscreen-Ansichten bei 100 % (Qt5) und 150 %
(Qt6) mit leerer/deaktivierter Auswahl, längerer Werkzeugnummer und gemischter
Auswahl visuell geprüft. Dropdown und Durchmesser bleiben zeilengleich.
Die bestehenden zwölf Shape-Werkzeugtests bestehen mit beiden Qt-Versionen.
Keine neuen GUI-Texte; die Übersetzungskataloge bleiben unverändert.

#### U2 – Baum-Buttons nur bei möglicher Zustandsänderung aktivieren

**Ursprünglicher Befund:** Die Buttons berücksichtigten den Baumzustand nicht.
Entities klappte nur bis Tiefe 0 zu. Jetzt meldet `TreeView` die verfügbaren
Aktionen über `expansionAvailabilityChanged`; `TreeHandler` verbindet beide
Buttonpaare einheitlich. Modellwechsel lösen alte Signalverbindungen und
registrieren Einfügen, Entfernen, Verschieben, Reset und Layoutänderung des
aktuellen Modells neu. Beide Zuklappaktionen verwenden `collapseAll`.

- [x] Für Layer und Entities denselben Vertrag umsetzen: vollständig
  zugeklappt → nur Ausklappen aktiv; vollständig aufgeklappt → nur Zuklappen
  aktiv; Zwischenstand → beide aktiv. Ohne aufklappbare Knoten sind beide
  deaktiviert. Blätter zählen nicht als zu-/aufklappbare Zweige.
- [x] Auch manuelles Klappen einzelner Zweige, Dateiladen, Modellwechsel und
  Verschieben müssen den Buttonzustand aktualisieren. Verdeckte Unterzweige
  dürfen den sichtbaren Zustand nicht falsch klassifizieren.
- [x] Entities ebenfalls vollständig zuklappen, einschließlich sichtbarer
  Wurzelknoten. Der bisherige Anfangszustand beim Laden (`expandToDepth(0)`)
  bleibt erhalten; die verfügbaren Buttons werden daraus abgeleitet.

**Abnahme und Tests:** Fokussierte Qt-Tests für beide Bäume mit leerem Baum,
Blättern, mehreren Hierarchiestufen, Zwischenständen und Modellneuladen.
Prüfen, dass jeder aktive Button tatsächlich eine Darstellung ändert und
die Bäume ihren Zustand unabhängig voneinander verwalten.

**Prüfung am 30.10.2026:** Acht neue Regressionen in
`dxf2gcode_treeview_test.py` prüfen leere Modelle/Blätter, manuelles und
vollständiges Klappen, verdeckte expandierte Unterzweige, Modellwechsel,
Einfügen/Entfernen/Umordnen, Signalblockierung und unabhängige Ansichten.
Der echte MainWindow-Workflow prüft beide Buttonpaare vor und nach DXF-Import
einschließlich des vollständigen Entities-Zuklappens. Qt5: 16 TreeView-,
ein MainWindow- und zwölf Werkzeugtests bestanden. Qt6: die acht neuen
Baumzustands-, ein MainWindow- und zwölf Werkzeugtests bestanden.

Im zusätzlichen Qt6-Lauf des gesamten TreeView-Testmoduls scheitern zwei
bestehende Drag-and-drop-Tests an alten Enum-Zugriffen; siehe R1. Das ist
keine grüne Gesamtfreigabe. UI-Dateien für Qt5/Qt6 sind neu erzeugt; Qt6
verwendet das vorhandene unveränderte Ressourcenmodul, da lokal `rcc` fehlt.
Keine Pakete installiert und keine Vollsuite, Release-/MSI-Builds oder
Debian-Läufe gestartet.

#### U3 – Nullpunkt über einen Punkt im Kontextmenü festlegen

**Gewünschter Ablauf:** An der gewünschten Position in der Zeichnungsansicht
das Kontextmenü öffnen und „Nullpunkt hierher verschieben …“ wählen.
Anschließend öffnet sich der bestehende Eingabedialog aus dem Menü mit den
aus diesem Punkt berechneten Verschiebungswerten. Diese lassen sich vor dem
Übernehmen bearbeiten oder unverändert bestätigen.

**Codebefund:** `MainWindow.moveWorkpieceZero` in
`presentation/qt/application.py` öffnet bereits den Dialog für die beiden
Achsenwerte (`cont_dx`, `cont_dy`) und übernimmt die Verschiebung nach
Bestätigung. `MyDropDownMenu` in `canvas.py` erhält die angeklickte Position
bereits als `clicked`. Diese Eingänge sollten denselben Anwendungsablauf
verwenden, statt eine zweite Nullpunktberechnung in der GUI einzuführen.

- [ ] Den Kontextmenüeintrag ergänzen und den beim Öffnen gewählten Punkt
  als Ausgangspunkt verwenden. Die berechneten Werte im bestehenden Dialog
  vorbelegen; sie bleiben editierbar. Der normale Menüaufruf für die rein
  numerische Eingabe bleibt erhalten.
- [ ] Erst beim Bestätigen die Verschiebung anwenden. Abbrechen verändert
  weder Nullpunkt noch Geometrie, Projektzustand oder Werkzeugweg.
- [ ] Klickkoordinaten korrekt in die vorhandene Nullpunktverschiebung
  umrechnen: aktuelle Verschiebung, Transformationen, Bildschirm-Y-Richtung
  und aktive Einheit berücksichtigen. Bei unveränderter Bestätigung soll der
  gewählte Zeichnungspunkt im resultierenden System bei X=0/Y=0 liegen.
- [ ] Vorschau, Plan und Export gemeinsam aktualisieren; die bestätigten
  Werte müssen beim erneuten Öffnen des numerischen Dialogs erscheinen und
  über die bestehende Projektpersistenz erhalten bleiben.
- [ ] **Begriff vor Umsetzung abstimmen:** Die vorhandene Funktion verschiebt
  den Werkstück-/Zeichnungsnullpunkt. Der vom Nutzer genannte
  „Maschinennullpunkt“ darf nicht versehentlich als Änderung des physischen
  Maschinenreferenzpunkts oder als neuer Steuerungsbefehl umgesetzt werden.
  Ein optionales Fangen auf Geometriepunkte ist gesondert festzulegen; eine
  zusätzliche Fangfunktion ist mit diesem TODO noch nicht beschlossen.
- [ ] Neue Menü-/Hilfetexte gemeinsam in Deutsch, Französisch und Russisch
  pflegen.

**Abnahme und Tests:** Klickpunkt → vorbelegter Dialog → Bestätigen sowie
Bearbeiten und Abbrechen gezielt testen. Bestehenden numerischen Menüweg,
wiederholtes Setzen ohne Verschiebungsdrift, bereits verschobene/transformierte
Zeichnungen, mm/in und Projekt-Roundtrip einbeziehen. Vorschau und exportierte
Koordinaten müssen dieselbe bestätigte Verschiebung verwenden. Die Umsetzung
bleibt bis zur Auswahl dieses Punkts zurückgestellt.

#### U4 – Ticket #157: Startzustand des Layerbaums konfigurieren

**Quelle:** [SourceForge-Ticket #157 – Feature Request(s)](https://sourceforge.net/p/dxf2gcode/tickets/157/).
Das Ticket wünscht unter anderem zuklappte Layer als wählbaren Startzustand.
Die Nutzerfestlegung für diese Umsetzung lautet: **Standard weiterhin
aufgeklappt.** Der zusätzliche Importfilterwunsch I2 ist ebenfalls umgesetzt;
das Tastenkürzel U5 bleibt offen.
Alphanumerische Sortierung (R4) und Segmentmarkierung (I1) sind nach
ausdrücklicher Nutzerfestlegung vom 30.10.2026 ausgeschlossen; sie sollen
nicht umgesetzt werden. U4 erledigt nicht die übrigen offenen Ticketwünsche.

- [x] Checkbox „Layer beim Laden einer Zeichnung ausklappen“ in der
  Anwendungskonfiguration unter General settings ergänzen.
- [x] `General.expand_layers_on_load` als persistierten booleschen Wert mit
  Standard `True` einführen. Abgewählt startet der Layerbaum zugeklappt;
  gewählt startet er vollständig aufgeklappt.
- [x] Die Einstellung beim Aufbau des Layerbaums auswerten, nicht bei jeder
  Auswahl-/Parameteränderung. Manuelles Klappen bleibt jederzeit möglich;
  die U2-Buttons zeigen den resultierenden Zustand an. Der Entities-Baum
  und fachliche Bearbeitungs-/Exportreihenfolgen bleiben unberührt.
- [x] Ältere unterstützte Profile ohne den Schlüssel erhalten `True`.
  Konfigurationsschema 9.15 ergänzt die Versionen 9.11–9.14 kompatibel;
  bestehende Werte gehen nicht verloren. Kein `.d2g`-Formatwechsel.
- [x] Neue Beschriftung in Deutsch, Französisch und Russisch pflegen und
  die QM-Dateien kompilieren. Expliziter Qt-Kontext `MyConfig` verhindert
  für diesen neuen Text den unter K1 beschriebenen Kontextfehler.

**Prüfung:** Vier fokussierte Konfigurationstests prüfen Standard, Laden aller
älteren unterstützten Versionen ohne Schlüssel, Speichern/Laden beider Werte
und die echte Checkbox mit geladenen DE-/FR-/RU-Übersetzungen. Der
MainWindow-Workflow prüft beide Startzustände einschließlich U2-Buttons,
unverändertem Entities-Baum, Shape-Parametern und Reihenfolge. Diese Prüfungen
bestehen unter Qt5 und Qt6. Lange Gesamt-/Debian-/Release-Prüfungen wurden
nicht ausgeführt.

#### U5 – Ticket #157: Tastenkürzel zum Ein-/Ausklappen

- [ ] Tastenkürzel für die Layer-Klappaktionen vorsehen. Vor Umsetzung
  festlegen, ob der gesamte Baum oder die ausgewählte Gruppe gemeint ist
  und ob dieselbe Bedienung auch für Entities gelten soll.
- [ ] Mit vorhandenen Baum-/Canvas-Tasten und deren Fokusregeln abstimmen;
  dieselben Aktionen und Verfügbarkeitsregeln wie die U2-Buttons verwenden.

**Abnahme und Tests:** Echte Tastenevents im aktiven Baum prüfen, einschließlich
leerem, vollständig ein-/ausgeklapptem und gemischtem Baum. Keine Auslösung
bei Texteingabe oder unbeabsichtigte Änderung des Canvas-Zooms.

#### V1 – Werkzeugkreis am Start unabhängig vom Lead-in anzeigen

**Codebefund:** `StMoveGUI` in `canvas2d.py` zeichnet den Kreis nur innerhalb
der Prüfung auf einen nicht leeren Lead-in-Pfad.
`_lead_in_dive_point` und `boundingRect` haben ebenfalls diese Bindung.
Eine eigene Konfigurationsoption für die Sichtbarkeit fehlt.

- [ ] Den Werkzeugdurchmesser auch ohne Lead-in am zugehörigen Startpunkt
  darstellen; Zeichnen und Bounding-Box gemeinsam von der Lead-Auswahl lösen.
- [ ] Eine persistierte Anzeigeoption mit verständlichem Text in allen drei
  Sprachen ergänzen. **Vorschlag zur Freigabe:** standardmäßig eingeschaltet;
  Ausschalten verbirgt nur den Werkzeugkreis, nicht Leads oder Werkzeugbahnen.
- [ ] Vor Umsetzung den Bezugspunkt eindeutig vereinbaren. **Vorschlag:**
  tatsächlicher Werkzeugmittelpunkt am Einstieg des geplanten Schnitts;
  mit Lead-in dessen vorhandener Eintauchpunkt, ohne Lead-in der entsprechende
  Bahnanfang. Bei Softwarekompensation den kompensierten Punkt verwenden;
  bei Maschinenkompensation eine nur angenäherte Darstellung gegebenenfalls
  kenntlich machen. Kein zweiter Offset-/Lead-Algorithmus in der Ansicht.
- [ ] Effektive Shape-Werkzeuge, Transformationen, Zoom und mehrere
  Teilkonturen aus der zurückgestellten Erweiterung berücksichtigen.
  Zunächst betrifft der Befund 2D; den gewünschten Umfang in 3D vor Umsetzung
  festlegen und mit Abschnitt 5 abstimmen.

**Abnahme und Tests:** Anzeige an/aus mit Lead-in an/aus, G40/G41/G42,
Shape-Werkzeugoverride und transformierter Geometrie prüfen. Mittelpunkt,
Radius und Bounding-Box gezielt testen; die Anzeigeoption darf den Plan oder
G-Code nicht verändern. Bestehende Startpunkt-/Lead- und Vorschautests ergänzen.

### 10. Layer-Zuordnung, Drag-and-drop und Exportreihenfolge

#### R1 – Absturz beheben und Shape-Wechsel zwischen Layern modellieren

**Codebefund:** `TreeView.dropEvent` in `treeview.py` verschiebt Zeilen
innerhalb desselben Elternknotens. In einem Ablehnungszweig wird
`drop_item.parent().rowCount()` aufgerufen, obwohl ein fremder oberster
Layer keinen Parent hat. Damit ist ein plausibler `None`-Zugriff sichtbar;
der gemeldete Absturz ist ohne Reproduktion/Traceback noch nicht abschließend
diesem Pfad zugeordnet. Ein echter Wechsel der Layer-Zugehörigkeit wird durch
die bisherigen `takeRow`-/`insertRow`-Aufrufe nicht implementiert.

**Zusätzlicher Qt6-Befund bei U2:** Zwei bestehende Tests
(`test_drop_reorders_siblings_and_calls_export_callback` und
`test_drop_without_drag_or_onto_viewport_is_ignored`) scheitern an
`TreeView.BelowItem`/`TreeView.OnViewport`. Auch die vorhandenen Drop-Handler
verwenden flache `QTreeView`-Enum-Namen. Bei R1 auf die Qt5-/Qt6-kompatiblen
`DropIndicatorPosition`-Werte umstellen und den tatsächlichen Drop erneut
prüfen. Diese Fehler wurden im Rahmen von U1/U2 dokumentiert, nicht behoben.

`TreeHandler.updateExportOrder` benötigt zugleich die Mitgliedschaft in
`real_layer.shapes`; eine rein optisch umgehängte Shape genügt deshalb nicht.
`domain/project/project.py` stellt Projekte nach DXF-Neuimport über Layernamen
und Shape-Zuordnungen wieder her. Deren Ladepfad muss einen Layerwechsel
ebenfalls nachvollziehen können.

- [ ] **Teil R1a – Stabilität:** den gemeldeten Drop auf einen anderen Layer
  reproduzieren und den Fehlerpfad absichern. Unzulässige/abgebrochene Drops,
  ungültige Zielindizes und Drops auf leere Bereiche dürfen nicht abstürzen
  oder das Modell teilweise verändern. Qt5 und Qt6 gezielt berücksichtigen.
- [ ] **Teil R1b – gewünschte Funktion:** gültige Shapes in einen anderen
  Bearbeitungslayer verschieben sowie Layer und Shapes innerhalb ihrer Ebene
  umordnen können. Auswahl mehrerer Shapes und eindeutige Drop-Markierung
  beim Umhängen beziehungsweise Einfügen berücksichtigen.
- [ ] Einen Anwendungsfall für die atomare Änderung von Quell-/Ziellisten,
  `parentLayer`, Reihenfolge und Planinvalidierung verwenden. Baum, Modell,
  Vorschau und Export anschließend aus demselben Zustand aktualisieren;
  Identität und Gesamtzahl der Shapes erhalten.
- [ ] **Vor R1b abstimmen:** Beim Verschieben explizite Shape-Werte behalten
  und geerbte Werte aus dem Ziel übernehmen? Das ist der Vorschlag für
  Werkzeug, Tiefe und Leads; die wirksamen Änderungen müssen erkennbar sein.
  Sonderlayer, Breaks und benutzerdefinierter G-Code benötigen klare Regeln.
- [ ] Speichern/Laden nach dem Verschieben prüfen. Ein notwendiger Ausbau
  der Projektzuordnung ist als eigener Kompatibilitätsschritt zu planen;
  bestehende `.d2g`-Versionen 1.1–1.3 bleiben lesbar. Keine unbemerkte
  Formatänderung als Nebenwirkung des GUI-Fixes.

**Abnahme und Tests:** Den Absturz mit einem realen Qt-Modell absichern;
`dxf2gcode_treeview_test.py` deckt bisher vor allem Geschwister-Reihenfolgen
ab. Danach Quell-/Ziellayer, Hin-/Zurückverschieben, Mehrfachauswahl,
Layerreihenfolge, unveränderte Identitäten/Overrides und Projekt-Roundtrip
testen. Ein Exporttest muss die neue Zuordnung tatsächlich verwenden.
R1a kann getrennt freigegeben werden; erst mit R1b ist der gewünschte
Layerwechsel vollständig erledigt.

#### R2 – Sichtbare Reihenfolge als Exportvertrag festlegen

**Codebefund:** `TreeHandler.updateExportOrder` übernimmt die Layerreihenfolge
in `layers_list` und die Shape-Reihenfolge in `exp_order` beziehungsweise
`exp_order_complete`. `MainWindow` bietet bereits getrennte Aktionen
`exportShapes` und `optimizeAndExportShapes`. `application/optimization/routes.py`
optimiert pro Layer, berücksichtigt `send_to_TSP` und ruft anschließend
`LayerContent.optimize` auf; Letzteres verändert auch Startpunkte. Eine
zusätzliche Exportoption ist daher nicht ungeprüft neu zu erfinden, sondern
zuerst gegen die vorhandenen Wege und Optimierungsmodi abzugleichen.

- [ ] Die dargestellte Reihenfolge der Bearbeitungslayer strikt abarbeiten;
  eine Optimierung darf keine Layergrenze überspringen oder Layer vertauschen.
- [ ] Innerhalb eines Layers die Shape-Reihenfolge beibehalten, außer für
  ausdrücklich zur Optimierung freigegebene Shapes bei bewusst gewählter
  Optimierung. Nicht freigegebene Shapes dürfen nicht als Nebeneffekt
  umsortiert werden; vorhandene Modi wie `TSP_shape_order` darauf prüfen.
- [ ] „Ohne Optimierung exportieren“ muss als klar erkennbare Aktion verfügbar
  sein. Sie löst weder eine neue Sortierung noch eine automatische Änderung
  der festgelegten Startpunkte aus. Exportiert wird die aktuell sichtbare
  Reihenfolge, auch wenn diese zuvor bewusst optimiert wurde.
- [ ] Routenanzeige/Live-Update von Optimierung unterscheiden. Anzeigen oder
  Exportieren allein darf die Bearbeitungsreihenfolge nicht verändern.
- [ ] GUI, CLI, Projekt-Roundtrip und tatsächliche G-Code-Sequenz verwenden
  denselben expliziten Reihenfolgevertrag. Werkzeugwechsel innerhalb eines
  Layers dürfen keine versteckte Gruppierung nach Werkzeug auslösen.

**Abnahme und Tests:** Mindestens zwei Layer mit eindeutig unterscheidbaren
Shapes und unterschiedlichen Werkzeugen verwenden. Layer und Shapes manuell
umordnen, über R1 verschieben und mit Optimierung aus/an exportieren.
Gemischte Optimierungsfreigabe und benutzerdefinierten G-Code einbeziehen;
Shape-/Werkzeugsequenzen im ausgegebenen G-Code statt nur Baumzeilen prüfen.
`dxf2gcode_tsp_optimization_test.py`, Tree- und Workflowtests erweitern.
Die Reihenfolge-Anforderungen vor einer Änderung des Optimierers präzise
festschreiben; bestehende Golden-Fälle bleiben Regressionen.

#### R4 – Ticket #157: Layer alphanumerisch sortieren

**Entfallen – ausdrücklich nicht gewünscht (30.10.2026).** Keine
alphanumerische/natürliche Layersortierung aus diesem Ticket implementieren.
Der Eintrag bleibt nur zur Dokumentation der Abgrenzung erhalten und zählt
nicht als offene Aufgabe. Die manuelle Bearbeitungs-/Exportreihenfolge aus
R1/R2 bleibt davon unberührt.

### 11. Postprozessor und Werkzeugwechsel

#### P1 – Z-Positionierung beim automatischen Werkzeugwechsel absichern

**Meldung:** Ein ATC-Profil kann zunächst Z zur Werkzeugwechselposition
fahren, das Werkzeug wechseln und erst danach mit aktiver
Werkzeuglängenkorrektur die Arbeitshöhe anfahren. Das gemeldete Beispiel
verwendet `G91 G28 Z0`, `M06 T04`, die Rückkehr zu `G90` und später
`G43 Z1. H04`. Vorgeschlagen wurde, die einmalige Z-Rückzugsbewegung hinter
den Werkzeugwechsel zu verschieben oder dort zusätzlich auszugeben.

**Codebefund:** In
`adapters/postprocessor/postprocessor.py:exportShapes` wird
`rap_pos_z(Depth_Coordinates['axis3_retract'])` einmal vor der Layer-/Shape-
Schleife ausgegeben. Innerhalb der Schleife wird bei neuer effektiver
Werkzeugnummer `chg_tool` aufgerufen. Diese Methode expandiert nur das
Profiltemplate `Program.tool_change`; eine zusätzliche Z-Positionierung
direkt nach dem Wechsel gibt es dort nicht. Der erste exportierte
Shape-Eintrag löst aktuell ebenfalls `chg_tool` aus, weil `previous_tool`
anfangs `None` ist. Die Annahme „gleiche Werkzeugnummer, deshalb beim ersten
Shape kein Wechselaufruf“ trifft im aktuellen Code somit nicht zu.

Das Standardtemplate in `postprocessorconfig.py` enthält `T%tool_nr M6`
und die Drehzahl, aber keine allgemeine ATC-/Werkzeuglängensequenz.
Beliebige Profiltemplates können zudem Position und Modalzustand verändern,
ohne dass `chg_tool` die intern geführten Z-/G90-/G91-Werte nachführt.
Das ist bei einer Lösung insbesondere für inkrementellen Export zu beachten.

- [ ] Einen reproduzierbaren Export mit dem betreffenden Maschinenprofil
  und mindestens zwei Werkzeugen erstellen; tatsächliche Ausgabe gegen die
  gewünschte Reihenfolge prüfen. Controller, Wechselmakro, H-Nummernzuordnung
  und geltende Koordinatensysteme vor Implementierung festhalten.
- [ ] Programmstart, Freifahren vor einem Werkzeugwechsel und Positionieren
  nach einem Werkzeugwechsel als getrennte Anforderungen beschreiben.
  Initiale Positionierung bleibt auch ohne weiteren Werkzeugwechsel oder
  bei leerem/manuellem Wechseltemplate sichergestellt; eine Zeile nicht
  ersatzlos in den Zweig „Werkzeugnummer geändert“ verschieben.
- [ ] Eine profilabhängige ATC-Sequenz vorsehen: Wechselposition anfahren,
  Werkzeugwechsel, benötigten Modalzustand wiederherstellen und
  Werkzeuglängenkorrektur/Positionierung passend zum Controller ausgeben.
  `G28`, `G43` und eine Zuordnung `H = T` nicht ungeprüft für alle Maschinen
  fest einbauen. Die Lage der XY-Positionierung innerhalb dieser Sequenz
  ist Teil des zu vereinbarenden Maschinenprofilvertrags.
- [ ] Festlegen, welche Höhe nach dem Wechsel gilt: globale initiale
  Rückzugshöhe, nächste Layer-/Shape-Rückzugshöhe oder eine besondere
  Profilvorgabe. Diese Höhen nicht mit Maschinen-Z-Home gleichsetzen.
- [ ] Internen Positions-/Modalzustand nach Wechselmakros eindeutig neu
  herstellen oder über einen definierten Profilvertrag aktualisieren;
  keine falschen inkrementellen Z-Differenzen aus Werten vor dem Wechsel
  berechnen. Nicht versuchen, beliebigen Makro-G-Code allgemein zu parsen.
- [ ] Werkzeugwechsel innerhalb eines Layers wegen Shape-Overrides ebenso
  behandeln wie Wechsel zwischen Layern. Wiederholte Shapes mit demselben
  Werkzeug dürfen keinen unbeabsichtigten erneuten ATC-Zyklus auslösen.
- [ ] Exportorchestrierung und Profiladapter übernehmen diese Verantwortung;
  Geometrie-/Konturplaner erhalten keine hartcodierten ATC-Befehle.
  Vorhandene Profile bleiben kompatibel. Absichtliche neue ATC-Ausgaben
  gesondert freigeben; vorhandene Golden-Ausgaben nicht pauschal ändern.

**Abnahme und Tests:** Vollständige Exportsequenzen statt nur Aufrufanzahlen
prüfen: ein Werkzeug, mehrere Shapes mit gleichem Werkzeug, Wechsel A→B→A
innerhalb eines Layers und zwischen Layern, leere/deaktivierte Layer sowie
manuelles/leeres Wechseltemplate. Ein eigenes ATC-Testprofil und Golden
decken Wechselposition, Modalzustand, H-Zuordnung und erste Bewegung nach
dem Wechsel ab; absolute und inkrementelle Ausgabe berücksichtigen.
`dxf2gcode_shape_tool_test.py` prüft Werkzeugwechsel bereits auf Aufrufebene
und kann um die ausgegebene Reihenfolge ergänzt werden. Diese Prüfungen
bewerten erzeugten Code, nicht die Freigabe für eine reale Maschine.
Analyse und Testspezifikation sind vorgemerkt; kein Exportverhalten geändert.

### 12. Schleppmesser: Konturschluss und wiederholte Schnitte

#### D1 – Kleine ungeschnittene Lücke am Start-/Endpunkt untersuchen

**Forumsbericht:** Im gezeigten Thread
[Overcut with drag knife / vinyl cutter](https://www.ltspiceusers.ch/threads/overcut-with-drag-knife-vinyl-cutter.2247/)
beschreibt Randy am 16. und 27. Juni 2026 kleine ungeschnittene Stellen beim
Konturschluss. Besonders bei Schrift lassen sich dadurch Abfallbereiche nur
schwer entfernen, ohne Buchstaben abzulösen. Als Ursache vermutet er den
Versatz der Messerspitze; genannt werden etwa 0,25 mm. Das ist eine
Nutzervermutung, noch kein nachgewiesener Fehler im aktuellen Stand.

**Codebefund:** Eine Überfahrt für geschlossene Schleppmesserkonturen ist
bereits vorhanden: `domain/toolpath/stmove.py` hängt `build_overcut`-Geometrie
an die Originalkontur an, bevor der Spitzenversatz verarbeitet wird.
`dxf2gcode_leadmove_golden_test.py` enthält `drag_knife_overcut`, ein
Funktionstest prüft zusätzlich den erfolgreichen Export. Diese Tests belegen
noch nicht, dass die physische Messerspitze am Konturschluss die gemeldete
Lücke in allen Fällen überfährt. Der ältere Forumsbericht ist mit dem
aktuellen Code und den wirksamen Einstellungen abzugleichen.

- [ ] Reproduktion mit einer kleinen geschlossenen Schrift-/Testkontur,
  Werkzeugversatz, Startausrichtung, Überfahrt und Schneidtiefe festhalten.
  Werkzeughalterbahn und tatsächliche Messerspitzenbahn unterscheiden.
- [ ] Konturschluss mit aktivierter und deaktivierter Überfahrt prüfen;
  Startorientierung, Richtung, erste kurze Linie beziehungsweise Bogen und
  Übergang vom letzten zum ersten Segment einbeziehen. Eine Mindestlänge
  größer als der Spitzenversatz nicht ungeprüft als allgemeine Lösung setzen.
- [ ] Bestehende Überfahrt bei Bedarf gezielt korrigieren. Ein neues
  Wiederholungsmerkmal aus D2 darf einen Fehler des Konturschlusses nicht
  lediglich verdecken. Keine pauschale Änderung anderer Maschinenmodi.

**Abnahme und Tests:** Spitzenbahn am Anfang und Ende sowie tatsächlich
abgedeckte Schnittstrecke geometrisch prüfen, nicht nur nicht leeren G-Code.
Geschlossene Linien-/Bogenkonturen, kurze Anfangssegmente und beide
Umlaufrichtungen testen; bestehende Schleppmesser-Goldens vergleichen.
Praktische Schnittqualität erfordert danach einen gesonderten Materialtest;
ein solcher ist mit diesem TODO nicht durchgeführt oder freigegeben.

#### D2 – Optional zweimal um dieselbe Kontur ohne Anheben dazwischen

**Gewünschte Erweiterung aus dem Bericht:** Jede geschlossene Kontur zweimal
durchfahren, ohne am Übergang zwischen den Umläufen das Messer zurückzuziehen.
Die vorhandenen Eckenschleifen und Spitzenversatzkorrekturen müssen erhalten
bleiben. Der Nutzer nennt alternativ einen ersten flacheren Schnitt und
danach einen Schnitt auf Endtiefe; gewöhnliche Fräspässe ersetzen den
Schleppmesserablauf wegen der fehlenden Eckenschleifen nicht.

**Codebefund:** `DragKnifeStrategy` in
`domain/toolpath/strategies/drag_knife.py` verarbeitet die vorbereitete Bahn
einmal und hängt danach den Rückzug an. Eine eigene Einstellung für mehrere
zusammenhängende Umläufe ist dort nicht vorhanden. `slice_depth` dient im
Schleppmessermodus bereits als Schwenktiefe an Ecken; dieser Parameter darf
nicht stillschweigend zur Tiefe eines ersten Schnittumlaufs umgedeutet werden.

- [ ] Vor Umsetzung den gewünschten Modus festlegen: zweimal dieselbe
  Endtiefe oder erste Teilzustellung und danach Endtiefe. Eine frei wählbare
  Anzahl Umläufe wäre eine weitere Erweiterung, keine bereits beschlossene
  Anforderung. Standardverhalten bleibt zunächst ein Umlauf.
- [ ] Den Übergang zwischen den Umläufen kontinuierlich planen, einschließlich
  Messerorientierung und Eckenkorrektur an der Schließstelle. Anfahrt,
  anfängliche Rampe und abschließenden Rückzug nicht einfach mitduplizieren.
- [ ] „Ohne Anheben“ am Umlaufwechsel von den vorhandenen Z-Korrekturen bei
  Messerschwenks unterscheiden. Vor Umsetzung ausdrücklich abstimmen, ob
  diese Eckenkorrekturen unverändert bleiben sollen; die positiv bewerteten
  Eckenschleifen dürfen nicht durch einen normalen Fräspfad ersetzt werden.
- [ ] Kombination mit Überfahrt aus D1, offenen Konturen und Rampe vorab
  definieren. Vorschlag: zunächst nur geschlossene Konturen; eine Überfahrt
  erst am Ende des letzten Umlaufs. Vorschlag ist noch freizugeben.
- [ ] Einstellung, Projektpersistenz und GUI-Anzeige gemeinsam planen;
  neue Texte in Deutsch, Französisch und Russisch pflegen. Wiederholungen
  als semantischen Ablauf planen, damit Vorschau und Export denselben Plan
  verwenden. Keine bloße Verdoppelung des fertigen G-Code-Texts.

**Abnahme und Tests:** Anzahl und Tiefe der Umläufe, korrekten Nahtübergang,
fehlenden Zwischenrückzug, erhaltene Eckenschleifen und genau einen
abschließenden Rückzug im Plan prüfen. G-Code und 3D-Projektion verwenden
dieselben Z-Bewegungen; 2D darf deckungsgleiche XY-Bahnen weiterhin einmal
darstellen. Unveränderten Ein-Umlauf-Modus sowie Roundtrip der neuen Option
absichern. D1/D2 sind vorgemerkt, noch nicht umgesetzt oder neu getestet.

### 13. Versions- und Build-Metadaten

#### Ziel, Vertrag und implementierter Stand

Paketversion und Herkunft sind getrennte Angaben. Die Paketversion aus
`_version.py` ist eine bewusste Release-Entscheidung. Ein Commit aktualisiert
die Herkunftsanzeige beim nächsten Lesen, erhöht aber weder die Release-Version
noch erzeugt er ein neues Wheel oder eine neue EXE/MSI.

- [x] `bootstrap/version_metadata.py` ermittelt Paketversion, Revision,
  Quellbranch, Commit-Datum und lokale Änderungen. Die Anzeige kürzt die
  Revision und trennt Commit- und Build-Datum von Python-/Qt-Versionen.
- [x] Beim Quellstart nur den eindeutig erkannten Projekt-Checkout lesend
  abfragen. Git-Abfragen haben ein Zeitlimit, festes Arbeitsverzeichnis und
  verändern den Index nicht; fremde übergeordnete Repositorys werden nicht
  als Herkunft verwendet.
- [x] Nach Commit oder Branchwechsel die Herkunft beim nächsten Start bzw.
  Öffnen des Infofensters neu lesen. Detached HEAD gesondert darstellen;
  fehlende Herkunft ausdrücklich anzeigen, statt ein altes Datum als
  aktuellen Stand auszugeben. Bei lokalen Änderungen bleibt das Commit-Datum
  das Datum des letzten Commits; der Status kennzeichnet die Abweichung.
- [x] Installierte Pakete und eingefrorene Anwendungen lesen
  `dxf2gcode/_build_metadata.json` ohne Git. Deren Branch bezeichnet die
  Build-Quelle, keinen lokalen Branch auf dem Rechner des Endnutzers.
- [x] `tools/build/setuptools_commands.py` erzeugt die Metadatendatei nur
  im Build-Verzeichnis beziehungsweise Quellarchiv. Ein Wheel daraus
  übernimmt Revision, Branch, Status und Zeitstempel unverändert.
- [x] `tools/build/windows.py` bindet entsprechende Metadaten in EXE/MSI
  ein. Die Datei wird nicht in den Quellcheckout geschrieben oder als
  Quelländerung eingecheckt. `SOURCE_DATE_EPOCH` ermöglicht reproduzierbare
  Build-Zeitstempel.
- [x] Infofenster und G-Code-Kopf verwenden Paketversion und bekannte Herkunft.
  Die Bewegungsbefehle ändern sich durch die Herkunftsanzeige nicht.
  Beschriftungen in Deutsch, Französisch und Russisch sind implementiert.
- [x] Alte Perl-Keywordfilter, Attributzuordnung, Keyword-Anleitung und lokale
  Filterkonfiguration entfernen. Ein Commit-/Post-Commit-Hook ist für den
  neuen Ablauf nicht nötig; weder Push noch erneuter Checkout sind zur
  Aktualisierung der Herkunftsanzeige im Quellstart erforderlich.

Der Status wurde bei der Zusammenführung anhand des vorhandenen Providers,
der Build-Anbindungen und der fokussierten Tests abgeglichen. Er bedeutet
keine neue Abnahme eines vollständig gebauten oder auf Debian installierten
Pakets.

#### Vorhandene fokussierte Prüfungen

`tests/dxf2gcode_version_metadata_test.py` deckt saubere/geänderte Checkouts,
neue Commits, Branchwechsel, Detached HEAD, fehlendes/fehlerhaftes Git,
ungültige oder zur Version unpassende Metadaten, Paketressourcen ohne Git
und die Übernahme aus Quellarchiven ab. Fremde umgebende Repositorys dürfen
keine Herkunft liefern. Ein frisch erzeugter Build-Baum darf den zuvor
erfassten Quellstatus nicht nachträglich als geändert markieren.

Die Setuptools-/MSI-Anbindung wird außerdem mit kleinen Build-Bäumen und
ersetztem Setup-Aufruf geprüft. Kompilierte Kataloge und das Infofenster
wurden fokussiert geprüft; Beschriftungen unterscheiden fehlende Herkunft
von fehlendem aktivem Branch und behandeln Anzeigenamen als Text.
Diese Angaben übernehmen den bisherigen dokumentierten Prüfstand; bei der
Dokumentzusammenführung wurden die Anwendungstests nicht neu ausgeführt.

#### M1 – Noch offene Paket-/Debian-Abnahme

- [ ] Nach gesonderter Freigabe ein aktuelles Wheel/Quellarchiv und die
  Windows-Artefakte bauen und ihre mitgelieferten Metadaten prüfen.
- [ ] Wheel aus dem Quellarchiv ohne Git bauen; Herkunft und Zeitstempel
  müssen aus dem Archiv stammen. Installierte Anwendung ohne Git starten.
- [ ] Das freigegebene Wheel im isolierten Debian-Testworkflow prüfen:
  Infofenster zeigt die Paketversion und Build-Herkunft des tatsächlich
  installierten Artefakts, nicht einen vorherigen Quellstand oder den
  lokalen Branch der VM. Ergebnisse einschließlich Paketidentität festhalten.
- [ ] Paket-/Quellstart und G-Code-Kopf gegen dieselbe Herkunft abgleichen;
  Bewegungsausgabe bleibt gegenüber den bestehenden Golden-Fällen erhalten.

**Freigabegrenze:** M1 ist vorgemerkt, nicht mit der Dokumentbereinigung
beauftragt. Vollständige Release-/MSI-Builds, Debian-/SSH-Läufe und Änderungen
an installierten Testumgebungen erfolgen erst auf ausdrücklichen Auftrag
oder nach angenommenem konkretem Vorschlag.

#### Historischer Befund und Grund für den Wechsel

Vor der Umstellung am 30.10.2026 verwendete das Infofenster
`domain/constants.py`: `VERSION` enthielt nur Python/PyQt; `DATE`, `REVISION`
und `AUTHOR` kamen aus expandierten Git-Keywords. Die Paketversion fehlte
in dieser Anzeige. Deshalb konnte selbst ein Wheel mit Version `20261030`
noch den 11. Oktober als vermeintlich aktuellen Stand anzeigen.

Die damalige `.gitattributes` ordnete `*constants.py` dem lokalen
`rcs-keywords`-Filter zu. `clean` entfernte Expansionen beim Übernehmen in
den Index, etwa durch `git add`; `smudge` expandierte beim Schreiben aus Git
ins Arbeitsverzeichnis, etwa beim Checkout. Commit und Push aktualisierten
die expandierten Arbeitsdateien nicht automatisch. Der Filter las zudem
`HEAD` über `git log` und belegte damit keine unveränderliche Herkunft eines
später gebauten Pakets. Hintergrund:
[Git-Dokumentation zu Attributfiltern](https://git-scm.com/docs/gitattributes).
Dieser Abschnitt beschreibt den entfernten Mechanismus, keinen weiterhin
erforderlichen Einrichtungsschritt.

Der ursprüngliche Metadatenplan bestand aus Provider, gemeinsamer Herkunft
für Wheel/Quellarchiv/MSI, umgestellter und übersetzter Anzeige, Entfernung
der Keywords sowie Checkout-/Buildtests. Diese lokalen Schritte sind oben
als umgesetzt erfasst; seine abschließende Paket-/Debian-Prüfung bleibt M1.

### 14. Importqualität und Layerfilter – weitere Wünsche aus Ticket #157

Diese Punkte erfassen die übrigen Wünsche aus
[Ticket #157](https://sourceforge.net/p/dxf2gcode/tickets/157/), einschließlich
des ergänzenden Kommentars. I2 ist zusätzlich zur Startzustandsoption
umgesetzt; I1 wurde ausdrücklich ausgeschlossen.

#### I1 – Zu kurze Segmente in der Vorschau markieren

**Entfallen – ausdrücklich nicht gewünscht (30.10.2026).** Das Merkmal
„Too short segments highlighting“ aus dem Ticket wird nicht umgesetzt und
zählt nicht als offene Aufgabe. Bestehende Geometrievalidierung und andere
Diagnosen werden dadurch nicht entfernt oder geändert.

#### I2 – Layer 0 und IGNORE-Layer optional vom Import ausschließen

**Status: umgesetzt.** `BuildDrawingModel` filtert vor der Shape-Erzeugung,
sodass ausgeschlossene Layer und Shapes weder im Bearbeitungsmodell noch
im Entities-/Layerbaum, in Vorschau oder Export auftauchen. Die Rohdaten
werden weiterhin gelesen, etwa für Blockreferenzen; das ist kein zweites
Bearbeitungsmodell. Ohne aktivierte Filter bleibt das bisherige Verhalten
erhalten: IGNORE-Shapes werden importiert und standardmäßig deaktiviert.

- [x] Den ergänzenden Ticketwunsch „Do NOT import IGNORE ... Layers“ als
  eigene Konfigurationsoption „IGNORE-Layer nicht importieren“ umsetzen.
  Bei aktivem Filter sollen betroffene Layer und Shapes tatsächlich nicht
  ins importierte Bearbeitungsmodell aufgenommen werden; bloßes Deaktivieren
  oder Überspringen beim Export erfüllt die Anforderung nicht.
- [x] Die optionale Behandlung von Layer `0` davon unabhängig halten, damit
  beide Filter getrennt wählbar bleiben.
- [x] Gemäß Nutzerfestlegung beide Filter standardmäßig ausschalten:
  `Import_Parameters.exclude_ignore_layers=False` und
  `Import_Parameters.exclude_layer_zero=False`. Neue Konfigurationen und
  unterstützte ältere Profile ohne Schlüssel übernehmen diese Werte.
  Schema 9.16 bleibt mit 9.11–9.15 kompatibel.
- [x] Namensregel mit der bestehenden Deaktivierung gemeinsam verwenden:
  `IGNORE` plus konfiguriertes `id_float_separator`, normalerweise `IGNORE:`;
  Groß-/Kleinschreibung bleibt relevant. `IGNORED:` oder `ignore:` werden
  nicht zusätzlich ausgeschlossen. Layer `0` wird anhand seines Namens,
  nicht anhand seiner internen Nummer erkannt.
- [x] BLOCK/INSERT-Zuordnung berücksichtigen. Die vorhandene Option
  `insert_at_block_layer` entscheidet weiterhin über die Zuordnung von
  Blockinhalten. Ist sie aktiv, bleiben Inhalte auf Layer `0` in einem
  regulären INSERT erhalten; bei aktivem Layer-0-Filter erben auch verschachtelte
  INSERTs auf `0` die äußere Zuordnung. Ein INSERT auf einem ausgeschlossenen
  Layer wird mit seinem Inhalt ausgelassen; leere gefilterte Blockknoten
  werden nicht im Baum belassen.
- [x] Importdiagnosen, Geometriezuordnung, Projektladen und Filterwirkung
  abstimmen. Bestehende Projekte dürfen keine unbemerkten fehlenden
  Shape-Referenzen bekommen; Konfigurations-/GUI-Texte in allen Sprachen pflegen.

**Bedienung und Geltungsbereich:** Die Anwendungskonfiguration bietet
„IGNORE-Layer nicht importieren“ und „Layer 0 nicht importieren“. Die Optionen
wirken beim nächsten Aufbau aus der DXF-Datei, auch beim Projektladen,
und gelten für GUI und CLI. Sie gehören zum aktiven Konfigurationsprofil;
die `.d2g`-Version und das Speicherformat werden nicht geändert. Ausgeschlossene
Layernamen werden als strukturierte `DrawingModel.excluded_layers` und im
übersetzten Importprotokoll ausgegeben. Die verbleibenden Shapes erhalten
zusammenhängende Nummern und konsistente Layer-/Entity-Zuordnungen.

**Prüfung am 30.10.2026:** Zwölf Importfiltertests, sechs Konfigurations-/
Übersetzungstests und der erweiterte MainWindow-Workflow bestehen mit Qt5
und Qt6. Abgedeckt sind beide Filter unabhängig/an/aus, Namensregeln,
Blockzuordnung einschließlich verschachtelter INSERTs, Shape-Callbacks und
Nummerierung, echter DXF→G-Code-Export sowie Laden und erneutes Speichern von
Projekten 1.1–1.3 bei aktiven Filtern. Der GUI-Test prüft Layerbaum, Vorschau
und eine vollständig weggefilterte Zeichnung. DE-/FR-/RU-Texte und QM-Dateien
sind aktualisiert und mit echten Translatoren geprüft.

Dabei wurde eine fehlende Bounding-Box einfacher importierter Shapes sichtbar,
wenn die Vorschau direkt den semantischen Plan verwendet. Der Modellaufbau
berechnet die Bounding-Box jetzt unabhängig vom Zeichnen; die GUI-Regression
mit der realen Linien-DXF deckt diesen Fall ab.

Zusätzlich bestehen die fokussierten Import-, Projektadapter-, Projekt-Lead-,
Anwendungs-/Importgrenzen- und Workflowtests. Alle 18 bestehenden
Golden-G-Code-Fälle bleiben bytegleich. Keine Vollsuite, Release-/MSI-Builds
oder Debian-Läufe ausgeführt; keine Pakete installiert.

## Zurückgestellte Erweiterung: mehrere Konturen einer Operation

**Priorität:** nach den laufenden Refactoring-Abschnitten. Jetzt bei
Architekturentscheidungen berücksichtigen; noch keine Funktion implementieren.

Wenn eine Pocket- oder Shape-Operation zwei oder mehr getrennte Inseln bzw.
Bearbeitungskonturen erzeugt, sollen diese einzeln behandelt werden können:

- [ ] Lead-in, Lead-out und Overcut je entstandener Teilkontur unabhängig
  planen und einstellen können.
- [ ] Die Startpunkte dieser Teilkonturen in der GUI einzeln auswählen und
  festlegen können, auch wenn sie zur selben ursprünglichen Shape bzw.
  Operation gehören.
- [ ] Die Zuordnung der Startpunkte und Einstellungen zu den Teilkonturen bei
  Neuberechnung sowie Speichern/Laden eines Projekts nachvollziehbar erhalten;
  das genaue Zuordnungs- und Speicherverfahren später ausarbeiten.
- [ ] Vorschau und Export verwenden dieselben Teilkonturen samt ihren
  Startpunkten, Leads und Overcuts. Mehrere Tiefenpässe und Verbindungsbewegungen
  dürfen diese Zuordnung nicht vermischen.

**Architekturleitlinie:** Ursprungs-Shape, Operation, resultierende Teilkontur
und Tiefenpass müssen unterscheidbar bleiben. Datenmodell und Schnittstellen
dürfen nicht dauerhaft genau einen Startpunkt oder genau ein Lead-/Overcut-Paar
pro Shape voraussetzen. Identifizierbare Teilkonturen müssen später als
Untergliederung eines Werkzeugwegplans ergänzt werden können. Die konkrete
Modellierung und GUI-Bedienung werden erst beim Aufgreifen dieser Erweiterung
entschieden; sie ist kein Abnahmetor für das aktuelle Refactoring.

## Zurückgestelltes Bedienkonzept R3: Geometrie und Bearbeitung trennen

**Vorschlag zur Diskussion, noch keine Architekturentscheidung:** Importierte
DXF-Layer beschreiben die Zeichnung; die gewünschte CNC-Bearbeitung beschreibt
eine davon unabhängige Reihenfolge von Arbeitsgängen. Diese Aufgaben sollten
langfristig getrennt sichtbar sein, statt weitere Bedeutung in denselben
Layerbegriff zu packen.

```text
Geometrie                         Bearbeitung (Export von oben nach unten)
  DXF-Layer / Entities             1. Taschen – Werkzeug 2
    Originalkonturen                  Operation → referenzierte Kontur(en)
                                   2. Innenkonturen – Werkzeug 1
                                      Operation → referenzierte Kontur(en)
                                   3. Außenkonturen – Werkzeug 1
                                      Operation → referenzierte Kontur(en)
```

- [ ] Einen Tab „Geometrie“ für Herkunft, Sichtbarkeit und Auswahl sowie einen
  Tab „Bearbeitung“ für geordnete Gruppen/Operationen entwerfen. Die Auswahl
  in Baum und Vorschau bleibt gekoppelt. Die ursprüngliche DXF-Zuordnung
  bleibt als Herkunft erhalten, auch wenn Arbeitsgänge umsortiert werden.
- [ ] Bearbeitungsgruppen anlegen/benennen, Werkzeug und Vorgaben zuweisen,
  Operationen per Drag-and-drop umsortieren oder in andere Gruppen verschieben.
  Zusätzliche Aktionen „Nach oben/unten“ und „In Gruppe verschieben …“ machen
  die Planung auch ohne präzises Ziehen bedienbar.
- [ ] Dieselbe Originalkontur über explizit angelegte Referenzen später in
  mehreren Arbeitsgängen nutzen können, etwa Tasche und anschließendes
  Schlichten. B1 gilt je Operation; zwei getrennte Operationen dürfen dieselbe
  Geometrie unterschiedlich bearbeiten. Verschieben und bewusstes Erzeugen
  einer weiteren Operation müssen in der Bedienung unterscheidbar sein.
- [ ] Jede Operation besitzt eine stabile Identität und klare effektive
  Werkzeug-/Bearbeitungswerte. Entstehende Teilkonturen können später eigene
  Startpunkte und Leads erhalten, wie im vorherigen Abschnitt beschrieben;
  Tiefenpässe sind keine separat zu sortierenden Geometrieobjekte.
- [ ] Reihenfolge und Optimierungsfreigabe im Bearbeitungsbaum sichtbar halten.
  Optimierung erfolgt innerhalb ausdrücklich freigegebener Grenzen und
  verändert niemals die fachlich geplante Gruppenreihenfolge.
- [ ] Projektpersistenz und Übernahme bestehender Layerprojekte gesondert
  planen. **Offene Entscheidung:** zunächst eine Bearbeitungsgruppe je
  bestehendem Layer als verlustfreie Ausgangssicht? Speicherformat und
  Kompatibilitätsweg vor Implementierung klären.

**Empfohlener Weg:** R1a zuerst unabhängig vom neuen Baum lösen; R1b/R2 mit
expliziten Anwendungsaktionen und einem dokumentierten Reihenfolgevertrag
umsetzen. Danach R3 mit Bedienabläufen und Modell-/Speicherentwurf zur
Freigabe vorlegen. So wird die aktuelle Oberfläche benutzbar, ohne neue
Fachregeln dauerhaft in `QStandardItem`-Zeilen oder DXF-Layern zu verankern.
R3 bleibt ebenso wie die Teilkontur-Erweiterung zunächst zurückgestellt.

## Teststrategie für die neuen Aufgaben

Tests werden bei der später freigegebenen Umsetzung passend zum Risiko
festgelegt; in dieser Untersuchung werden nur die Prüffälle vorgemerkt.

- Reproduzierbare Abstürze, ungültige Bearbeitungszustände, falsche
  Zuordnungen und Export-/Speicherfehler erhalten automatische Regressionen.
  Der Test soll das beobachtbare Verhalten prüfen und vor dem Fix den Fehler
  nachweisen. Fachregeln möglichst ohne Qt testen; Signal-/Modellzusammenspiel
  zusätzlich mit wenigen fokussierten Qt-Workflows absichern.
- Vorhandene Tests erweitern, wenn sie denselben Vertrag abdecken. Ein neuer
  Test ist sinnvoll, wenn eine bislang ungesicherte Regel oder Fehlerursache
  geprüft wird; reine Wiederholungen der Implementierung vermeiden.
- Neue Konfigurationsoptionen über Vorgaben, Persistenz und Wirkung testen;
  Übersetzungen mit tatsächlichem Kontext und geladenem Katalog prüfen.
- Kleine Layoutänderungen primär gezielt visuell prüfen. Keine fragilen
  Pixeltests nur für Abstände; Zustandslogik wie bei den Baum-Buttons ist
  dagegen sinnvoll automatisch prüfbar.
- Bei Exportänderungen Planinhalt, Reihenfolge und relevante Golden-Ausgaben
  vergleichen. Tests verringern das Wiederholungsrisiko; sie garantieren nicht
  die Abwesenheit aller denkbaren Fehler oder Plattformunterschiede.
- Zunächst schnelle lokale Prüfungen des freigegebenen Teilbereichs.
  Vollständige Suite, Debian-/SSH-Läufe und Release-/MSI-Builds nur auf
  ausdrücklichen Auftrag oder nach angenommenem konkretem Vorschlag.

## Abnahmetore

- [ ] Planer, Geometrieberechnung, Vorschau und Formatierung sind getrennt
  testbar; Geometrieklassen kennen keinen Postprocessor oder G-Code.
- [ ] Pro migrierter Scheibe bestehen fokussierte Verhaltenstests und die
  zugehörigen Golden-Ausgaben bleiben bytegleich.
- [ ] Nach Abschluss der Migration besteht
  `python tests/run_tests.py full`.
- [ ] GUI-, CLI-, 2D- und 3D-Ausgabe verwenden nachweislich denselben
  unveränderlichen Plan.
- [ ] 2D vermeidet deckungsgleiche Wiederholungen; 3D behält die
  Tiefenausdehnung und verwendet für Pass-Ebenen ausschließlich Plandaten.
- [ ] Softwareoffsets sind geometrisch enthalten; Maschinenoffsets erscheinen
  als explizite Zustände zur programmierten Kontur. Beide Darstellungen
  bleiben unterscheidbar.
- [ ] Unterstützte und nicht unterstützte Maschinen-/Kompensationskombinationen
  sind explizit getestet; fachliche Änderungen sind separat begründet und
  geprüft. Die unveränderten bestehenden Golden-Fälle bleiben bytegleich.
- [ ] Importgrenzen belegen, dass Domain und Application keine Qt-,
  Postprocessor- oder globalen Laufzeitabhängigkeiten einführen.
- [ ] Es gibt keine aktive Shape-basierte G-Code-Planung mehr und keine
  doppelte Berechnung von Passfolge, Tabs, Leads oder Pocket-Bahnen.

## Historische Ausgangslage und ursprüngliche Etappen

Die folgenden Angaben bewahren den Kontext des ursprünglichen
Werkzeugwegplans. **Alte Pfade und Methoden sind keine aktuellen Zielpfade
und sollen nicht wiederhergestellt werden.** Der aktuelle Aufgabenstatus
steht in den Abschnitten 1–14.

### Damalige Kopplungen

- `core/stmove.py` erzeugte Anfahr-/Offsetgeometrie und Pocket-Bahnen in
  derselben veränderlichen Sammlung und enthielt Vorschau-Zeichenlogik.
- `core/shape.py:Write_GCode()` wählte Software-/Maschinenkompensation,
  Tiefenpässe, Richtungsumkehr, Tabs, Leads und Rückzüge; Schleppmesser
  verwendeten einen eigenen Exportpfad.
- `core/linegeo.py` und `core/arcgeo.py` formatierten durch direkte
  Postprocessor-Aufrufe ihre Bewegungen selbst.
- `core/pocketmill.py` las StMove-Zustand und hängte Pocketgeometrie an
  dessen Liste. `postpro/postprocessor.py` orchestrierte Layer/Shapes und
  formatierte gleichzeitig Steuerungsbefehle.
- Maschinenart, Kompensationsverantwortung und G40-/G41-/G42-Richtung
  wirkten über mehrere dieser Module hinweg.
- Die Vorschau zeigte nur Teile des Weges. Export expandierte Tiefenpässe,
  kehrte offene Konturen um, wählte Tabs pro Pass und erzeugte eigene
  Zustellungen/Rückzüge. Diese Mehrfachberechnung motivierte die gemeinsame
  Planquelle und getrennte 2D-/3D-Projektionen.

### Zuordnung der früheren Etappen zur heutigen Liste

Die frühere Nummerierung wird hier ausschließlich erklärt; für neue Aufträge
gelten die Abschnittsnummern dieses Dokuments.

| Frühere Etappe | Inhalt und heutige Zuordnung |
| --- | --- |
| 0 – Verhaltensmatrix | Vor Änderungen gültige Maschinenarten, Software-/Maschinenkompensation, G40/G41/G42, offene/geschlossene Konturen, Tiefenpässe, Tabs, Leads, Überfahrt, Pocket-Richtung und Postprocessor-Regeln festhalten; heute Abschnitt 1 und die Fallmatrix in Abschnitt 3 |
| 1 – Plan-Datenmodell | Qt-/Postprocessor-freie Pässe/Aktionen zunächst aus bestehenden StMove-Geometrien gewinnen, ohne gleichzeitig Algorithmen umzuschreiben; heutiger Stand und Abschnitte 1/2 |
| 2 – Shape-Ausgabe entkoppeln | Orchestrierung aus `Shape.Write_GCode()` verlagern; mit einfachem Fräsen beginnen, dann Kompensation, Mehrfachpässe und offene Konturen; heute Abschnitte 2–4 |
| 3 – Vorschau anbinden | Gemeinsame Bewegungs-/Passdaten, 2D ohne Mehrfachlinien, 3D mit Z, keine eigene Tab-/Lead-out-Planung; heute Abschnitt 5 |
| 4 – Geometrie aus StMove lösen | Offset, Leads, Pocket und Messerspitzenweg in explizite Geometriefunktionen/Planer verschieben; StMove nur während der Migration adaptieren und erst nach Migration seiner Aufrufer entfernen/umbenennen; heute Abschnitte 3/5/6 |
| 5 – Strategien/Randfälle | Drehmaschine, Schleppmesser, Postprocessor-Fähigkeiten und gültige Pocket-/Kompensationsfälle vervollständigen; Gültigkeitsgrenzen zentral prüfen; heute Abschnitte 1/3/4/6 |
| 6 – Alte Kopplungen entfernen | Direkte Geometrieausgabe, doppelte Pass-/Tab-/Lead-Berechnung und globale Zustandszugriffe nach Umstellung der Aufrufer entfernen; heute Abschnitt 6 und Abnahmetore |

Als frühe Verhaltensbasis waren 644 Tests und 73 % Gesamtabdeckung
dokumentiert. Diese historischen Zahlen sind weder der aktuelle Stand noch
ein Ersatz für gezielte Verhaltenstests. Die späteren Ergebnisse nach
Abschnitt 2 sind separat unten erhalten. Die alte Arbeitsregel sah eine
Vollsuite nach jeder Etappe vor; gemäß der späteren Nutzerfestlegung gelten
jetzt fokussierte lokale Prüfungen und eine gesonderte Freigabe für lange
Läufe. Das abschließende Vollsuite-Abnahmetor bleibt bestehen.

## Prüfstand nach Abschnitt 2

Historischer Prüfstand des damaligen Abschnittsabschlusses; diese Läufe
wurden bei der Untersuchung vom 30.10.2026 nicht erneut ausgeführt.

- Gezielte Lead-, Diagnose-, Planvertrag- und Golden-G-Code-Regressionen: 151 Tests
  bestanden.
- Vollständige Suite über `python tests/run_tests.py full`: 706 Tests
  bestanden; alle 18 bestehenden Golden-G-Code-Fälle bestehen unverändert.
- Grenztests importieren den neuen Domain-Planer ohne Qt oder globale
  Laufzeitvariablen. Vertragstests prüfen wiederholbare Planung, unveränderte
  Eingaben und das Ausbleiben sämtlicher Postprocessor-Bewegungsaufrufe.
- Qt-Projektmetadaten enthalten die neuen Dateien und keine entfernten
  Module. Diagnoseübersetzungen sind in Deutsch, Französisch und Russisch
  vorhanden, kompiliert und geprüft.
- Abschnitt 1 (Verhalten und Planvertrag), Abschnitt 2 (reine
  Planungsstrategien) und Abschnitt 5a (Werkzeugänderung pro Shape) sind
  abgeschlossen. Die fachliche Fallmatrix in Abschnitt 3 und die weitere
  Geometrie-/Vorschauentkopplung bleiben offen.

## Arbeitsweise

Arbeiten in kleinen, reviewbaren Scheiben ausführen. Für jede Scheibe zuerst
die bisherigen Ergebnisse durch Tests festhalten, dann Planung und Ausgabe
umstellen und erst nach bestandenem Abnahmetor mit der nächsten Scheibe
beginnen. Absichtliche Änderungen am G-Code-Verhalten benötigen eine eigene
fachliche Begründung und dürfen nicht als Nebeneffekt der Strukturmigration
einfließen.

Geometrieausgabe und Geometriealgorithmen nicht gleichzeitig ändern, wenn
sich ihre Effekte nicht getrennt validieren lassen. Bestehende G-Code-Ausgabe
bleibt Verhaltensvertrag, bis eine Änderung ausdrücklich beschlossen ist.
Keine großflächigen Umbenennungen/Verzeichnisverschiebungen als ersten Schritt
einer fachlichen Scheibe; entfernte alte Importpfade nicht wieder einführen.
Die lokalen Prüfungen ersetzen nicht die abschließende Gesamtprüfung. Lange
Prüfungen werden nach der Freigaberegel der Teststrategie eingeplant.
