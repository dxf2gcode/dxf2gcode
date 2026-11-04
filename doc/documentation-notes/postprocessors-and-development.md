# Postprozessoren, Entwickler- und Projektseiten (WP9–WP13)

Stand: **04.11.2026**, Anwendungsbasis `bf1ac6d`. Neue englische Inhalte auf
`docs/remaining-guide-wp9-wp13`: 19 Seiten, fünf eigene Beispielprofile und ein
eigenes Architekturdiagramm. [Assetnachweis](../../docs/assets/examples/postprocessors/README.txt).

## WP9: maßgebliche Quellen

- [Postprozessorschema](../../source/dxf2gcode/adapters/postprocessor/postprocessorconfig.py):
  Leser 8/8.1/8.2/8.3, aktueller Stand 8.3, `lin_mov_xyz`, vollständige
  General/Program-/Format-/Zeilennummern-/Wechselabschnitte.
- [Dialekt](../../source/dxf2gcode/adapters/postprocessor/dialect.py) und
  [Exporter](../../source/dxf2gcode/adapters/postprocessor/postprocessor.py):
  aktuelle Platzhalter, Headerunterschiede und Formatierungszustand.
- [Deutsche Makroreferenz](../tool-change-macros.md) und
  [LinuxCNC-Ablauf](../linuxcnc-manual-tool-change.md): Legacy gegenüber
  next_start_at_retract, absolute Makroziele bei G91, skalare Referenzen,
  H-Zuordnung und Einschränkung freier Baumzeilen. Englischer Inhalt mit diesen
  aktuellen Verträgen abgeglichen; alte Testzahlen nicht als neu ausgeführt
  ausgegeben. Offizielle G43-/manualtoolchange-Quellen erneut geöffnet.

## WP10: fünf einzeln abgegrenzte Beispiele

1. **Laser:** Grbl 1.1, ladbares Nullleistungsprofil mit M4 S0 beim Schnitt
   und M5 S0 bei Travel/Ende. Keine automatische Übernahme der Fräsdrehzahl
   als Leistung. `$32`, `$30`/`$31` und reale Hardware separat prüfen.
2. **Heißdraht:** LinuxCNC 2.9 XYUV, parallele identische Profile an beiden
   Enden; Rapid und Schnitt gleichermaßen abgebildet. Keine Heizung oder
   unabhängige Vierachs-/Konusplanung. FOAM-Anzeige ist kein Kinematiksetup.
3. **Drehen:** LinuxCNC 2.9, G18/G7/G94/G97, Z längs und X Durchmesser;
   eigenes offenes Stufenprofil. Bögen linearisiert wegen anderer Offset-
   Semantik im Durchmessermodus. Kein automatischer Werkzeug-/Spindelstart
   und keine freie X-Rückzugsbahn behauptet.
4. **DXF:** eigenes ladbares Linien-Demoprofil. Schema und synthetisches LINE-
   Template geprüft; kein vollständiger Export oder CAD-Reimport.
5. **Python:** eigenes ladbares Ereignislisten-Profil. Schema und synthetische
   Records mit ast.parse geprüft; Ausgabe nicht ausgeführt, keine Plugin-API.

Der Anwender wünschte konkrete Beispiele aus dem Hobby-/Handwerkerbereich.
Die drei Steuerungsbeispiele sind entsprechend neu ausgearbeitet, ohne
historische Fremdprofile zu übernehmen. Schema, synthetische Formatierung und
eigener DXF-Import wurden geprüft, kein Interpreter oder realer Aufbau.
Maßgebliche Primärquellen: offizielles Grbl-1.1-Laser-/Konfigurations-Wiki und
LinuxCNC-2.9-Handbuch (AXIS Foam, INI, Lathe und G-Code), auf den Seiten verlinkt.

## WP11/WP12: aktuelle Entwicklerquellen

[Paketmetadaten](../../source/pyproject.toml),
[Quell-README](../../source/README.md),
[Runner](../../tests/run_tests.py), [tox](../../tox.ini),
[Qt-Assets](../../source/tools/build/qt_assets.py),
[Übersetzungen](../../source/tools/build/translations.py),
[Makefile](../../source/Makefile), [Checks](../../.github/workflows/checks.yml),
[geteilte Paketprüfungen](../../.github/workflows/package-checks.yml),
[Release](../../.github/workflows/publish-release.yml) und
[Pages](../../.github/workflows/documentation-pages.yml) gegen die Anleitung
verglichen. Python-Mindestdeklaration nicht mit frischer Plattformabnahme
gleichsetzen. Shared runtime/Qt-Kopplung ausdrücklich erhalten; Architektur-
diagramm ist eine Verantwortungsübersicht, kein Beweis kompletter Entkopplung.

Compile-only und TS-Update/Übersetzungsprüfung getrennt; generierte Dateien
bleiben ignoriert. CONTRIBUTING und Tests-README mit der inzwischen geltenden
Dokumentationsausnahme/aktuellen CI-Namen abgeglichen. Kein Fast-/Voll-/Buildlauf.

## WP13: Veröffentlichung und Herkunft

[Pipeline](../release-pipeline.md),
[Downloadnotizen](downloads-and-versions.md),
[Rechteaufstellung](../migration/sourceforge/RIGHTS.md) und
[Inventar](../migration/sourceforge/manifest.json) sind Grundlage.
Keine neue stabile Version behauptet, keine ungeklärten Originale/Archive
veröffentlicht. Lizenzseite trennt Softwaremetadaten, eigene Beispiele,
Projekt-Nutzungserlaubnis des Brandings und fremde Inhalte.

Die Website enthält nun alle geplanten Themen, aber technische/visuelle
Kapitelabnahme, Veröffentlichung sowie optionale historische Wiederverwendung
und reale Steuerungs-/Plattformabnahmen bleiben getrennte Statusangaben.
