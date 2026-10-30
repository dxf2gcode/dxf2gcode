# Werkzeugweg-Refactoring: offene Arbeiten

Diese Liste konkretisiert die noch offenen Arbeiten am Werkzeugweg. Sie ist
mit dem Zielplan in [toolpath-refactoring-plan.md](toolpath-refactoring-plan.md)
abgestimmt. Der semantische `ToolpathPlan`, der Exportpfad und die Vorschau-
Anbindung sind vorhanden. Die Planerzeugung verwendet reine Strategien und
explizite Eingaben. Vorbereitete Geometrie und Teile der Vorschau verwenden
weiterhin bestehende Algorithmen; deren vollständige Entkopplung bleibt offen.

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
- [ ] Pocketmilling einschließlich `always_inward` und
  `selected_direction`.
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

## Abnahmetore

- [ ] Pro migrierter Scheibe bestehen fokussierte Verhaltenstests und die
  zugehörigen Golden-Ausgaben bleiben bytegleich.
- [ ] Nach Abschluss der Migration besteht
  `python tests/run_tests.py full`.
- [ ] GUI-, CLI-, 2D- und 3D-Ausgabe verwenden nachweislich denselben
  unveränderlichen Plan.
- [ ] Importgrenzen belegen, dass Domain und Application keine Qt-,
  Postprocessor- oder globalen Laufzeitabhängigkeiten einführen.
- [ ] Es gibt keine aktive Shape-basierte G-Code-Planung mehr und keine
  doppelte Berechnung von Passfolge, Tabs, Leads oder Pocket-Bahnen.

## Prüfstand nach Abschnitt 2

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
