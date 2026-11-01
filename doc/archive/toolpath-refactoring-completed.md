# DXF2GCODE: abgeschlossene Arbeiten und Prüfergebnisse

Stand der Dokumentbereinigung: **31.10.2026**.

Dieses Dokument bewahrt abgeschlossene Implementierungen, deren dokumentierte
Prüfergebnisse und die historische Ausgangslage. Die
[aktive Todo](../todo.md) enthält die verbleibenden Aufgaben
in empfohlener Umsetzungsreihenfolge. Die Trennung ändert keinen fachlichen
Status und ist keine erneute Codeprüfung oder Testfreigabe.

Historische Testergebnisse gelten für den jeweils beschriebenen Stand.
Insbesondere liegen die Vollsuite-Ergebnisse mit 775 Tests vor der späteren
Darstellungskorrektur; diese wurde anschließend mit jeweils 21 gezielten
Tests unter Qt5 und Qt6 abgesichert. Daraus folgt keine neue Paketabnahme.

## Überblick

| Abgeschlossen | Inhalt |
| --- | --- |
| Werkzeugweg-Etappen 1–6 | Planvertrag, native Strategien, Fallmatrix, Profilformatierung, gemeinsame Werkzeugwegvorschau und Entkopplung |
| Etappe 5a | Shape-spezifische Werkzeugzuordnung einschließlich Persistenz und Anzeige |
| Darstellungskorrektur | Originalgeometrie bleibt Grunddarstellung und Auswahlfläche; Werkzeugweg erscheint zusätzlich bei Auswahl in den bestehenden Farben |
| Importreihenfolge | Rückwärts importierte Kurvenketten behalten die korrekte Reihenfolge ihrer Teilstücke; rote Kontur und G40-Plan sind zusammenhängend |
| U1 / U2 | Werkzeugauswahl ausrichten; Klappbuttons nach Baumzustand und Hänger-Nachbesserung |
| U4 / I2 | Konfigurierbarer Startzustand des Layerbaums; optionale Importfilter |
| R1a | Drag-and-drop-Absturzpfade und Qt5-/Qt6-Kompatibilität |
| R2 | Sichtbare Exportreihenfolge, Treeview-Synchronisierung und gemeinsame GUI-/CLI-Optimierungsmodi |
| K3 | Vierstellige Längeneingabe und Erhaltung genauer Originalwerte bis zur bewussten Bearbeitung; Profilformatierung bleibt maßgeblich |
| B1 / B2 | Gemeinsame Bearbeitungszustände, sichtbare Konflikte alter Projekte und korrekte Geometrieprüfung für Bohren/Pocketing |
| Versionsmetadaten | Provider, Build-Anbindung, Infofenster/G-Code-Kopf und Entfernung der alten Keywords; Paketabnahme M1 bleibt offen |
| Bereinigung | `.kilo/` und erzeugte `.coverage` entfernt |

Die weiterhin geltenden [Architekturverträge](../architecture.md#weitergeltende-architekturverträge)
stehen in der aktuellen Architekturdokumentation. Dieses Archiv bewahrt
Umsetzungshistorie und damalige Prüfergebnisse.

<a id="r2"></a>

## Abgeschlossener Exportreihenfolgevertrag

### R2 – Sichtbare Reihenfolge als Exportvertrag festlegen

**Codebefund:** `TreeHandler.updateExportOrder` übernimmt die Layerreihenfolge
in `layers_list` und die Shape-Reihenfolge in `exp_order` beziehungsweise
`exp_order_complete`, auch beim manuellen Umordnen ohne Routen-Live-Update.
`MainWindow` bietet getrennte Aktionen
`exportShapes` und `optimizeAndExportShapes`. `application/optimization/routes.py`
optimiert pro Layer, berücksichtigt `send_to_TSP` und ruft anschließend
`LayerContent.optimize` auf; Letzteres verändert nur Startpunkte von zur
Optimierung freigegebenen Shapes. Eine
zusätzliche Exportoption ist daher nicht ungeprüft neu zu erfinden, sondern
zuerst gegen die vorhandenen Wege und Optimierungsmodi abzugleichen.

- [x] Die dargestellte Reihenfolge der Bearbeitungslayer strikt abarbeiten;
  eine Optimierung darf keine Layergrenze überspringen oder Layer vertauschen.
- [x] Manuelles Umordnen von Shapes im Treeview (Drag-and-drop oder
  Auf-/Ab-Schaltflächen) legt die neue Bearbeitungsreihenfolge innerhalb
  desselben Layers fest. Modell und Exportlisten übernehmen diese Reihenfolge
  auch bei ausgeschaltetem Routen-Live-Update; eingeschaltet zeigt die
  Routenanzeige sofort die neuen Verbindungen. Geometrie, Startpunkte,
  Werkzeugzuordnung und Optimierungsfreigabe bleiben dabei erhalten.
  Speichern/Laden und anschließender Export ohne Optimierung übernehmen
  die manuelle Reihenfolge einschließlich benutzerdefiniertem G-Code.
- [x] Innerhalb eines Layers die Shape-Reihenfolge beibehalten, außer für
  ausdrücklich zur Optimierung freigegebene Shapes bei bewusst gewählter
  Optimierung. Nutzerentscheidung vom 01.11.2026: Die bestehenden Modi
  bleiben erhalten; die relative Reihenfolge nicht freigegebener Shapes
  genügt. `CONSTRAIN_ORDER_ONLY` erhält diese relative Reihenfolge;
  `CONSTRAIN_PLACE_AFTER` stellt diese Shapes vor die freigegebenen Shapes.
- [x] „Ohne Optimierung exportieren“ muss als klar erkennbare Aktion verfügbar
  sein. Sie löst weder eine neue Sortierung noch eine automatische Änderung
  der festgelegten Startpunkte aus. Exportiert wird die aktuell sichtbare
  Reihenfolge, auch wenn diese zuvor bewusst optimiert wurde.
- [x] Routenanzeige/Live-Update von Optimierung unterscheiden. Anzeigen oder
  Exportieren allein darf die Bearbeitungsreihenfolge nicht verändern.
- [x] GUI, CLI, Projekt-Roundtrip und tatsächliche G-Code-Sequenz verwenden
  denselben expliziten Reihenfolgevertrag. Werkzeugwechsel innerhalb eines
  Layers dürfen keine versteckte Gruppierung nach Werkzeug auslösen.

**Abnahme und Tests:** Mindestens zwei Layer mit eindeutig unterscheidbaren
Shapes und unterschiedlichen Werkzeugen verwenden. Layer und Shapes innerhalb ihrer bestehenden Ebene
manuell umordnen und mit Optimierung aus/an exportieren. Layerwechsel erst
bei der späteren gemeinsamen Umsetzung von R1b/R3 ergänzen.
Gemischte Optimierungsfreigabe und benutzerdefinierten G-Code einbeziehen;
Shape-/Werkzeugsequenzen im ausgegebenen G-Code statt nur Baumzeilen prüfen.
`dxf2gcode_tsp_optimization_test.py`, Tree- und Workflowtests erweitern.
Die Reihenfolge-Anforderungen vor einer Änderung des Optimierers präzise
festschreiben; bestehende Golden-Fälle bleiben Regressionen.

**Abgeschlossen und lokal geprüft, 01.11.2026:** Manuelles Umordnen und
Routenanzeige synchronisieren die Exportlisten ohne Optimierung. Die normale
Exportaktion ist ausdrücklich als Export ohne Optimierung bezeichnet;
DE/FR/RU-Kataloge und QM-Dateien wurden aktualisiert und mit tatsächlich
geladenen Übersetzungen geprüft. CLI-Projektexport erhält benutzerdefinierten
G-Code an seiner Position. Der kombinierte Treeview-/Projekt-/Exporttest prüft
zwei Layer, manuelle Shape-/Layer-Umordnung, Werkzeugwechsel, Startpunkte und
die tatsächliche G-Code-Sequenz; deaktivierte Einträge werden ausgelassen.
Auch der echte MainWindow-Workflow prüft manuelle Umordnung vor dem Export.
Die neuen Regressionen weisen die jeweiligen Fehler am vorherigen Stand nach.

Gezielt bestanden: PyQt5 mit 52 Tests (TSP, Tree-Multiselect, Exportreihenfolge,
MainWindow-Workflow und Shape-Werkzeuge); PyQt6 mit 40 Tests (dieselben Module
ohne Shape-Werkzeuge). Keine Vollsuite, Debian-Prüfung oder Paketbuild ausgeführt.
Die bisherigen Treeview-Drag-and-drop-Tests wurden dabei nicht erneut ausgeführt;
die neue gemeinsame Exportprüfung verwendet die Auf-/Ab-Schaltflächen.

**Optimierungsvertrag:** Die bestehenden Modi bleiben gemäß Nutzerentscheidung
erhalten. Der gemeinsame Anwendungsablauf wendet sie vor Startpunktoptimierung
und Routenanzeige an, sodass GUI und CLI dieselbe Shape-/Werkzeugfolge ausgeben.
Benutzerdefinierter G-Code behält beim normalen Export seine sichtbare Position;
bei bewusster Optimierung gelten die bisherigen Treeview-Modi auch für den CLI:
`CONSTRAIN_ORDER_ONLY` hängt alle aktiven Shapes hinter die übrigen Baumzeilen,
`CONSTRAIN_PLACE_AFTER` nur die freigegebenen Shapes. Die übrigen Zeilen behalten
ihre relative Reihenfolge. Die ergänzten Tests vergleichen beide Modi mit zwei
Layern und gemischter Freigabe im tatsächlichen G-Code sowie den anschließenden
Export ohne Optimierung. Ein weiterer CLI-Fall verwendet den echten TSP-Optimierer
mit deaktivierten Shapes, deaktiviertem G-Code und leerem Bearbeitungslayer.

## Importreihenfolge zusammengesetzter Kurven

Korrigiert am **31.10.2026** anhand von `fräsen_test_02 2004.dxf` und
`ATT00079.dxf`. Bei rückwärts verwendeten DXF-Entitäten drehte
`BuildDrawingModel` jedes einzelne Linien-/Bogenstück um, ließ aber die
Reihenfolge der Stücke unverändert. Die ausgewählte Originalkontur verband
dadurch falsche Endpunkte mit roten Geraden. Die blaue Vorschau zeichnete
die Teilstücke einzeln und verdeckte diese Unterbrechungen. Die fehlerhafte
Geometriekette war auch für die Planung relevant, nicht nur für die Anzeige.

Beim Rückwärtsimport wird jetzt zuerst die Teilstückreihenfolge umgekehrt
und dann jedes kopierte Teilstück gedreht. Die importierten Quelldaten
bleiben unverändert. `dxf2gcode_import_chain_test.py` prüft für beide Dateien
alle Shape-Verbindungen einschließlich Konturschluss, mit und ohne optionale
Linienteilung, sowie die Anschlusspositionen innerhalb der G40-Planpässe.
Die Prüfungen bestehen unter Qt5 und Qt6; zusätzlich wurde die tatsächliche
2D-Darstellung über den Hauptfenster-Ladeweg geprüft. Keine Vollsuite oder
Debian-Prüfung ausgeführt.

<a id="b1-b2"></a>

## B1/B2: Bohren, Pocketing und Kompensation

Umgesetzt am **31.10.2026**. `domain/project/machining.py` enthält die reine
Zustandsregel; `application/shapes.py:SetMachiningMode` wendet eine gemeinsame
Zielaktion auf die gesamte Auswahl an. Die Qt-Aktionen delegieren dorthin.

- Bohren einschalten setzt `Drill=True`, `Pocket=False` und G40.
- Pocketing einschalten oder G40/G41/G42 ausdrücklich wählen schaltet Bohren
  aus. Pocketing bleibt mit allen drei Kompensationszuständen kombinierbar.
- Ausschalten stellt keine frühere Bearbeitungsart wieder her. Gemischte
  Mehrfachauswahlen erhalten einen einheitlichen Zielzustand. Menühaken,
  Parameteranzeige und Vorschau werden anschließend aktualisiert.
- Widersprüchliche Projektwerte bleiben beim Laden erhalten. Das Hauptfenster
  meldet die betroffenen Shape-Nummern und fordert zur Auswahl einer gültigen
  Bearbeitungsart im Kontextmenü auf. Keine stillschweigende Vorrangregel.
- Für solche Shapes wird keine Geometrie vorbereitet. Der Planer liefert
  `machining.conflict` ohne exportierbaren Plan; die 2D-Vorschau zeigt eine
  Warnung statt einer Bearbeitungsbahn. Andere gültige Shapes bleiben
  exportierbar. Nach ausdrücklicher Auflösung ist das Shape wieder nutzbar.
- Automatische Fräskompensation verändert Bohreinstellungen nicht und löst
  bestehende Konflikte ebenfalls nicht stillschweigend auf.
- B2: Eine zusätzliche Sperre für Bohren bei Maschinenkompensation ließ sich
  im aktuellen Stand nicht bestätigen. Die Menüprüfung verwendet jetzt echte
  Geschlossenheit für alle ausgewählten Shapes; der bisherige Vergleich
  `allClosed == False` hatte offene Geometrie nicht ausgeschlossen. Bohren
  bleibt für geschlossene Kreisgeometrie bei beiden Kompensationskonfigurationen
  verfügbar. Leere, offene und gemischte ungeeignete Auswahlen bieten Bohren
  nicht an. Die gesonderte Pocketing-Sperre bei Maschinenkompensation bleibt.

Gezielte Tests unter Qt5 und Qt6 prüfen Zustandsübergänge, gemischte Auswahl,
Menühaken und erneut geöffnetes Menü, beide Kompensationskonfigurationen,
Projekt-Roundtrip mit Konfliktmeldung, blockierte Planung/Ausgabe, Auflösung
und Vorschauwarnung. Ein gültiger Bohrfall liefert pro Konfiguration einen
Plan und G-Code ohne Taschenbewegungen und G41/G42. Die deutschen,
französischen und russischen Meldungen wurden ergänzt, QM-Dateien regeneriert
und alle neuen Übersetzungen geprüft. Zusätzlich bestanden unter Qt5 die
bestehenden Projekt-/Adapter- und Werkzeugweg-Falltests einschließlich Goldens.
Keine Vollsuite, Debian-Prüfung oder Paketabnahme ausgeführt.

## K3: Dezimalpräzision und Werterhaltung

Umgesetzt am **31.10.2026**. Der ursprüngliche Befund war ein tatsächlicher
Wertverlust: Tiefen wie 0,015 und 0,005 Zoll wurden in den Konfigurationsfeldern
mit Qt-Standardpräzision von zwei Stellen quantisiert.

- `CorrectedDoubleSpinBox` verwendet standardmäßig vier Nachkommastellen.
  Dies gilt auch für die Werkzeugtabelle, Tiefen, Start-/Rückzugskoordinaten
  und Leads; die Schleppmesser-Rampenlänge verwendet jetzt ebenfalls vier.
  Explizit abweichende Genauigkeiten etwa für Importtoleranzen bleiben erhalten.
- Vereinbarte Regel: Geladene Werte mit mehr Stellen werden für die Anzeige
  gerundet, intern aber unverändert zurückgegeben, bis der Benutzer den Wert
  bearbeitet oder die Pfeiltasten des Spinbox-Felds verwendet. Unverändertes
  Bestätigen des Dialogs quantisiert diese Werte nicht.
- Shape-/Layerfelder schreiben ihre gerundete Anzeige beim bloßen Verlassen
  oder Bestätigen nicht zurück. Bewusstes Bearbeiten übernimmt die Eingabe;
  Punkt und Komma werden als Dezimaltrenner akzeptiert.
- Negative Werkzeug-Zusatzversätze werden in der Tabelle erhalten und nicht
  mehr durch die bisherige Untergrenze null ersetzt.
- Die vorhandenen Postprocessorprofile bleiben unverändert. `post_decimals`
  bestimmt weiterhin die G-Code-Präzision: drei Stellen reichen für 0,015 und
  0,005, für **0,0005 Zoll mindestens vier Nachkommastellen im verwendeten
  Postprocessorprofil einstellen**.

Bereits gerundet gespeicherte Werte lassen sich nicht rekonstruieren. Nach
dem Update deshalb bestehende Tiefen, Werkzeugwerte und die Ausgabepräzision
des Profils prüfen und bei Bedarf aus den ursprünglichen Vorgaben korrigieren.

Fokussierte Regressionen in `tests/dxf2gcode_numeric_precision_test.py` prüfen
positive/negative 0,015, 0,005, 0,0005 und mm-Werte, echte Tastatureingaben mit
Punkt/Komma, Erhaltung genauer geladener Werte, unverändertes Dialogbestätigen,
Speichern/Neuladen, mm/in-Wechsel sowie Projektpersistenz und Schneid-/Schwenktiefe
im Schleppmesserplan und ausgegebenen Z-Code bei expliziter Profilpräzision.
`TestParameterEditing` sichert außerdem die unveränderte Shapeanzeige und eine
bewusst akzeptierte Rundung ab. Die neuen Präzisionstests und die sieben
Bearbeitungstests bestehen unter Qt5 und Qt6; zusätzlich bestehen unter Qt5
alle Parameterzustands- und Pocketing-Konfigurationstests (44 Tests).
Keine neue Vollsuite, Debian-Prüfung oder Paketabnahme ausgeführt.

## Abgeschlossenes Werkzeugweg-Refactoring

Die folgenden Etappennummern 1–6 und 5a stammen aus der früheren Todo.
Sie bezeichnen keine Prioritätsabschnitte der neu geordneten aktiven Todo.
Die nachfolgenden Beschreibungen und Prüfstände sind aus dem bisherigen
Arbeitsdokument übernommen.

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
| Tabs/Breaks mit Passauswahl | `dxf2gcode_breaks_pass_test.py`, `dxf2gcode_toolpath_slices_test.py` | `slices_tabs_from_second_pass.gcode` | Native Aktionen und Projektion für automatische, ausgeschaltete und explizite Passauswahl geprüft |
| Pocketing, Kompensation und Richtungsmodi | `dxf2gcode_pocket*_test.py`, `dxf2gcode_toolpath_slices_test.py` | `slices_pocket_g40.gcode`, `slices_pocket_g41.gcode`, `slices_pocket_g42.gcode` | Native Bewegungen und Tiefen geprüft; vorbereitete Geometrie weiterhin aus bestehendem Algorithmus |
| Bohren/Hole-Geometrien | `dxf2gcode_toolpath_slices_test.py`, bestehende Hole-Vorschau/-Hit-Tests | `slices_drill.gcode`, `slices_drill_peck.gcode` | Kreis und HoleGeo mit einfacher/wiederholter Zustellung, Bohrposition und 2D-/3D-Projektion geprüft |
| Schleppmesser: offen/geschlossen, Overcut, Rampeneinfahrt | `dxf2gcode_leadmove_golden_test.py` | `drag_knife_*.gcode` | Eigene native Strategie mit Drag-/Rampenrollen; weitere Planinhaltstests ergänzen |
| Drehmaschine | `dxf2gcode_leadmove_function_test.py`, `dxf2gcode_toolpath_slices_test.py` | `slices_lathe_closed.gcode`, `slices_lathe_arc_open.gcode` | Bestehender Linien-/Bogenpfad, Passumkehr, Durchmesserformatierung und Lead-Einschränkungen geprüft; keine neuen Drehzyklen |
| Postprocessor-Bogenexport und Kompensationsregeln | `dxf2gcode_stmove_gcode_test.py`, Lead-Golden-Tests | Bogenverhalten nicht als eigene Golden-Matrix | Explizite MachineCapabilities; zusätzliche Profil-/Koordinatenkombinationen absichern |

Die Matrix dokumentiert bestehende Regressionen, nicht vollständige
Planabdeckung. Neue native Strategien benötigen für ihre vertikale Scheibe
gezielte Planinhaltstests und weiterhin bytegenaue G-Code-Vergleiche.
`dxf2gcode_toolpath_slices_test.py` ergänzt für Abschnitt 3 die gemeinsame
Plan-/Export-/Projektionsprüfung; weitere Profilkombinationen bleiben bei
konkretem Bedarf gezielt zu ergänzen.

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
ergänzt die gezielte fachliche Plan- und Exportmatrix,
insbesondere für Bohren, Drehmaschine und weitere Kombinationen. Die
Weiterverwendung vorhandener StMove-/Offset-/Pocket-Geometriealgorithmen
bedeutet weiterhin keinen vollständigen Abschluss des gesamten Refactorings.

### 3. Fälle in kleinen vertikalen Scheiben migrieren

Jede Scheibe umfasst Planer, Export, Vorschauprojektionen und Regressionen.
Die Reihenfolge minimiert Abhängigkeiten zwischen den Fällen.

- [x] Geschlossene Kontur, Softwarekompensation, mehrere Tiefenpässe.
- [x] Offene Kontur mit alternierender Passrichtung und Softwarekompensation.
- [x] Maschinenkompensation G41/G42 einschließlich Ein-/Ausschalten und
  Richtungswechselregeln des Postprocessors.
- [x] Leads, Overcut und ungültige Lead-Geometrie mit Diagnosen.
- [x] Tabs/Breaks mit Auswahl der betroffenen Pässe.
- [x] Pocketmilling mit frei wählbarer Kompensationsrichtung G40/G41/G42.
- [x] Bohren und Hole-Geometrien.
- [x] Schleppmesser einschließlich Tipweg, Drag-Hops und Rampeneinfahrt.
- [x] Drehmaschine: vorhandene unterstützte Formen und Einschränkungen
  explizit abbilden.

**Umsetzung und Grenzen (30.10.2026):** Die nativen Strategien aus Abschnitt 2
werden weiterverwendet. `dxf2gcode_toolpath_slices_test.py` prüft für die
Fallgruppen wiederholbare Planung, unveränderte Projekteingaben und dieselbe
Ausgabe über direkten Planexport und den Shape-Exportadapter. Formatierte
XY-Endpunkte werden mit den Planaktionen verglichen. Vorhandene Golden-Fälle
bleiben unverändert; acht neue Referenzen sichern Tabs, Pocket G40/G41/G42,
einfaches/wiederholtes Bohren sowie Linien und offene Bögen der Drehmaschine.

- Offene Softwarekompensationsbahnen werden in 2D auch bei umgekehrter
  Passrichtung nur einmal gezeichnet. Getrennte XY-Abschnitte erhalten im
  echten `QPainterPath` eigene Teilpfade statt künstlicher Verbindungslinien.
- Der Plan hält den ersten Anfahrpunkt auch bei späteren Pocket-Eilwegen fest.
  Der eingefrorene Werkzeugradius ermöglicht Bohrmarkierungen in 2D; die
  Z-Aktionen desselben Plans liefern die Bohrbewegungen in 3D.
- Tabs sind für automatische/ausgeschaltete sowie erste/zweite Passauswahl
  geprüft. Die bestehende Schnittpunktberechnung verwendet unter Qt6
  `QLineF.intersects`; ältere Qt5-Versionen behalten ihren bisherigen Zugriff.
- Pocketing bleibt Softwarekompensation mit gewähltem G40/G41/G42; die
  vorhandene GUI-Sperre bei Maschinenkompensation wird nicht aufgehoben.
- Beim Schleppmesser bleiben vorbereiteter Halterversatz zur Messerspitze,
  Schwenkbögen, Hubtiefe und bestehende Rampenausgabe erhalten. D1/D2 werden
  dadurch nicht vorweggenommen; es wird kein neuer Messerablauf eingeführt.
- Die Drehmaschine verwendet weiterhin die vorhandene Konturstrategie für
  Linien/Bögen und Tiefenpässe. Leads und Overcut bleiben deaktiviert;
  der Postprocessor behält seine bestehende Durchmesserformatierung bei.
  Neue Drehzyklen oder zusätzliche Maschinenfreigaben sind nicht enthalten.

**Gezielte Prüfung:** 115 Tests unter Qt5 bestanden (Fallmatrix, Planvertrag,
StMove-Export, Tab-Pässe, 18 bestehende Golden-Fälle, Lead-Pass-/Exportvergleich
und Pocket-Kompensationsfälle). Nach der Qt-Kompatibilitätskorrektur bestehen
zusätzlich die 17 betroffenen Tab-Tests unter Qt5 und alle neun neuen
Fallmatrix-/Painter-Tests unter Qt6. Keine Vollsuite, Debian-/SSH-Läufe oder
Builds ausgeführt; kein manueller GUI-/OpenGL-Renderingnachweis.
Zum damaligen Prüfstand waren die Vorschau-/Geometriearbeiten aus den
Etappen 5/6 noch offen; ihre späteren Abschlüsse sind unten dokumentiert.

### 4. G-Code-Serialisierung auf semantische Bewegungen umstellen

- [x] `ToolpathGCodeExporter` serialisiert alle Planaktionen; er berechnet
  keine Konturen, Offsets, Passfolgen oder Pocket-Bahnen.
- [x] Postprocessor-Dialekte formatieren nur Bewegungs- und Steuerungsaktionen
  und verwalten ihren modalen Ausgabestatus.
- [x] Direkte Postprocessor-Aufrufe aus `ShapeToolpathCommandBuilder`,
  Geometrieklassen und Planungslogik entfernen.
- [x] Alle vorhandenen Golden-G-Code-Ausgaben bytegenau erhalten.

**Umsetzung (31.10.2026):** `adapters/postprocessor/dialect.py:ProfileDialect`
enthält die profilabhängige Bewegungs-/Steuerungsformatierung, Zahlenformate,
Template-Ersetzung, Zeilennummern und Zeilenenden. Der modale Ausgabezustand
für Vorschub und absolute/inkrementelle XY-/Z-Werte gehört ebenfalls dorthin.
Die Klasse erhält Profil, Startkoordinaten, Start-Z und Durchmesserfaktor
explizit; sie importiert weder Qt, globale Laufzeitwerte noch einen Planer.
Die vorhandenen Formatierungsalgorithmen und Profilvorlagen bleiben erhalten.

`MyPostProcessor` erbt diese Formatierungsoberfläche für bestehende Aufrufer.
Seine Exportinitialisierung übergibt die aufgelösten Startwerte und den
Drehmaschinenfaktor einmal an den Dialekt. Profilverwaltung, GUI-Anbindung,
Programmkopf mit Versionsmetadaten, Dateiausgabe, Layer-/Shape-Durchlauf und
Anschluss an den Planungsanwendungsfall bleiben in dieser Exportfassade.
Die Fassade ist damit weiterhin kein vollständig GUI-unabhängiger Dienst;
für reine Planserialisierung genügt dagegen `ProfileDialect` zusammen mit
`ToolpathGCodeExporter`. Weitere Entkopplung bleibt gesonderte Arbeit.

**Gezielte Prüfung:** 72 lokale Tests bestanden: alle 18 bisherigen
Lead-/Schleppmesser-Golden-Fälle, die neun vertikalen Fallmatrix-/Painter-Tests
mit acht weiteren Referenzdateien, die StMove-/Postprocessor-Regressionen,
drei eigenständige Dialekttests und ein Importgrenztest. Die Fallmatrix
vergleicht jetzt zusätzlich die Ausgabe des eigenständigen Dialekts mit der
bestehenden Exportfassade. Neue Tests prüfen fortlaufenden modalen Zustand
über mehrere Pläne, absolute/inkrementelle Koordinaten, getrennte Instanzen,
explizite Durchmesserskalierung von Bogenworten sowie geordnete Profil-,
Bohr-, Kompensations- und Literalaktionen. Keine Referenzdatei geändert;
keine Vollsuite, Debian-/SSH-Läufe oder Builds ausgeführt.

### 5. Vorschau und gemeinsame Planquelle abschließen

- [x] 2D-Projektion zeigt gleiche XY-Bahnen einmal und kennzeichnet Tabs,
  Leads, Eilwege sowie programmierte beziehungsweise kompensierte Bahn
  eindeutig.
- [x] 3D-Projektion übernimmt Z und Passfolge aus demselben Plan.
- [x] 2D/3D-Vorschau berechnet weder Passfolge noch Tabs, Leads oder
  Rückzüge unabhängig vom Export neu.
- [x] Änderungen an Werkzeug, Tiefe, Kompensation, Leads, Tabs und
  Pocket-Einstellungen invalidieren den Plan und beide Projektionen zusammen.

**Umsetzung (31.10.2026):** Beide Ansichten erhalten ihre Pläne über
`adapters/toolpath/preview.py` mit derselben Eingabeaufbereitung und demselben
Domain-Planer wie der Export. Verwendet werden das geladene Postprocessorprofil
beziehungsweise dessen Schema-Vorgaben, solange noch kein Profil geladen ist,
sowie die aktuellen Break-Layer. Vorschauplanung verändert den modalen
Ausgabezustand des Exporters nicht.

`plan_preview_segments` projiziert die geordneten Planaktionen einschließlich
Z, Leads, Tabs, Pocket-Bewegungen und Eilwegen. Die Zusatzdarstellung in 2D/3D
berechnet keine eigenen Leads oder Tab-Schnittpunkte mehr. Offene XY-Bahnen
werden auch bei umgekehrter Passrichtung dedupliziert; getrennte Abschnitte
bleiben getrennte Painter-Teilpfade. Die Bogenprojektion berücksichtigt auch
Profile, die ausschließlich Gegenuhrzeigersinn-Bögen ausgeben.

Programmiertes G41/G42 und Werkzeugmittelpunktbahnen mit G40 sind als
Kompensationsraum im Plan festgehalten und durch den 2D-Tooltip unterscheidbar.
Die vorhandenen Bahnfarben bleiben unabhängig davon erhalten. Die Beschreibungen sind in Deutsch,
Französisch und Russisch übersetzt; die QM-Dateien wurden neu erzeugt und
mit tatsächlich geladenen Translatoren geprüft. Tab- und Lead-Bewegungen
besitzen eigene Darstellungsrollen.

Es gibt keinen wiederverwendeten Plan-Cache: Bei einem erneuten Darstellen
oder Exportieren werden die aktuellen Werkzeug-, Tiefen-, Kompensations-,
Lead-, Tab- und Pocket-Werte neu eingefroren. Änderungen können deshalb keinen
alten Plan in einer der Projektionen weiterverwenden. Die vorhandenen
GUI-Änderungsaktionen lösen das erneute Darstellen aus. Die Originalgeometrie
ist die stets sichtbare Grunddarstellung und Auswahlfläche. Der gemeinsame
Plan bestimmt ausschließlich die bei Auswahl zusätzlich angezeigte
Werkzeugwegvorschau und den Export.

**Darstellungskorrektur nach Nutzertest (31.10.2026):** Die erste Umsetzung
hatte bei vorhandenem Plan die Grunddarstellung irrtümlich durch die geplante
Bahn ersetzt. In 2D verwendet `ShapeGUI.path` jetzt wieder die Originalkontur;
in 3D enthält `drawObject` ebenfalls die Originalgeometrie. Der planbasierte
Werkzeugweg liegt getrennt in der Auswahl-Zusatzdarstellung. Auswahl und
Abwahl blenden diese ein beziehungsweise aus, ohne die Originalkontur oder
deren Trefferfläche zu ersetzen. Werkzeugbahn, Pocket, Lead-in/Werkzeug,
Lead-out und Eilwege verwenden wieder die vorhandene Farbpalette; die
Zusatzbahn erhält keine neue Farbe abhängig vom Kompensationsraum.

Die zuvor irrtümlich auf die Grunddarstellung bezogenen Plan-Painter- und
3D-Passprüfungen wurden auf die Werkzeugweg-Zusatzdarstellung umgestellt.
Gezielte Prüfungen belegen Originalkontur und Trefferfläche, Ein-/Ausblenden
bei Auswahl/Abwahl, getrennte Teilpfade sowie Bahn-, Lead- und Werkzeugfarben:
**21 Tests jeweils unter Qt5 und Qt6 bestanden**. Keine erneute Vollsuite und
kein Debian-Lauf für diese Darstellungskorrektur; die OpenGL-Prüfungen
kontrollieren Aufrufe mit einem Mock, keinen echten GPU-Renderdurchlauf.

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

- [x] `domain/toolpath` und `domain/geometry` benötigen weder Qt noch
  `bootstrap.runtime_state` oder Postprocessor-Module.
- [x] Globale Werte wie `g.config` und Maschinenart in der Planungslogik durch
  explizite Einstellungen und Fähigkeiten ersetzen.
- [x] GUI-spezifische Fehleranzeige aus Planern entfernen; GUI und CLI
  präsentieren dieselben Diagnosen jeweils passend.
- [x] Entfernen der alten Shape-basierten G-Code-Ausgabe und aller
  Übergangspfade erst nach Migration sämtlicher Aufrufer.

**Umsetzung nach Abschnitt 5 (31.10.2026):**

- `PreparationSettings` hält aufgelöste Maschinenart, Kompensationszuständigkeit,
  Werkzeugwerte, Lead-Modi, Überfahrt, Messerstartwinkel und Pocket-Freiraum
  als unveränderliche Werte. `adapters/toolpath/preparation.py` löst die
  Laufzeitwerte auf; die Geometrievorbereitung erhält sie explizit. GUI, CLI
  und Testfixtures wurden auf diese Grenze umgestellt.
- `Geos` und die gemeinsamen Kontur-Operationen liegen unter
  `domain/geometry/collections.py`. Der Offset-Algorithmus erbt von
  `ContourGeometry`, statt das Qt-/konfigurationsabhängige Projekt-Shape zu
  importieren. Das Projekt-Shape verwendet dieselben Geometrieoperationen.
  `ArcGeo` erhält die Toleranz für die Mittelpunktberechnung als Parameter.
- Domain-Meldungen tragen Quelltext, Kontext und Formatargumente ohne Qt.
  Beschriftungen und Übersetzung liegen im Qt-Adapter; bestehende
  Übersetzungskontexte bleiben erhalten.
- `PocketMill.generate()` liefert neue Geometrie zurück. Die Berechnung
  verändert weder die Eingabesammlung des Aufrufers noch das Projektmodell.
  Die Vorbereitung übernimmt das Ergebnis anschließend in ihren eigenen Weg.
- Die getrennte Vorschau-Berechnung von Exit-Leads, letzten Passrichtungen
  und Break-Schnittpunkten sowie die StMove-Zeichenroutine sind entfernt.
  Für bestehende Anzeigezugriffe bereitgestellte `exit_geos` sind nur noch
  aus den fertigen Planaktionen abgeleitete Werte, kein zweiter Planungsweg.
  Shape und Geometrieklassen erzeugen weiterhin keinen G-Code.

Ein Importgrenztest lädt sämtliche Module unter `domain/geometry` und
`domain/toolpath` in einem frischen Prozess und prüft das Ausbleiben von Qt-,
Presentation-, Postprocessor- und globalen Laufzeitimporten. Das ist die hier
abgeschlossene Grenze; Profilverwaltung und GUI-/Dateiorchestrierung der
Exportfassade sowie die übrigen Projektmodelle sind davon zu unterscheiden.

**Prüfstand der Refactoring-Etappe vor der nachfolgenden Darstellungskorrektur:**

- Windows, Python 3.11 / Qt5: vollständige Suite, **775 Tests bestanden**
  (`.tox/toolpath-full-windows-final.log`). Die neuen Vorschauprüfungen wurden
  zusätzlich gezielt unter Qt6 ausgeführt; keine vollständige Qt6-Suite.
- Debian auf `192.168.178.183`, Python 3.13.5 / Qt5: vollständige Suite,
  **775 Tests bestanden**, in einer neuen virtuellen Umgebung unter
  `/home/christian/dxf2gcode-test-work/runs/toolpath-full-20261031T065841Z-59bd6e20`.
  Verwendet wurden dieselben Runtime-Abhängigkeitsversionen wie in der
  vorhandenen Debian-Testinstallation. Diese Installation und ihre Samples
  wurden nicht verändert.
- Der erste Debian-Snapshot hatte versehentlich `source/tools/build`
  ausgelassen; dadurch scheiterte ausschließlich der Metadaten-Test
  `TestBuildProvenance.test_build_commands_prefer_source_to_older_installed_package`.
  Der korrigierte Snapshot enthält diese Dateien. Der bereits gestartete
  Wiederholungslauf war vor dem angeforderten Stop beendet; danach wurde
  auf Nutzerwunsch **nur dieser einzelne Test erneut ausgeführt und bestand**.
  Keine weiteren Tests gestartet.
- Debian-Snapshot SHA-256:
  `655764dedb20ba9fea6543a92600a6801dc42d3674950601c43fd55b0b1898b8`.
  Bericht und Protokoll sind lokal unter `.tox/toolpath-debian-report.json`
  und `.tox/toolpath-full-debian-final.log` gesichert. Fehlgeschlagene
  Debian-Läufe wurden zur Nachvollziehbarkeit beibehalten.
- Die vorhandenen Golden-G-Code-Referenzen bleiben unverändert. Es wurden
  keine Release-/MSI-Builds oder Systempaketinstallationen ausgeführt.
  OpenGL-Aufrufprüfungen verwenden weiterhin ein Mock; ein manueller
  GPU-Renderingnachweis ist damit nicht verbunden.

## Abgeschlossene Bedien- und Importaufgaben

### U1 – Werkzeugauswahl an der Durchmesserzeile ausrichten

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

### U2 – Baum-Buttons nur bei möglicher Zustandsänderung aktivieren

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

**Nachbesserung nach Hängermeldung (30.10.2026):** Nach manuellem Zuklappen
eines Asts reagierte das native Fenster beim anschließenden Ein-/Ausklappen
nicht mehr. Betroffene Datei: `Frontplatte_Texte_aufgebrochen.dxf`;
Programmstart direkt aus dem Projekt.

Der bisherige Signalpfad lief die Baumstruktur synchron aus Qt-Ein-/
Ausklappsignalen ab. `isExpanded()` kann dabei ein ausstehendes Qt-Layout
ausführen; die synchronen Buttonänderungen erzeugten außerdem unnötige
Rückkopplungen und mehrere Zwischenzustände pro Sammelaktion. Zwei gezielte
Regressionen belegten diese synchronen bzw. mehrfachen Benachrichtigungen
vor der Korrektur.

- [x] Einzelne Klapp-/Modellsignale über einen dem View gehörenden
  Single-Shot-Timer zusammenfassen und erst nach der Qt-Aktion auswerten.
- [x] Während `expandAll`, `collapseAll` und `expandToDepth` keine erneute
  Zustandsabfrage auslösen; am Ende einmal den abgeschlossenen Zustand melden.
- [x] Wiedereintritt absichern und unveränderte Buttonzustände nicht erneut
  veröffentlichen. Während einer laufenden Abfrage angeforderte Updates erst
  anschließend einplanen, statt eine verschachtelte Timer-Schleife zu starten.
- [x] Sichtbaren Baum und echtes Hauptfenster mit der betroffenen DXF im
  Offscreen-Modus prüfen: Astpfeile und Buttons per Mausklick, beide Tabs,
  wiederholtes Ein-/Ausklappen und gemischte Zustände. Separate Testprozesse
  haben Zeitlimits, damit ein Hänger nicht die ganze Testsuite blockiert.

Fokussierter Prüfstand nach der Nachbesserung: Qt5 mit 20 TreeView- und zwei
MainWindow-Tests; Qt6 mit zwölf Baumzustands- und zwei MainWindow-Tests.
Der vollständige native Windows-Hänger ließ sich im Offscreen-Test nicht
zuverlässig reproduzieren; eine Bestätigung im normalen Fenster steht noch
aus. Keine erneute Vollsuite, Debian-Prüfung oder Paketerstellung für diese
Nachbesserung; das vorhandene Wheel enthält sie noch nicht.

### U4 – Ticket #157: Startzustand des Layerbaums konfigurieren

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

### I2 – Layer 0 und IGNORE-Layer optional vom Import ausschließen

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

## Abgeschlossene Drag-and-drop-Stabilisierung

<a id="r1a"></a>

### R1a – Drag-and-drop stabilisieren

**Codebefund:** `TreeView.dropEvent` in `treeview.py` verschiebt Zeilen
innerhalb desselben Elternknotens. In einem Ablehnungszweig wird
`drop_item.parent().rowCount()` aufgerufen, obwohl ein fremder oberster
Layer keinen Parent hat. Damit ist ein plausibler `None`-Zugriff sichtbar;
der gemeldete Absturz ist ohne Reproduktion/Traceback noch nicht abschließend
diesem Pfad zugeordnet. Ein echter Wechsel der Layer-Zugehörigkeit wird durch
die bisherigen `takeRow`-/`insertRow`-Aufrufe nicht implementiert.

**Früherer Qt6-Befund bei U2:** Zwei bestehende Tests
(`test_drop_reorders_siblings_and_calls_export_callback` und
`test_drop_without_drag_or_onto_viewport_is_ignored`) scheitern an
`TreeView.BelowItem`/`TreeView.OnViewport`. Auch die vorhandenen Drop-Handler
verwenden flache `QTreeView`-Enum-Namen. Im aktiven Drop-Handler und den Tests
sind diese bei R1a durch Qt5-/Qt6-kompatible `DropIndicatorPosition`-Werte
ersetzt. Die ungenutzte historische Methode `dropEventOld` bleibt unverändert.

`TreeHandler.updateExportOrder` benötigt zugleich die Mitgliedschaft in
`real_layer.shapes`; eine rein optisch umgehängte Shape genügt deshalb nicht.
`domain/project/project.py` stellt Projekte nach DXF-Neuimport über Layernamen
und Shape-Zuordnungen wieder her. Deren Ladepfad muss einen Layerwechsel
ebenfalls nachvollziehen können.

- [x] **Teil R1a – Stabilität:** den gemeldeten Drop auf einen anderen Layer
  reproduzieren und den Fehlerpfad absichern. Unzulässige/abgebrochene Drops,
  ungültige Zielindizes und Drops auf leere Bereiche dürfen nicht abstürzen
  oder das Modell teilweise verändern. Qt5 und Qt6 gezielt berücksichtigen.

**Prüfstand R1a (30.10.2026):** Ein ergänzter Regressionstest mit echtem
`QStandardItemModel` und simuliertem Drop-Event reproduziert vor dem Fix den
`NoneType.rowCount`-Absturz beim Drop auf einen fremden obersten Layer.
Der Ablehnungszweig greift nun nicht mehr auf dessen fehlenden Parent zu.
Ungültige Quell-/Zielindizes und Drops auf fremde Zweige oder leere Bereiche
werden abgelehnt; der Drag-Zustand wird beendet. Der Test prüft unveränderte
Zeilen, Shape-Identität und ausbleibende Exportbenachrichtigungen.
Alle 21 Tests aus `dxf2gcode_treeview_test.py` bestehen jeweils unter Qt5 und
Qt6. Kein manueller GUI-Durchlauf, keine Vollsuite und keine Builds ausgeführt.

**Nachkorrektur R1a:** Beim manuellen Test trat unter Qt6 zusätzlich ein
`AttributeError` auf: echte `QDropEvent`-Objekte besitzen dort `position()`
statt `pos()`. Der aktive Handler verwendet nun den passenden Zugriff und
verzichtet auf die vorzeitige Positionsabfrage im Debug-Logging. Die vorhandenen
Tests für Umordnen und abgelehnte Drops verwenden jetzt echte `QDropEvent`-
Objekte statt eines simulierten Events; damit wurde der gemeldete Fehler vor
der Korrektur reproduziert. Erneut bestehen alle 21 TreeView-Tests jeweils
unter Qt5 und Qt6.

Der Layerwechsel R1b bleibt zusammen mit R3 zurückgestellt; siehe
[aktive Todo](../todo.md#r1b).

## Versions- und Build-Metadaten

### Implementierung und Vertrag

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

### Vorhandene fokussierte Prüfungen

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

Die Implementierung ist erledigt; die Abnahme fertiger Artefakte bleibt
als [M1 in der aktiven Todo](../todo.md#m1) offen.

## Abgeschlossene Bereinigung

**Abgeschlossene Bereinigung:** `.kilo/` und die erzeugte Datei `.coverage`
sind entfernt. Der frühere Plan bleibt unter
[archive/machine-comp-radius-leadin-plan.md](machine-comp-radius-leadin-plan.md)
als ausdrücklich historische Referenz erhalten. `.coverage` ist bereits
ignoriert und kann durch einen späteren Coverage-Lauf erneut entstehen.

## Bewusst verworfene Anforderungen

Diese Punkte wurden ausdrücklich abgewählt; sie sind weder implementiert
noch offene Aufgaben. Sie werden nur zur Abgrenzung aufbewahrt.

### I1 – Zu kurze Segmente in der Vorschau markieren

**Entfallen – ausdrücklich nicht gewünscht (30.10.2026).** Das Merkmal
„Too short segments highlighting“ aus dem Ticket wird nicht umgesetzt und
zählt nicht als offene Aufgabe. Bestehende Geometrievalidierung und andere
Diagnosen werden dadurch nicht entfernt oder geändert.

### R4 – Ticket #157: Layer alphanumerisch sortieren

**Entfallen – ausdrücklich nicht gewünscht (30.10.2026).** Keine
alphanumerische/natürliche Layersortierung aus diesem Ticket implementieren.
Der Eintrag bleibt nur zur Dokumentation der Abgrenzung erhalten und zählt
nicht als offene Aufgabe. Die manuelle Bearbeitungs-/Exportreihenfolge aus
R1/R2 bleibt davon unberührt.

## Einordnung der früheren Abnahmetore

Die früher durchgehend offenen Kontrollkästchen werden nicht als neun neue
Implementierungsaufgaben fortgeführt. Vorhandene Nachweise und verbleibende
Grenzen sind getrennt zu lesen:

| Kriterium der früheren Liste | Dokumentierter Stand / verbleibende Grenze |
| --- | --- |
| Planung, Geometrie, Vorschau und Formatierung getrennt testbar | Nachweise aus Etappen 1–6; keine G-Code-Ausgabe aus Geometrieklassen |
| Verhaltenstests und unveränderte Golden-Ausgaben je Scheibe | Repräsentative Fallmatrix, 18 bisherige und acht ergänzende Referenzen |
| Vollsuite nach Migration | 775 Tests unter Windows und Debian bestanden; spätere Darstellungskorrektur nur fokussiert geprüft |
| Gemeinsamer unveränderlicher Plan für GUI/CLI und Werkzeugwegvorschau | Gemeinsamer Planvertrag, Planer und Exportadapter; Originalgeometrie bleibt eine gesonderte Grunddarstellung |
| 2D-Deduplizierung und 3D-Tiefen | Projektionstests und fokussierte Darstellungskorrektur; kein manueller GPU-Nachweis |
| Software-/Maschinenkompensation unterscheidbar | Geometrie beziehungsweise explizite Zustandsaktionen und Tooltip; bestehende Bahnfarben erhalten |
| Unterstützte und nicht unterstützte Kombinationen vollständig erfasst | Repräsentative Tests vorhanden; Konfliktfälle B1/B2 und die genaue Abnahmegrenze bleiben in der aktiven Todo |
| Importfreiheit von Domain und Application | Nachgewiesen für alle Module unter `domain/geometry` und `domain/toolpath`; die weitergehende pauschale Formulierung ist unter A1 zu klären |
| Alte Shape-Ausgabe und doppelte Werkzeugwegplanung entfernt | Etappen 2/4/6; für Anzeigezugriffe verbleiben lediglich aus Planaktionen abgeleitete Werte |

Fertige Pakete und ihre Herkunft werden erst mit
[M1](../todo.md#m1) abgenommen. Eine allgemeine
Release-Freigabe oder ein Nachweis physischer Bearbeitungsqualität folgt aus
den dokumentierten Tests nicht.

### Metadaten: früherer Keyword-Mechanismus

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
als umgesetzt erfasst; seine abschließende Paket-/Debian-Prüfung bleibt [M1](../todo.md#m1).

## Historische Ausgangslage und ursprüngliche Etappen

Die folgenden Angaben bewahren den Kontext des ursprünglichen
Werkzeugwegplans. **Alte Pfade und Methoden sind keine aktuellen Zielpfade
und sollen nicht wiederhergestellt werden.** Der aktuelle Aufgabenstatus
steht in der [aktiven Todo](../todo.md). Die folgenden
Etappen- und Abschnittsnummern beziehen sich auf die frühere Todo-Struktur,
nicht auf die neue Prioritätsreihenfolge.

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
  Geometrie-/Vorschauentkopplung waren zu diesem historischen Zeitpunkt noch offen.

## Architektur-Migrationsstand vom 29. Oktober 2026

Aus dem früheren Architekturbericht übernommen. Diese zeitgebundene
Bestandsaufnahme wird historisch bewahrt; sie ist keine aktuelle
Prüfung des Codes und kein zusätzlicher Umsetzungsauftrag. Für offene
Arbeiten gilt die [aktive Todo](../todo.md).

### Damals offene Architekturgrenzen

Die Paketnamen und Dateipfade sind vereinheitlicht; die inhaltliche Entkopplung
ist noch nicht vollständig. Diese Punkte sind sichtbar und dürfen nicht als
abgeschlossene Zielarchitektur behandelt werden:

- Mehrere Domain-Module greifen noch auf `bootstrap.runtime_state` zu; einige
  verwenden zudem Qt für Übersetzung oder Warnmeldungen.
- `presentation.qt.application` enthält weiterhin CLI-Start, Laufzeitaufbau
  und GUI-Orchestrierung neben dem Hauptfenster.
- `adapters/dxf/parser.py` enthält den bestehenden Parser und liefert noch
  legacy-orientierte Modellobjekte.
- Alle Shape-Exporte laufen über einen `ToolpathPlan` mit semantischen
  Aktionen. `domain/toolpath/planner.py` wählt reine Strategien für einfache
  Fräsfälle, Konturen und Schleppmesser. Ein Adapter übergibt unveränderliche
  Geometrie-, Einstellungs- und Fähigkeitsdaten. Die Planung führt keine
  Postprocessor-Methoden mehr aus; Shape-Builder und Recorder sind entfernt.
  Die vorbereiteten Offset-/Pocket-/Lead-Geometrien stammen weiterhin aus
  den bestehenden Algorithmen. Deren globale und Qt-Kopplungen sowie die
  vollständige fachliche Fallmatrix bleiben weitere Arbeitsschritte.
- Projektserialisierung und Teile der Bearbeitungslogik liegen noch in den
  Domain-Modellen, statt vollständig über Ports und Adapter zu laufen.

Die nächsten Schritte verlagern diese Zuständigkeiten in kleinen Scheiben:
Laufzeitkonfiguration explizit an Anwendungsfälle übergeben, Importdaten
normalisieren, den Werkzeugwegplan auf alle Maschinenarten ausweiten und
schließlich die Start- und UI-Koordination trennen. Erst danach sind die
Abhängigkeitsregeln der Zielstruktur vollständig erfüllt.
