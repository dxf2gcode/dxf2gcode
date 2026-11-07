# R3/R1b: Bearbeitungsmodell und Projektformat 2.0

Stand: **07.11.2026**, P1–P3. Die Bedienung im dritten Tab folgt in P4/P5.
[Plan und Entscheidungen D1–D19](../planning/r3-r1b-implementation-plan.md),
[Prüfnachweis](../archive/toolpath-refactoring-completed.md#r3-r1b-p1-p3).

## Identitäten und Auflösung

`MachiningProject` enthält Geometriereferenzen, Werkzeugdefinitionen und eine
geordnete Liste benannter Schritte. Ein Schritt besitzt genau eine Art und
eine Werkzeugdefinitions-ID. Seine Einträge sind Bearbeitungen oder freier
G-Code. Mehrere Bearbeitungen dürfen dieselbe Originalkontur referenzieren;
Startpunkt, Richtung, Aktivierung und Werte gehören jeweils zur Bearbeitung.
Neue IDs sind UUIDs und bleiben beim Speichern erhalten. Die Ausgabenummer
ist keine Werkzeugidentität: unterschiedliche Definitionen mit derselben
Nummer sind nach D19 erlaubt, auch bei unterschiedlichen Durchmessern.

Der Resolver liest ausschließlich gespeicherte Werte: Werkzeugvorgaben,
Projektvorgaben, Schrittvorgaben, eigene Bearbeitungswerte; die jeweils
speziellere Ebene gewinnt. `parameter_origins` benennt `tool`, `project`,
`step` oder `operation`. Werkzeug und Art selbst kommen immer vom Schritt.

| Feld / heutige Quelle | Neuer Eigentümer und Migration | Einheit / Neuberechnung |
| --- | --- | --- |
| `tool_nr`, `tool_diameter` aus Layer oder `tool_override` | Schritt verweist auf gespeicherte Definition; nur vollständig gleiche Definitionen wiederverwenden | Nummer dimensionslos, Durchmesser in Projekteinheit; Werkzeugweg neu planen |
| `speed`, `start_radius`, `lead_radius`, `lead_length`, `overcut_length` aus effektivem Werkzeug | Definition als gespeicherte Werkzeugvorgabe; spätere eigene Bearbeitungswerte möglich | Drehzahl unverändert; Längen in Projekteinheit; neu planen |
| `axis3_start_mill_depth`, `axis3_slice_depth`, `axis3_mill_depth` | Unklare Altwerte als eigene Bearbeitungswerte, auch bei Gleichheit mit Vorgaben | Projekteinheit; Tiefenplan neu erstellen |
| `axis3_retract`, `axis3_safe_margin` | Schrittvorgaben aus Layer; keine Overrides pro Bearbeitung im Format 2.0 | Projekteinheit; Plan neu erstellen |
| `f_g1_plane`, `f_g1_depth` | Unklare Altwerte als eigene Bearbeitungswerte | Projekteinheit/min; Plan neu erstellen |
| `milling_offset`, `cut_cor`, `break_pass`, `drag_angle` | Effektive Altwerte als eigene Bearbeitungswerte | Offset als Länge, Winkel in Grad, übrige Werte dimensionslos; neu planen |
| `lead_in_mode`, `lead_out_mode`, `overcut_enabled` | Bestehendes `default` beweist Vererbung vom gespeicherten Schritt; explizite Werte bleiben eigene Werte | Zustände; neu planen |
| `drag_swivel_depth` | Vorhandener eigener Wert bleibt; `None` erbt gespeicherte Schrittvorgabe | Projekteinheit; Messerplan neu erstellen |
| `Drill`, `Pocket`, Layerart | Einheitliche Schrittart `contour`, `pocket`, `drill`, `break` oder `ignored`; widersprüchliche Altzustände zusätzlich erhalten und diagnostizieren | Zustände; neu planen |
| Start, `cw`, `disabled`, `send_to_TSP` | Eigene Bearbeitungsdaten; Start in lokalen Konturkoordinaten | Start als Länge, übrige Werte dimensionslos; neue Projektion/Plan |
| Import-, Maschinen-, Pocket-, Messer-, Lead- und Routenvorgaben | Projektkonfigurations-Snapshot; globale Profiländerungen ändern gespeicherte Aufträge nicht | Mit gespeicherter Einheit lesen, keine erneute implizite Umrechnung |

Geometrie und Projektwerte werden vor der Planung in getrennte Shape-/Layer-
Projektionen kopiert. Vorschau und Export verwenden denselben Resolver und
dieselbe gespeicherte Konfiguration. Projektionen werden frisch erstellt,
statt alte Pläne nach einer Änderung weiterzuverwenden. `update_tool` ist die
atomare Modelloperation zur ausdrücklichen Werkzeugaktualisierung; die
Profilübernahme mit Änderungsanzeige/Undo folgt mit der neuen Bedienung.

## Datei, Migration und Reload

Neue GUI-Speicherungen schreiben UTF-8-JSON mit `format: DXF2GCODE`,
`version: 2.0`, `source` und `machining`. `source` bewahrt Zeichnungspfad,
Transformation und den Wiederherstellungsstand des bisherigen Baums.
`machining` ist maßgeblich für die Bearbeitungen. Der Codec führt keinen
Python-Code aus; ungültige Identitäten, doppelte JSON-Felder, nicht endliche
Zahlen und unvollständige Konfigurations-Snapshots werden abgelehnt.

Die bisherigen Formate 1.1–1.5 bleiben lesbar. Die Übernahme erfolgt beim
ersten neuen Speichern; unklare Zahlenwerte werden nicht durch Vergleich mit
heutigen Standards als geerbt umgedeutet. Werkzeug-/Artwechsel und freier
G-Code begrenzen die Anfangsschritte, damit die bisherige Ausgabereihenfolge
erhalten bleibt. BREAKS-/Ignore-Layer bleiben entsprechende Schrittarten.
Alte Dateien müssen zunächst unter einem neuen Namen gespeichert werden;
der Dateispeicher verhindert das Überschreiben einer Legacy-Datei mit JSON.
Schreibvorgänge ersetzen das Ziel erst nach erfolgreicher temporärer Ausgabe.
Alte Programmversionen können das Format 2.0 nicht öffnen.

Eine Referenz kombiniert ursprünglichen Layer, Blockinstanz und einen
richtungsunabhängigen Fingerabdruck der vollständigen lokalen Geometrie.
Werkstückverschiebung/-skalierung ändern die Referenz nicht. Eindeutige
Treffer bleiben verknüpft; fehlende oder mehrdeutige Treffer werden nicht
ersetzt. Eine aktive ungelöste Bearbeitung sperrt den gesamten Export vor
der Ausgabe. Die vorhandene Zieldatei bleibt erhalten, stdout bleibt leer.
Neue Konturen beim Neuimport bleiben ohne Bearbeitungszuordnung.
Auch der Parser verwendet den gespeicherten Import-Snapshot. Abweichende
Einheiten der Quelldatei werden abgelehnt, statt den Auftrag umzudeuten.

Bis P4 synchronisiert ein begrenzter Adapter Änderungen des vorhandenen
Editors in den aktiven Arbeitsgang. Bei mehreren Verknüpfungen muss der
Kontext ausdrücklich über `activate_operation` gewählt werden; ohne Kontext
gibt es keine willkürliche Vorschau oder gemeinsame Parameteränderung.
Gruppenaktionen, Listen aller Verknüpfungen, eigener/geerbter Wertdarstellung,
neue Unzugeordnet-Anzeige, Undo und Bearbeitungsbaum sind noch keine UI-Funktionen.
Die bisherige Layer-/Entities-Bedienung wird erst in P4 vollständig auf die
vereinbarte Auswahlrolle umgestellt.

## Maßgebliche Quellen

- [Reines Modell und Resolver](../../source/dxf2gcode/domain/project/machining_project.py)
- [Migration, Bindung und Projektionen](../../source/dxf2gcode/application/machining.py)
- [Codec](../../source/dxf2gcode/adapters/project/machining_d2g.py),
  [Dateispeicher](../../source/dxf2gcode/adapters/project/file_store.py)
- [GUI-Projektkoordination](../../source/dxf2gcode/presentation/qt/project_session.py),
  [CLI](../../source/dxf2gcode/application/cli_export.py)
- [Modell-/Formatregressionen](../../tests/dxf2gcode_machining_project_test.py),
  [echter Qt-Workflow](../../tests/dxf2gcode_machining_gui_test.py)
