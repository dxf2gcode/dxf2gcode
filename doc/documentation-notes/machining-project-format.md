# R3/R1b: Bearbeitungsmodell und Projektformat 2.0

Stand: **07.11.2026**, P1–P6 implementiert. P8 ist die gemeinsame Nutzerabnahme.
[Anwenderanleitung](../../docs/user-guide/machining-steps.md),
[Plan und Entscheidungen D1–D22](../planning/r3-r1b-implementation-plan.md),
[P1–P3](../archive/toolpath-refactoring-completed.md#r3-r1b-p1-p3) und
[P4–P6-Nachweis](../archive/toolpath-refactoring-completed.md#r3-r1b-p4-p6),
[Formular-Korrektur D22](../archive/toolpath-refactoring-completed.md#r3-parameter-form-correction).

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
atomare Modelloperation zur ausdrücklichen Werkzeugaktualisierung.
`MachiningCommands` bietet Profilübernahme und Schrittvorgabenänderung mit
Änderungsanzeige/Undo. Eigene Werte werden dabei nicht überschrieben.

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
Eine ausdrücklich über das vorhandene Einheitenmenü gewählte Interpretation
wird als `General.drawing_units_override` gespeichert; dabei werden Längen
und Vorschübe einmalig umgerechnet, lokale Geometriestarts bleiben unverändert.

Der Bearbeitungstab verwendet atomare Modellbefehle statt Änderungen an Original-
Layer-Mitgliedschaften. Entities/Layers haben gemäß D20 keine Exportcheckboxen
mehr. Originalauswahl zeigt alle Verknüpfungen; eine ausdrücklich aktive
Bearbeitung bestimmt Werte und Vorschau. Neue Konturen können über
„Nicht zugeordnet“ zugewiesen werden. Drag-and-drop, Menü, Sortierung und
Undo/Redo benutzen dieselbe Befehlsschicht. Ungültige Mehrfachaktionen ändern
weder Zuordnung noch History. Rückgängig/Wiederholen gilt für die neuen
Bearbeitungsaktionen; ein Import/Reload beginnt eine neue History.

Gemäß D22 sind die bisherigen Werkzeug-/Konturfelder in den Bearbeitungstab
verschoben. `MachiningParameters` verbindet sie mit den Modellbefehlen;
die direkte Legacy-Layer-/Shape-Signalverdrahtung ist für diese Felder entfernt.
Die Ersatz-Parametertabelle entfällt. Kette/Stift zeigen die Herkunft ohne
dauerhafte Textspalte; Tooltips nennen Quelle und Wert. Ein gemeinsames
Symbolmenü je Feld bietet Bearbeiten und das Rücksetzen eigener Konturwerte.
Die vier Spalten beider Gruppen sind bündig. Die gekürzte Zahlenanzeige
ändert unveränderte Modellwerte nicht. „Bearbeitungswerkzeug“ benennt die
Werkzeuggruppe. Entities und Layers liegen in zwei einklappbaren, vertikal
verstellbaren Gruppen im Tab Geometrie. Rechtsklick zeigt zuerst ein Menü
mit verknüpften Schritten. „Bearbeitung zuordnen …“ öffnet in Canvas,
Geometrie- und Bearbeitungsbaum denselben Dialog für Kopieren/Verschieben
in vorhandene oder neue Schritte. Alle Felder bleiben sichtbar und an festen
Positionen: bestehendes Ziel aktiviert die Schrittauswahl, neues Ziel
Name/Art/Werkzeug. Die Dialoggröße wird einmal für das ganze Formular gesetzt;
Zielwechsel ändern weder Aktion noch Eingaben. Toolbar-Erstellen behält den eigenen Dialog inklusive leerem Schritt.
Bei Schrittauswahl bearbeiten dieselben Felder
Schrittvorgaben, bei aktiver Kontur deren Werte. Sicherheits-/Rückzugshöhe und
Werkzeugzuweisung bleiben schrittbezogen. Die Herkunft wird nicht aus bloßer
Wertgleichheit erraten, und unveränderte Felder erzeugen keinen eigenen Wert.

Optimierung bleibt in Schritt- und Custom-G-Code-Grenzen und erhält beide
relativen Constraint-Modi. Routenendpunkte stammen aus dem vollständigen Plan
einschließlich Leads/Overcut, nicht aus einer willkürlichen Originalreferenz.
Gemäß D21 löst weiterhin nur eine andere Ausgabenummer den Profil-
Werkzeugwechselblock aus. Unterschiedliche Definitionen oder Drehzahlen bei
aufeinanderfolgend gleicher Nummer geben keine zusätzliche Drehzahl aus.
Dies ist bewusst beibehaltenes Exportverhalten, keine Exportsperre.

Die alte Eingabesynchronisierung besteht für Legacy-Adapteraufrufe weiter;
der normale neue Parametereditor benutzt Modellbefehle. Vor Entfernen der
verbliebenen Aufrufer folgt P8. Manuelle Stegregionen/Fang/Automatik bleiben P7.

Die früheren Bearbeitungs-Kontextaktionen sind gemäß D30 im Bearbeitungsbaum
und Canvas wieder verfügbar: Kontur, Taschenfräsen, Bohren, G40/G41/G42.
`MachiningCommands.set_operation_mode` arbeitet auf ausgewählten Zuordnungen.
Artwechsel erzeugen neue homogene Schritte mit kopierten Quellvorgaben und
identischer Werkzeugdefinition; je Quellschritt getrennt, direkt dahinter.
Arbeitsgang-/Geometrie-IDs und eigene Werte bleiben erhalten. Bohren setzt
bewusst G40; Kompensationswahl auf einer Bohrkreis-Zuordnung wählt wieder
Konturbearbeitung. Die gesamte Mehrfachaktion ist transaktional mit einem
Undo-Eintrag. Vorhandene Typ-/Maschinen-/Geometriesperren gelten weiterhin.
Der Canvas löst ausschließlich eindeutige oder ausdrücklich aktive Zuordnungen
auf; bei mehrdeutiger Originalauswahl sind die Aktionen deaktiviert.

D32 erhält im Canvas die bisherigen Aktionsgruppen mit Trennlinien:
Nullpunkt, Auswahl, Richtung/Konturstart, passende Bearbeitungsarten und
Kompensation. „Bearbeitung zuordnen …“ steht als separate letzte Gruppe. Der zusätzliche
Kontur-Modus-Eintrag bleibt im Bearbeitungsbaum; im Canvas führt das Abschalten
einer aktiven Pocket-/Bohraktion zur Konturbearbeitung. Auswahl aktivieren/
deaktivieren verändert nur die aufgelösten aktiven Zuordnungen.
`edit_operation_paths` nutzt isolierte Bearbeitungsansichten für die vorhandenen
Startpunktalgorithmen und speichert deren lokale Starts/Richtung atomar zurück.
Originalgeometrie und andere Referenzen bleiben erhalten. Der 3D-Klickpunkt wird
je effektiver Werkstückoberfläche aufgelöst. Manuelle Routenanzeige bleibt
unabhängig von der Vorschau. Die vertrauten DE/FR/RU-Beschriftungen werden
wiederverwendet.

Der gemeinsame Zuordnungsdialog liest im Canvas ausdrücklich ausgewählte
Bearbeitungszuordnungen statt nur einer aktiven Referenz je Original. Eine
mehrdeutige Originalauswahl bleibt gesperrt. Bestehende Ziele werden durch ihre
stabile Schritt-ID gewählt; Name, Art und Werkzeug des Zielschritts werden
dabei nicht geändert. `assign_to_step` kombiniert Transfer und erstmalige
Geometriezuordnung in einer Transaktion mit einem Undo-Schritt; neue Ziele
verwenden denselben Vertrag über `create_step`. Eigene Werte bleiben erhalten,
geerbte Werte stammen vom Ziel. Abbruch und Ablehnung verändern nichts.
„Schritt bearbeiten“ und „Schrittvorgaben bearbeiten“ entfallen im Kontextmenü:
Doppelklick/F2 und Zeilenauswahl übernehmen diese Funktionen. Die drei
Profil-/G-Code-Verwaltungsaktionen stehen unter „Erweitert“ und sind bei
mehrdeutiger Schrittauswahl gesperrt.

## Werkzeugauswahl in der Oberfläche

Änderungsdetails erscheinen über den vorhandenen Fensterlogger in der zentralen
Meldungsausgabe unten im Hauptfenster (INFO); Warnungen und Ablehnungen dort
als WARNING. Es gibt keine zusätzliche Meldungsfläche im Bearbeitungstab und
keinen pauschalen Hinweis auf verfügbare Rückgängig-Aktionen. Deren Verfügbarkeit
zeigt der Zustand der Historienknöpfe. Die eingestellte Fenster-Logstufe gilt
auch für diese Meldungen.

Die Historienaktionen im Bearbeitungstab verwenden gebogene Pfeile: links
Rückgängig, rechts Wiederherstellen. Tooltips enthalten die Tastenkürzel
Ctrl+Z/Ctrl+Shift+Z in der nativen Plattformschreibweise. Ohne verfügbare Aktion
ist der jeweilige Knopf ausgegraut.

Beim Umordnen von Schritten über Pfeile oder Drag-and-drop bleiben genau die
verschobenen Schritte ausgewählt und die aktuelle ausgewählte Zeile behält
den Tastaturfokus. Auch Undo/Redo stellt die zugehörige Auswahl wieder her;
die vollständige Exportreihenfolge wird nicht als Auswahl interpretiert.

Das Werkzeugfeld und der Schrittdialog verwenden dieselbe gemeinsame Liste
ohne Quellgruppen. Einträge zeigen T-Nummer, Durchmesser und Projekteinheit.
Vollständig gleiche Definitionen aus Projekt und Tabelle erscheinen einmal;
die Gleichheit berücksichtigt sämtliche ungerundeten Werkzeugwerte nach
Einheitenumrechnung. Beim Laden werden auch gleiche Projektdefinitionen unter
einer Identität zusammengeführt. Abweichende Definitionen derselben Nummer
bleiben mit Herkunft und abweichenden Daten erkennbar; Tooltips enthalten die
weiteren Werkzeugwerte. Nur im Projekt vorhandene Werkzeuge bleiben verfügbar.

Bei ausdrücklich gewählter Schrittzeile: Die Auswahl der passenden Tabellenvariante statt einer Projektabweichung
ersetzt die Definition für alle Schritte, die genau dieses Projektwerkzeug
verwenden. Andere Definitionen derselben Nummer bleiben erhalten. Ein Wechsel
zu einer anderen Nummer gilt nur für den ausgewählten Schritt. Rückgängig stellt
auch Werkzeugidentitäten und gemeinsame Zuordnungen wieder her. Das bloße
Öffnen der Auswahl ändert keine Werkzeugdaten; spätere Änderungen der allgemeinen
Tabelle verändern gespeicherte Projektwerte nicht automatisch.

## Werkzeugkonflikte vor dem Export

Bei einer oder mehreren ausgewählten Konturen bietet das Werkzeugfeld einen Wechsel nur für
die ausgewählten Zuordnungen an. Zuerst wird ein vorhandener kompatibler
Zielschritt gesucht; bei mehreren Treffern entscheidet der Nutzer. Ohne Treffer
ändert sich bei Vollauswahl das Quellwerkzeug direkt, sonst entsteht unmittelbar
nach der Quelle ein neuer Schritt gleicher Art/Vorgaben für die Auswahl. Eigene Werte und
Zuordnungs-IDs bleiben erhalten; Undo/Redo behandelt alle Quellen gemeinsam.
Gemischte Definitionen erscheinen als „Unterschiedliche Werkzeuge“. Andere
Parameterfelder folgen der gemeinsamen Wertedarstellung und bleiben soweit
anwendbar editierbar. Dies unterscheidet sich vom bewussten
Definitionsersatz bei ausdrücklich ausgewählter Schrittzeile: Die Konturauswahl ändert
keine nicht ausgewählten Benutzer derselben Projektwerkzeugdefinition.

Für tatsächlich aktivierte Bearbeitungen müssen Werkzeugnummer und vollständige
Projektdefinition mit der aktuellen Werkzeugtabelle übereinstimmen. Fehlende
Nummern und abweichende Werte blockieren den gesamten Export vor einer Ausgabe,
einschließlich CLI und historischen Projektdateien. Die Tabellenwerte werden
aus ihrer tatsächlich vorliegenden Einheit (`tool_units_metric`) in die
Projekteinheit umgerechnet; Anzeigepräzision und Bearbeitungswerte bleiben
unverändert. Leere und vollständig deaktivierte Schritte sowie `ignored` und
`break` verwenden für diesen Export kein zu prüfendes Werkzeug.

Die übersetzte Diagnose nennt T-Nummer, betroffene Schritte und bei fehlenden
Nummern sämtliche gespeicherten Werkzeugwerte; bei Abweichungen zeigt sie die
unterschiedlichen Projekt-/Tabellenwerte. Sie schlägt vor, das Werkzeug in der
Tabelle anzulegen/korrigieren oder ein vorhandenes Tabellenwerkzeug zuzuweisen.
Das Anlegen bleibt eine bewusste Konfigurationsänderung. Vorschau, Speichern und
Laden bleiben möglich; vorhandene G-Code-Zieldateien werden bei einer Sperre
nicht verändert und stdout bleibt leer. Explizite eigene Bearbeitungswerte
werden durch diese Definitionsprüfung nicht automatisch überschrieben.

## Auswahl und Vorschau mehrerer Bearbeitungen

Die Originalauswahl zeigt alle verknüpften tatsächlichen Werkzeugpläne. Jeder
behält Leads, Endpunkte und Tiefen sowie die bisherigen semantischen Farben.
Aktive/überfahrene Bearbeitungen werden nur durch Strichstärke hervorgehoben;
Teilauswahl punktiert die Originalkontur und zeigt k/n. Canvas-Pfade und Labels
sind direkt auswählbar, überlagerte Treffer bieten ein Menü, Strg schaltet die
Mehrfachauswahl. Die aktive Bearbeitung steuert die Hervorhebung; Parameter
aggregieren die gesamte Auswahl. Eigene Werte werden auf den ausgewählten
Zuordnungen gesetzt/entfernt, gemeinsame Rückzugs-/Sicherheitswerte auf ihren
Schritten. Jede Aktion ist atomar rückgängig zu machen. Ein lokales Start-X/Y
ändert nur die jeweilige Koordinate; die andere bleibt individuell erhalten.
Bei Originalgeometrie mit mehreren Verknüpfungen bleibt der Editor gesperrt,
bis Bearbeitungszuordnungen ausdrücklich im Baum oder Canvas gewählt wurden.
Eindeutig zugeordnete Originalkonturen dürfen gemeinsam bearbeitet werden.
Exportrouten bleiben davon unabhängig. Bildschirmdarstellung verschiebt keine
Geometrie: Das Overlay ist viewportfest, die 2D-Abbildung nutzt viewportTransform.
G40 ohne Zusatz-Offset liegt deckungsgleich auf dem Original; fachliche
Kompensationsabstände bleiben erhalten. Die 3D-Projektion behält tatsächliches Z.

Labels zeigen Schrittname, übersetztes „Kontur“ mit Originalnummer aus dem
Bearbeitungsbaum und T-Nummer; keine zusätzliche laufende Exportposition.
Die 2D-Rahmenauswahl setzt alle betroffenen Zustände vor einer gemeinsamen
Callback-Meldung. Dadurch werden Bäume und Pläne nicht einmal je Kontur neu
aufgebaut. Abwahl der bisherigen Auswahl wird genauso gemeinsam gemeldet.

## Maßgebliche Quellen

BREAKS-Schnittpunkte an einer Regionsecke werden nur einmal gezählt, auch wenn
beide angrenzenden Kanten denselben Punkt liefern. Verwendet wird die
Punktgleichheit des Geometriekerns; es kommt keine neue konfigurierbare
Zeichnungstoleranz hinzu. Reine Eckberührung erzeugt keinen Nullbreiten-Steg.
Außenreste an identischen Start-/Endpunkten werden nicht als neue Geometrie
erzeugt. Siehe [Teilungsadapter](../../source/dxf2gcode/adapters/postprocessor/breaks.py)
und [Eck-/Endpunktregressionen](../../tests/dxf2gcode_break_intersections_test.py).

Automatische Art-/Werkzeugwechsel prüfen vorhandene Ziele vor jeder Neuanlage.
Passend heißt gleiche Art, vollständige Werkzeugdefinition und identische
gespeicherte Schrittvorgaben, einschließlich Vererbungsvertrag. Namen spielen
keine Rolle. Genau ein Ziel wird wiederverwendet; mehrere führen über
`MachiningTargetChoiceRequired` zur Zielauswahl. Die Auswahl gilt nur für den
aktuellen Auftrag, Abbruch verwirft den gesamten Auftrag. IDs/eigene Werte
bleiben erhalten, Einträge werden hinten angefügt, vorhandene Zielparameter
werden nicht geändert. Explizite Neuanlage und Schrittbearbeitung bleiben
ausdrückliche Aktionen; ohne passenden Zielschritt bleibt ein vollständig
ausgewählter Werkzeug-Quellschritt bestehen, Teilmengen erhalten einen neuen.

G40-Einfahrten werden im gemeinsamen Konturplan nach dem Eintauchen vor dem
Konturschnitt ausgegeben, auch ohne interne Werkzeugradiuskorrektur. Vorschau
und Export enthalten dieselbe vorbereitete Gerade beziehungsweise den Bogen.
„Aus“ erzeugt keine Einfahrt. Die Korrektur vom 08.11.2026 ändert bereits
geschriebene Dateien nicht: neu exportieren und den neuen Werkzeugweg prüfen.

- [Reines Modell und Resolver](../../source/dxf2gcode/domain/project/machining_project.py)
- [Migration, Bindung und Projektionen](../../source/dxf2gcode/application/machining.py)
- [Atomare Befehle und History](../../source/dxf2gcode/application/machining_actions.py),
  [Bearbeitungstab](../../source/dxf2gcode/presentation/qt/machining_panel.py)
- [Tabellenabgleich und Diagnose](../../source/dxf2gcode/application/tool_table.py),
  [Exportregressionen](../../tests/dxf2gcode_tool_table_test.py)
- [Wiederverwendete Felder und Herkunftssymbole](../../source/dxf2gcode/presentation/qt/machining_parameters.py)
- [Codec](../../source/dxf2gcode/adapters/project/machining_d2g.py),
  [Dateispeicher](../../source/dxf2gcode/adapters/project/file_store.py)
- [GUI-Projektkoordination](../../source/dxf2gcode/presentation/qt/project_session.py),
  [CLI](../../source/dxf2gcode/application/cli_export.py)
- [Modell-/Formatregressionen](../../tests/dxf2gcode_machining_project_test.py),
  [echter Qt-Workflow](../../tests/dxf2gcode_machining_gui_test.py)
- [Befehlsregressionen](../../tests/dxf2gcode_machining_actions_test.py),
  [echte Drops und Übersetzungen](../../tests/dxf2gcode_machining_panel_test.py)

## Importierte Haltestege als Modifikatoren

Die Oberfläche zeigt importierte BREAKS-Regionen nicht mehr als gewöhnliche
Bearbeitungsschritte. Ihre bisherigen `kind='break'`-Einträge bleiben intern
der Speicher- und Exportvertrag; die Projektformatversion ändert sich nicht.
Globale Wirkung über Layer-/Schrittgrenzen sowie Z-Höhe und Vorschübe bleiben
erhalten. Dieselbe Regions-ID kann unter mehreren Schritten erscheinen.

Die Verknüpfungen werden aus tatsächlich wirksamen geplanten Stegbewegungen
abgeleitet: `BreakGeo`, Geometriesnapshot und `ToolpathAction` transportieren
die Regions-ID als zusätzliche Metadaten. Diese ändern keinen G-Code und
werden nicht als zweiter Projektvertrag gespeichert. Gleiche Abschnitte
über mehrere Tiefenpässe werden pro Bearbeitung nur einmal gezählt.
Der Qt-Controller [TabModifiers](../../source/dxf2gcode/presentation/qt/tab_modifiers.py)
verwaltet Referenzen, Stegmodus und bestehende atomare Befehle. Höhe/Vorschübe,
Aktivierung und Entfernen sind rückgängig machbar; das Entfernen löst die
Bearbeitungszuordnung, die Original-DXF-Geometrie bleibt erhalten.
Neue manuell gezeichnete Formen und lokale Schritt-/Konturzuordnungen sind
weiterhin P7 und werden nicht durch diese reine Darstellungszuordnung vorweggenommen.

D41 ist implementiert: Polygonale Stegregionen werden an der Originalkontur
ausgewertet. Interne Radiuskorrektur überträgt die Stellen entlang der
Geradennormalen oder Bogenradien auf die Werkzeugmittelpunktbahn;
Maschinenkorrektur erhält dieselben programmierten Originalkonturstellen.
Keine tangentiale Radiuszugabe; die Regionsbreite definiert weiterhin keine
garantierte Materialstegbreite. Eckverbindungen bleiben auf Steghöhe und
Stegbögen erhalten ihre Bogenform. Der reine Dienst
[tabs.py](../../source/dxf2gcode/domain/toolpath/tabs.py) liefert geteilte
Wertgeometrien und ausgelassene Stege. Zusätzliche `tab_geometry`-Metadaten
erhalten die wirkliche Kurve durch Umkehr, Exitadapter und Überfahrt.

Nutzerentscheidung zu Sonderfällen: Nicht eindeutig zuordenbare Stege dort
vollständig auslassen und warnen, Export weiterhin zulassen. Ein anderer
gültiger Steg derselben Region bleibt erhalten. Nicht geschlossene/nicht
polygonale Regionen werden ebenfalls mit Warnung ausgelassen. Die Warnung
`tabs.unmapped` läuft über die gemeinsamen Plan-/Exportdiagnosen und DE/FR/RU.
Taschen-Randkonturen verwenden D41, Rasterfüllbahnen ohne eindeutigen
Originalkonturpartner behalten ihre räumliche Regionsauswertung; Schleppmesser
bleiben unverändert. Projektformat/IDs ändern sich nicht. Bereits geschriebener
G-Code bleibt bestehen; nach der Verhaltensänderung neu exportieren und prüfen.
Siehe [Entscheidung und Abnahmefälle](../planning/r3-r1b-implementation-plan.md#6-reihenfolge-sonderfälle-und-haltestege).
