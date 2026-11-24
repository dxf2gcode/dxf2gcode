# Oberfläche, Import und Projekte (WP2)

Stand: **03.11.2026**. Neue englische Kapitel:
[Interface and navigation](../../docs/user-guide/interface-and-navigation.md)
und [Import drawings and save projects](../../docs/user-guide/import-and-projects.md).

WP2 verwendet WP1s eigene Zeichnung und aktuellen Screenshot; Herkunft und
Umgebung bleiben in der [Assetbeschreibung](../../docs/assets/examples/first-dxf/README.txt).
Das Projektbeispiel wird vom Anwender mit dieser Zeichnung gespeichert, statt
eine D2G-Datei mit einem rechnergebundenen Autorenpfad zum Download anzubieten.

## Maßgebliche lokale Quellen

- [MainWindow](../../source/dxf2gcode/presentation/qt/application.py): `open`,
  `OpenFileDialog`, `load`, `reload`, `saveProject`, `loadProject`, Modifier.
- [2D-Canvas](../../source/dxf2gcode/presentation/qt/canvas2d.py): Auswahl,
  Mausrad und Panning; [Menütexte](../../source/dxf2gcode/presentation/qt/resources/dxf2gcode_ui.py).
- [DXF-Parser](../../source/dxf2gcode/adapters/dxf/parser.py) und
  [Zeichnungsmodell](../../source/dxf2gcode/application/drawings.py): unterstützte
  Entitäten, Konturbildung und Layerfilter.
- [Projektfassade](../../source/dxf2gcode/domain/project/project.py): gespeicherte
  Werte, Originalpfad, Abgleich über Layernamen/Geometriehash und neue Konturen.
- [D2G-Codec](../../source/dxf2gcode/adapters/project/legacy_d2g.py): Versionen
  1.1–1.5, validierte Daten und Migration. Die Formatversion ist keine App-Version.
- Bestehende Verträge:
  [Projektadapter](../../tests/dxf2gcode_project_adapter_test.py),
  [Projekt-/Leadwerte](../../tests/dxf2gcode_leadmove_project_test.py),
  [Import](../../tests/dxf2gcode_import_contract_test.py) und
  [Importfilter](../../tests/dxf2gcode_import_filters_test.py).

## Für spätere Kapitel erhalten

### Ansicht und feste Werkzeugleiste (24.11.2026)

Im aktuellen Quellstand schaltet das Würfelsymbol **Raumansicht** in der
Gruppe **Ansicht** auf 3D. Fehlt es, unter Optionen/Konfiguration in den
allgemeinen Einstellungen **3D-Ansicht mit VisPy (Neustart erforderlich)**
aktivieren und neu starten. Der Renderer benötigt PyQt6 und VisPy; bei einem
Startfehler bleibt die 2D-Ansicht erhalten. Quellen:
[Ansichtsleiste](../../source/dxf2gcode/presentation/qt/view_comparison.py),
[Konfigurationsfelder](../../source/dxf2gcode/presentation/qt/configuration_widgets.py).

Der Stegmodus bleibt nach dem Zeichnen und nach Undo aktiv; Escape beendet
zunächst eine laufende Zeichenaktion, ein weiteres Escape den Modus.
Das Rechtsklickmenü bleibt auch im Stegmodus erreichbar. Die obere
Werkzeugleiste bleibt sichtbar: Das Qt-Standardmenü zum Ausblenden ist
gesperrt; das Zeichnungsmenü bietet ebenfalls keinen Sichtbarkeitsschalter.
Ein früher gespeicherter ausgeblendeter Zustand wird beim Start korrigiert.
Unter Windows mit PyQt5/PyQt6 lokal geprüft; Linux Mint 22.3 MATE und
veröffentlichte Pakete sind noch nicht geprüft. Quellen:
[Hauptfenster](../../source/dxf2gcode/presentation/qt/application.py),
[Kontextmenü](../../source/dxf2gcode/presentation/qt/canvas.py),
[Steginteraktion](../../source/dxf2gcode/presentation/qt/tab_modifiers.py).

Datei/Reload liest die Zeichnung erneut; das interne `Project.reload` für
bestimmte Transformationen ist ein anderer Pfad. Beide nicht als generelle
Einstellungserhaltung bei beliebigen CAD-Änderungen beschreiben. Konfiguration,
Postprozessor, Zeichnung und D2G bleiben getrennte Artefakte. Keine portable
relative Pfadauflösung versprechen. Auswahl/Aktivierung, Reihenfolge und
Optimierung in WP3 aufgreifen, ohne Klickreihenfolge mit Exportfolge gleichzusetzen.

Code- und Dokumentationsprüfung belegen keine tatsächliche PDF-/PS-Konversion,
Installation oder Maschinenfahrt. Der einzige bisherige GUI-Dateiexportnachweis
dieses Inhaltsstrangs bleibt der bei WP1 dokumentierte Ablauf.
