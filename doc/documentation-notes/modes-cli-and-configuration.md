# Maschinenarten, CLI und Konfiguration (WP6–WP8)

Stand: **03.11.2026**. Neue englische Kapitel im User Guide, beginnend mit
[Haltestegen](../../docs/user-guide/tabs-and-breaking-layers.md). Inhalte auf
Quellbasis `6c4bcc9`; nur Dokumentation und eigene Assets geändert.
[Assetherkunft und Umgebung](../../docs/assets/examples/tabs/README.txt).

## WP6

- [BREAKS-Regionen](../../source/dxf2gcode/adapters/postprocessor/breaks.py),
  [Konturstrategie](../../source/dxf2gcode/domain/toolpath/strategies/contour.py),
  [Bewegungen](../../source/dxf2gcode/domain/toolpath/movements.py) und
  [Pass-Verträge](../../tests/dxf2gcode_breaks_pass_test.py): Steg-Z absolut;
  spätes Verarbeiten kann vorher entfernte Materie nicht wiederherstellen.
  Das Diagramm verwendet daher Pass 2 = Steg-Z = −1 und Endtiefe −1,5 mm.
- [Drehformatierung](../../source/dxf2gcode/adapters/postprocessor/dialect.py):
  Faktor 2 bei zweiter planarer Position und zugehörigem Zentrumsoffset;
  kein automatischer Beleg für X/Z-Achsabbildung oder fehlende Z-Kommandos.
  [Referenzausgabe](../../tests/golden/slices_lathe_closed.gcode) enthält
  weiterhin dritte-Achse-/Tiefenbewegungen. Die GUI-Beschriftung allein reicht
  deshalb nicht als Funktionsbeschreibung.
- [Messeranleitung](../drag-knife-usage.md),
  [Messerstrategie](../../source/dxf2gcode/domain/toolpath/strategies/knife_passes.py)
  und [Regressionen](../../tests/dxf2gcode_knife_passes_test.py): Offset ist
  angezeigter Spitzenversatz, intern halber Durchmesser. Unbekannte Stellung,
  Rampenkorrektur, Zusatzdurchgang und Nahtüberfahrt getrennt erklären.
- Historische Links aus [Schleppmesser-Notizen](drag-knife.md) am 03.11.2026
  geöffnet/geprüft. Keine fremden Assets übernommen. Lokale Forums-Testdateien
  bleiben Regressionseingaben und sind nicht automatisch Dokumentationsdownloads.

## WP7

- [Argumentparser und direkte Exportpfade](../../source/dxf2gcode/presentation/qt/application.py):
  quiet + input + export und unterstützte Endung vermeiden MainWindow. Andere
  Aufrufe können GUI initialisieren. Postprozessorauswahl über Beschreibung,
  unbekannter Name fällt aktuell auf Index 0 zurück. Fehlerstatus meist 2.
- [CLI-Anwendung](../../source/dxf2gcode/application/cli_export.py):
  DXF-Modell gegenüber gespeichertem D2G unterscheiden. Fehlende Projektzeichnung
  kann nicht über einen Dateidialog gesucht werden. Kein Universal-xvfb-Rezept.
- Nur `--help` wirklich ausgeführt; die Dateiexport-Kommandos sind codegeprüfte
  Anwendungsbeispiele. Bestehenden WP1-GUI-Exportnachweis nicht als CLI-Nachweis
  ausgeben. Stdout-Option bei Dateien beachten; quiet unterdrückt nicht alle Logs.

## WP8

- [Schema und Profile](../../source/dxf2gcode/adapters/config/runtime_config.py),
  [Ordnerbasis](../../source/dxf2gcode/domain/constants.py),
  [Widgetzuordnung](../../source/dxf2gcode/presentation/qt/configuration_widgets.py):
  Logging unter Software config; Import unter Output settings. Kein AppData-Pfad.
  Schema 9.19 akzeptiert 9.11–9.19. Unbekannte Version nicht durch bloßes
  Ändern der Versionsnummer erzwingen; `.bad`-Datei separat sichern.
- [Layerparser](../../source/dxf2gcode/domain/project/layercontent.py):
  Großschreibung, Separator und Aliase prüfen; Paare werden sequenziell angewandt.
  Toolnummer vor expliziten Dimensionen, sonst kann Toolauswahl Werte ersetzen.
  Ol ist nur Länge, nicht Overcut-Aktivierung. Lim und Lom haben andere Zahlen.
- Beispielnamen mit aktuellem Parser bestätigt. Neue englische Screenshots aus
  frischem temporärem Profil, keine Nutzereinstellungen dargestellt.

Für WP9 die Postprozessor-/Werkzeugwechselreferenz gesondert ausarbeiten.
Keine Dreh-, Messer- oder Fräs-Maschinenabnahme aus diesen Erklärungen ableiten.
