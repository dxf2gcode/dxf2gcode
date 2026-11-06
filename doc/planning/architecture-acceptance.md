# A1: Reichweite der Architekturabnahme

Stand: **05.11.2026**, geprüfte Quellbasis `7246810` im Windows-Checkout.
Diese Bestandsaufnahme trennt belegte Architekturverträge, konkrete Lücken
und mögliche Folgeschritte. Sie ist keine vollständige Maschinen-, Profil-,
Paket- oder Plattformfreigabe.

**Aktueller Status vom 06.11.2026:** Die vollständige Variante aus dem
[Abschlussplan](a1-completion-plan.md) ist umgesetzt. Pocket-Gültigkeit,
Projekt-/GUI-Aktualisierung und auftragsweiter Exportabbruch sind angebunden;
sämtliche Domain-/Application-Module werden ohne Qt, Runtime-Globals oder
konkrete Adapter importiert. [Abschluss und aktuelle Nachweise](../archive/toolpath-refactoring-completed.md#a1-complete).
Die folgenden Befunde beschreiben ausschließlich die historische Quellbasis
`7246810` vor der Umsetzung.

## Belegte Abdeckung

Die relevante Matrix ist repräsentativ, kein kartesisches Produkt aller
Maschinenarten, Geometrien, Profile und Bearbeitungsparameter. Die folgenden
Verträge sind mit konkreten Regressionen verbunden:

| Bereich | Beleg und Reichweite |
| --- | --- |
| Unveränderliche Planwerte und Diagnosen | [Planvertrag](../../tests/dxf2gcode_toolpath_contract_test.py): wiederholbare Planung, unveränderte Requests, vollständige Tiefenpässe, Warnungen mit Plan und Fehler ohne Plan |
| Fräsen, Softwarekompensation | [Falltests](../../tests/dxf2gcode_toolpath_slices_test.py): offene/geschlossene Kontur, alternierende Pässe und passende Golden-Ausgaben |
| Maschinenkompensation G41/G42 | Dieselben Falltests: offene/geschlossene Kontur, beide Seiten, Rücksetzen zwischen Tiefenpässen ein/aus und Seitenwechsel bei Umkehr |
| Leads, Überfahrt und Tabs | Falltests: Lead-Aktionen vor/nach den Schnittpässen, ungültiger Auslauf ohne Plan, ausgewählte Tab-Pässe und Z-Höhen |
| Software-Pocketing | Falltests: G40/G41/G42, Tiefen, sichere Verbindungen und Goldens; keine Aussage über Taschen mit Maschinenkompensation |
| Bohren | Kreis und Punktloch, direkte/mehrfache Zustellung und XY-/XYZ-Projektion; [B1/B2](../../tests/dxf2gcode_machining_modes_test.py) ergänzt widersprüchliche Drill/Pocket/G41/G42-Zustände, Projekt-Roundtrip, Vorschau und Auflösung |
| Schleppmesser | Falltests plus [Messerregressionen](../../tests/dxf2gcode_knife_passes_test.py): Spitzenweg, Schwenken, Rampen, Richtungsumkehr, Tiefen und G90/G91; keine Freigabe von Pocketing am Messer |
| Drehen | Falltests: offene/geschlossene Linie/Bogen in G40, Durchmesserfaktor und bestehende Lead-Grenzen; keine generelle Dreh-/Pocket-/G41/G42-Abnahme |
| Profile und Serialisierung | [Profiltests](../../tests/dxf2gcode_postpro_config_test.py), [Werkzeugwechseltests](../../tests/dxf2gcode_tool_change_test.py), Profilfähigkeiten und reale formatierte Endpunkte in den Falltests; keine beliebigen Anwenderprofile |
| Vorschau/Export | Falltests vergleichen denselben Plan, wiederholte Ausgabe, formatierte Endpunkte und 2D-/3D-Projektionen; [Vorschauregressionen](../../tests/dxf2gcode_toolpath_preview_test.py) ergänzen Edits und Grundgeometrie. Painter-/Mock-OpenGL-Nachweise sind keine GPU-Abnahme |

Das frühere Tor „alle unterstützten und nicht unterstützten Kombinationen
vollständig erfasst“ ist damit zu weit formuliert. Weitere Tests werden an
einen benannten Vertrag oder einen reproduzierbaren Befund gebunden.

## Genaue Importgrenze

Der [Importgrenztest](../../tests/dxf2gcode_architecture_boundary_test.py)
importiert in frischen Prozessen alle Module unter `domain/geometry` und
`domain/toolpath`, ohne PyQt, Presentation, Runtime-Globals oder Postprozessor
zu laden. Der Planer erhält explizite Werte statt eines Postprozessorobjekts.
Die Übergabe eines expliziten Geometriedienstes für Leads bleibt zulässig.

Zusätzlich sind `application.importing` und `application.projects` sowie
`ProfileDialect` und `ToolpathGCodeExporter` durch benannte Importtests
abgesichert. Das bedeutet **nicht**, dass jedes Application-Modul frei von
Qt oder konkreten Adaptern ist.

Die statische Prüfung der tatsächlichen Importanweisungen zeigt:

| Verbleibende Kopplung | Bedeutung |
| --- | --- |
| `domain/project/shape.py` | Runtime-Globals, Qt-Übersetzung und `QMessageBox`; die Paketzuordnung allein macht Shape nicht Qt-frei |
| `domain/project/layercontent.py` | Runtime-Globals und Qt-Übersetzung |
| `domain/project/project.py` | Runtime-Globals, Qt und konkreter Legacy-Projektadapter; außerdem GUI-Elternaufrufe |
| `domain/constants.py` | Qt-Bindung für Runtime-Versionsangabe; außerhalb der geprüften Geometry-/Toolpath-Pakete |
| `application/drawings.py` | Modellaufbau importiert `LayerContent` und erbt dadurch dessen Kopplungen |
| `application/cli_export.py` | Konkrete Reader-/Vorbereitungsadapter und Projektmodelle; kein Nachweis allgemeiner Qt-freier CLI-Orchestrierung |

## Konkrete zusätzliche Falllücke: Pocket-Zustände

Einmalige Diagnoseaufrufe nutzten `build_shape` aus den Golden-Testhelfern,
eine geschlossene 100×100-Kontur, Werkzeugdurchmesser 20, G40 und ausgeschaltete
Leads. Nach Setzen von `Pocket=True` wurde neu vorbereitet und der echte
Planungsdienst aufgerufen. Beobachteter Iststand:

| Maschinenart / Kompensation | Befund |
| --- | --- |
| Fräsen / Maschinenkompensation | Plan ohne Diagnose, keine Aktionen mit Rolle `pocket` |
| Schleppmesser / Softwarekompensation | Plan ohne Diagnose, keine Aktionen mit Rolle `pocket` |
| Drehen / Softwarekompensation | Plan ohne Diagnose, 55 Aktionen mit Rolle `pocket` |

Die [GUI](../../source/dxf2gcode/presentation/qt/canvas.py) bietet Pocketing
bei Maschinenkompensation und am Schleppmesser nicht an. Geladene oder direkt
gesetzte Werte werden dadurch nicht automatisch ungültig. Der
[Planer](../../source/dxf2gcode/domain/toolpath/planner.py) prüft derzeit den
Drill-/Pocket-/Kompensationskonflikt, jedoch keine vollständige Maschinen-/
Pocket-Gültigkeitsmatrix. Die Diagnoseaufrufe bilden gesetzte Modellzustände
nach, keinen vollständigen GUI-/CLI-Projektladeablauf.

Für Drehen ist die Lage ausdrücklich uneinheitlich: Ein vorhandener
[Menütest](../../tests/dxf2gcode_pocket_comp_mode_test.py) heißt zwar
`test_the_pocket_mill_is_not_offered_for_the_lathe`, erwartet aber tatsächlich
das Vorhandensein von „Pocket Mill“. Deshalb aus dem Testnamen kein Verbot
ableiten und keinen stillen Verhaltenswechsel implementieren.

**Folgeentscheidung A1-P:** Zulässigkeit und Verhalten dieser drei Zustände
festlegen. Vorschlag für die heute bereits in der GUI gesperrten Fälle:
Projektwerte erhalten und eine stabile blockierende Diagnose an Vorbereitung,
Planung, Vorschau sowie GUI-/CLI-Export weiterreichen. Für Drehen zuerst den
gewünschten Funktionsumfang entscheiden. Danach gezielte Projektlade-,
Planungs-, Vorschau- und Exportregressionen, keine Vollmatrix auf Verdacht.
Die fachliche Entscheidung und Implementierung sind noch nicht freigegeben.

## Vorschlag zur weiteren Importentkopplung

**Folgeschritt A1-I:** Die bestehende reine Kernabgrenzung erhalten. Eine
weitergehende Entkopplung gesondert planen, in dieser Reihenfolge:

1. Aufgelöste Einstellungen und Meldungen von Shape/Layer als explizite
   Werte bzw. Diagnosen übergeben; Qt-Präsentation außerhalb des Modells.
2. Projektserialisierung und GUI-Koordination über die vorhandenen Ports/
   Anwendungsfälle führen; `.d2g`-Roundtrip und Migration unverändert halten.
3. Konkrete Adapter im CLI-Aufbau injizieren; anschließend die erweiterten
   Module mit frischen Importprozessen ohne Qt/Runtime prüfen.

Neue Importgrenzen erst nach tatsächlicher Umstellung abnehmen. Keine
pauschale Behauptung „Domain und Application vollständig Qt-frei“.

## Nachweis dieser Untersuchung

Ein fokussierter Lauf unter Windows/Python 3.11/PyQt5 bestand mit **41 Tests**:

```powershell
$env:DXF2GCODE_QT = '5'
$env:PYTHONPATH = 'tests'
python -m unittest dxf2gcode_architecture_boundary_test dxf2gcode_toolpath_contract_test dxf2gcode_toolpath_slices_test dxf2gcode_machining_modes_test -q
```

Ergänzt durch AST-Importprüfung und die drei oben beschriebenen
Pocket-Diagnoseaufrufe. Sonstige Testdateien wurden für die Zuordnung gelesen;
ältere Prüfergebnisse sind keine neuen Testläufe. Keine Quellcodeänderung,
Vollsuite, Debian-/SSH-, Paket- oder Maschinenprüfung durch A1.
