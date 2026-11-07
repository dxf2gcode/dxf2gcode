# GUI-Zahlenanzeige und skalierbare Parameterformulare

Stand: 07.11.2026. Nutzerkorrektur zu R3-UI, Entscheidungen D28/D29.

Unter Optionen → Konfiguration → Allgemeine Einstellungen → Zahlenanzeige
stehen `Display.decimals_mm` (Standard 3), `decimals_in` (5) und
`decimals_angle` (1) und `decimals_feed` (1), jeweils 0–12. Längen folgen
der Einheit; Vorschübe und Winkel ihrer jeweils eigenen Einstellung; ganzzahlige Nummern/Drehzahlen bleiben
unverändert. Die Einstellungen gehören zum Anwendungsprofil, nicht zu den
Bearbeitungsparametern eines Projekts. Alte unterstützte Profile erhalten die
neuen Vorgaben über Konfigurationsversion 9.21. Bereits gespeicherte Anzeigeeinstellungen
bleiben erhalten; insbesondere wird ein vorhandener Winkelwert 3 nicht
automatisch überschrieben.

`presentation.qt.numeric_display` enthält die gemeinsame Anzeigeformatierung.
`NumericDisplay` verwaltet Zahlen in QLineEdits: ohne Fokus feste
Nachkommastellen, beim Bearbeiten der vollständige gespeicherte Float-Wert.
Unveränderte Felder werden nicht aus ihrem gerundeten Text zurückgeschrieben.
Auch die Rückgabe numerischer Popups erhält unbearbeitete Originalwerte.

`CorrectedDoubleSpinBox` trennt ebenfalls Anzeige und interne Genauigkeit.
Die interne Qt-Nachkommastellenbegrenzung steht auf 323, während
`textFromValue` die Anzeige formatiert. Eingaben, Werteübernahme, Fokuswechsel
und Schritte verwenden die vollständigen Werte. Ein bislang geladenes
`_original_value` bleibt unverändert, bis die Eingabe ausdrücklich geändert
wird. Punkt und Komma werden weiterhin angenommen. Spezielle dimensionslose
Prozentangaben können ihre eigene Anzeigepräzision behalten.

Die Anzeige ist kein Berechnungsschritt. Projektdatei, Planung und Export
verwenden die gespeicherten beziehungsweise berechneten Werte. Es gilt die
bestehende Float-Genauigkeit; die Änderung führt kein Dezimalzahlen-Datenmodell
ein. Die Nachkommastellen des Postprozessors sind ein eigener Ausgabevertrag.

Beide Parametergruppen besitzen gemeinsame Spaltengewichte aus den jeweils
breitesten Beschriftungen, Einheiten und Wertefeldern. Die Startbreite des
linken Bereichs wird daraus berechnet. Beim Verkleinern skalieren diese drei
Spalten, Beschriftungen dürfen umbrechen; die Herkunftsspalte bleibt 32 Pixel
breit. Einheiten sind in beiden Gruppen gleich ausgerichtet. Die alte starre
Mindestbreite und das horizontale Abschneiden des gesamten Formulars entfallen.

Maßgebliche Quellen:

- [Formatierung und Fokusverhalten](../../source/dxf2gcode/presentation/qt/numeric_display.py)
- [Konfigurationsschema](../../source/dxf2gcode/adapters/config/runtime_config.py),
  [Menüfelder](../../source/dxf2gcode/presentation/qt/configuration_widgets.py)
- [Konfigurationsfelder und Werkzeugtabelle](../../source/dxf2gcode/presentation/qt/configwindow.py)
- [Parameterlayout](../../source/dxf2gcode/presentation/qt/machining_parameters.py)
- [Präzisions- und Eingabetests](../../tests/dxf2gcode_numeric_display_test.py),
  [Projekt-/Exportnachweis](../../tests/dxf2gcode_numeric_precision_test.py)
- [Anleitung](../../docs/user-guide/machining-steps.md),
  [Abschlussnachweis](../archive/toolpath-refactoring-completed.md#r3-numeric-layout)
