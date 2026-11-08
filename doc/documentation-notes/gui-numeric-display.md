# GUI-Zahlenanzeige und skalierbare Parameterformulare

Stand: 08.11.2026. Nutzerkorrekturen zu R3-UI, Entscheidungen D28/D29 und kompakte Wertepaare.

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

Vier Group Boxes gliedern die Werte: Z-Werte, Vorschübe, Lead in/out und
Offset. `ParameterRow` stellt jeweils zwei Werte nebeneinander dar, auch bei
kleiner Breite. Kurze Beschriftungen enthalten die Einheit direkt. Zahlenfelder
zeigen ungefähr acht Zeichen und erlauben weiterhin volle Eingabepräzision.
Jeder Herkunftsknopf bleibt 32 Pixel breit und folgt mit 2 Pixel Abstand direkt
auf sein Feld; ein Dehnabstand kommt erst danach. Werkzeugauswahl und Drehzahl
stehen in einer gemeinsamen Kopfzeile. Lead-/Überfahrtwerte bleiben im
Konturbereich und verändern keine Werkzeugdefinition. Der Durchmesser steht
bereits in der Werkzeugauswahl. Ein expliziter abweichender Alt-Startradius
bleibt als Altwert erhalten. Maschinenfilter verbergen die komplette betroffene
Zelle: Messerparameter nur bei Dragknife, Standard-Fräsleads/Überfahrt nur bei
Fräsen. Andere Werte derselben Zeile bleiben sichtbar. Die Anzeige ändert weder
Modellwerte noch Befehlsverlauf.

Feld-Tooltips erklären die Funktion des Parameters, ohne Herkunftsangaben.
Nur der Symbol-Tooltip nennt Parameter, Wert und Herkunft: Kontur und Schritt
bei eigenen Konturwerten, Schritt bei eigenen Vorgaben beziehungsweise die
geerbte Schritt-/Werkzeug-/Projektquelle. Anzeigepräzision und Speicherwert
bleiben getrennt.

Im Bearbeitungstab bleibt nur der QSplitter zwischen Baum und gesamtem
Eingabebereich. Der innere Werkzeug-/Konturtrenner und die beiden Klappbereiche
entfallen. Ein gemeinsamer Scrollbereich enthält Kopfzeile und vier normale
Group Boxes, oben ausgerichtet mit Leerraum ausschließlich darunter. Ohne
Bearbeitung sind die Werte gesperrt. Sammelauswahl zeigt gleiche geerbte Werte
grau, gleiche Werte mit eigenen Overrides normal und unterschiedliche Werte
als editierbaren Platzhalter „Unterschiedlich“. Es wird exakt vor der
Anzeigerundung verglichen. Herkunft folgt gespeicherten Overrides, nicht der
Gleichheit mit Vorgaben; gemischte Herkunft hat ein eigenes Symbol mit Zählern
und Quellen im Tooltip. Eingaben/Dropdown-Auswahl betreffen alle ausgewählten
Bearbeitungen in einem Undo-Schritt. Platzhalter und unveränderte Bestätigungen
werden nie gespeichert; `NumericDisplay` erhält bei gemischten Werten `None`.
Nicht für alle anwendbare Parameter sind einzeln gesperrt. Rücksetzen entfernt
die jeweiligen eigenen Konturwerte; Schrittwerte und Werkzeugdaten bleiben.
Rückzug/Sicherheit sind weiterhin gemeinsame Schrittwerte mit entsprechendem
Wirkungshinweis am Symbol. Mehrdeutige Originalgeometrieauswahl sperrt auch das
Werkzeugfeld bis zur ausdrücklichen Auswahl von Bearbeitungszuordnungen.

Die Zahlenfelder der Konfiguration verwenden direkte Eingabe ohne sichtbare
Schrittknöpfe. Ihre bevorzugte Breite folgt einer kompakten Zahlendarstellung,
nicht der internen Speicherpräzision. Formularfelder sind auf 80–160 Pixel
begrenzt; Werkzeugspalten verteilen die verfügbare Tabellenbreite gleichmäßig.
Längere technische Spaltennamen werden umgebrochen und bleiben als Tooltip
verfügbar. Die Standardaufteilung berücksichtigt die fertige Dialoggröße.
Eingabe, Validierung und Präzision bleiben davon unabhängig.

Die zentrale Meldungsausgabe im Hauptfenster besitzt einen vertikalen Trenner
direkt oberhalb ihrer Fläche. Ziehen verändert ihre Höhe gegenüber dem
Zeichen-/Bearbeitungsbereich; die frühere feste Maximalhöhe entfällt.
Anfangs sind etwa 100 Pixel, mindestens 48 Pixel vorgesehen. Die Größenänderung
verändert weder Meldungsinhalt noch Projektwerte.

`WindowLayout` hält beim Fenstervergrößern die linke Breite und untere
Meldungshöhe konstant. Im Bearbeitungstab wächst der Baum, nicht der
Parameterbereich. QSettings speichert manuelle Trennergrößen sowie die
Klapppositionen der Geometriegruppen. Alte Parameter-Trennerzustände werden
ignoriert; Mindestmaße schützen den Canvas.

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
