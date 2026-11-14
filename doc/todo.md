# DXF2GCODE: offene Aufgaben

Stand: **14.11.2026**.

Diese Liste enthält ausschließlich offene Arbeiten und Entscheidungen.
Die Reihenfolge ist ein Vorschlag, kein pauschaler Umsetzungsauftrag.
[Abschlüsse und Prüfnachweise](archive/toolpath-refactoring-completed.md),
[Detailanforderungen](planning/open-task-details.md),
[Dokumentationsnotizen](documentation-notes/README.md) und
[Arbeits-/Prüfregeln](working-agreements.md) werden getrennt gepflegt.

## Empfohlene Reihenfolge

**Release-Freigabe:** Version **2.0.0** wird erst nach Abarbeitung der gesamten
Todo freigegeben. Der Develop-Release **2.0.0.dev12** vor Umsetzung von
R3/R1b ist veröffentlicht und seine Downloads sind geprüft;
[Nachweis](archive/toolpath-refactoring-completed.md#develop-r3-checkpoint).
Die Paket-/Installationsabnahme ist für den aktuellen Featureabschluss eingeplant.

| Priorität | Offenes Thema | Vor Umsetzung klären |
| --- | --- | --- |
| Releaseabschluss | [CI1 – Betriebsabnahme](#ci1) | Erste stabile Veröffentlichung und Codesignierung bleiben getrennt; Kandidaten-Paketabnahme bestanden |
| Separat | [M1 – macOS](#m1) | Konkrete Zielumgebung vor einer macOS-Abnahme festlegen |
| Optional | [LC1 – Automatischer LinuxCNC-CLI-Filter](#lc1) | Bedarf zusätzlich zum abgenommenen interaktiven GUI-Filter |
| Vor Abschluss durch Nutzer | [DOC1 – abschließende Sichtprüfung](#doc1) | Aktuelle Anleitung/Bilder fertig; Nutzer prüft die Darstellung am Schluss |
| Integration/Release | [Featureabschluss und Develop-Release](planning/maschining-project-release-plan.md) | Nutzerabnahme und IGNORE abgeschlossen; Anleitung/Bilder und Installationsumfang gemäß Plan |
| Zurückgestellt | [Teilkonturen](#teilkonturen) | Mit dem neuen Bearbeitungsmodell abstimmen |
| Optional | [Q1 – PySide6](#q1) | Konkreter Nutzungsbedarf und dauerhafter Prüfaufwand |
| Optional, später | [PP1 – Separater Drehzahlblock](#pp1) | Postprozessorvertrag für Drehzahländerungen bei gleicher Werkzeugnummer abstimmen |
| Optional | [GUI1 – Ribbon-Menüband](#gui1) | Bedienentwurf, Bibliothekswahl und Windows-/Linux-Kompatibilität |

Alle geplanten Dokumentationsthemen **WP1–WP13** sind ausgearbeitet und
veröffentlicht. Als nächstes konkrete fachliche Rückmeldungen einpflegen;
weitere Software-/Plattform-/Maschinenabnahmen bleiben gesonderte Aufgaben.
Der interaktive LinuxCNC-Dateifilter ist unter PyQt5/PyQt6 lokal und in einer
realen Debian-/AXIS-Simulation geprüft; [Nachweis und Grenzen](archive/toolpath-refactoring-completed.md#lc1-axis).

## Bereitstellung und Abnahme

<a id="ci1"></a>

- [ ] **CI1 – Verbleibende Betriebsabnahme:** den ersten bewusst
  freigegebenen stabilen Release nachvollziehen;
  Codesignierung nach Zertifikatsbereitstellung ergänzen. Implementierung
  und Develop-Aktivierung sind [abgeschlossen](archive/toolpath-refactoring-completed.md#ci1).
  [Verbleibende Prüfpunkte](planning/open-task-details.md#ci1).

<a id="m1"></a>

- [ ] **M1 – macOS separat:** bei konkretem Bedarf Zielumgebung und
  Paket-/Startprüfung vereinbaren. Der beauftragte Kandidatenumfang
  Windows/Ubuntu/Debian ist [abgenommen](archive/toolpath-refactoring-completed.md#pr5-installation).
  Endgültige Release-Artefakte werden im nachfolgenden Integrationsschritt geprüft.

<a id="lc1"></a>

- [ ] **LC1 – Optionaler automatischer LinuxCNC-CLI-Filter:** bei Bedarf
  entscheiden, ob zusätzlich zum interaktiven GUI-Filter ein ausdrücklicher
  automatischer stdout-Export ohne Bearbeitungsfenster angeboten werden soll.
  [Verbleibender Umfang](planning/open-task-details.md#lc1).

## Bedienmodell und zurückgestellte Erweiterungen

<a id="r3"></a>
<a id="r1b"></a>

- [ ] **Integration/Develop-Release:** abschließende Nutzersichtprüfung,
  vorbereiteten Kandidaten nach `develop` übernehmen und Develop-Prerelease
  erstellen; endgültige Release-Artefakte gegen Herkunft/Hashes prüfen und starten.
  [Abschluss- und Releaseplan](planning/maschining-project-release-plan.md).

<a id="teilkonturen"></a>

- [ ] **Teilkonturen:** eigene Startpunkte, Leads und Überfahrten je
  resultierender Teilkontur sowie stabile Zuordnung bei Neuberechnung und
  Projekt-Roundtrip entwerfen. [Planungsumfang](planning/open-task-details.md#teilkonturen).

<a id="pp1"></a>

- [ ] **PP1 – Separater Drehzahlblock, später:** einen eigenen konfigurierbaren
  Postprozessorblock für geänderte Drehzahlen bei gleicher Werkzeugnummer
  vorsehen, ohne den Werkzeugwechselblock erneut aufzurufen. Vor Umsetzung
  Auslösebedingungen, Profilkompatibilität und unterstützte Maschinenarten
  abstimmen. Nutzeranregung vom 07.11.2026; noch kein Implementierungsauftrag.
  Der aktuelle Werkzeugwechsel bleibt gemäß
  [D21](planning/r3-r1b-implementation-plan.md) an eine andere Nummer gebunden.

<a id="q1"></a>

- [ ] **Q1 – PySide6:** zusätzliche Qt-Bindung nur bei konkretem Bedarf
  gesondert beauftragen; PyQt5/PyQt6 erhalten.
  [Kompatibilitäts- und Prüfplan](planning/open-task-details.md#q1).

<a id="gui1"></a>

- [ ] **GUI1 – Optionales Ribbon-Menüband:** eine moderne, einklappbare
  Menüband-Oberfläche als mögliche Erweiterung prüfen. Vor Umsetzung
  Bedienentwurf und Bibliothekswahl abstimmen; bestehende Aktionen und
  Tastenkürzel wiederverwenden. [SARibbon](https://github.com/czyt1988/SARibbon)
  als Kandidaten bewerten, insbesondere Python-Bindings für PyQt5/PyQt6,
  Paketierung und Verhalten unter Windows und Linux. Noch kein
  Umsetzungsauftrag.

## Dokumentationsinhalte

<a id="doc1"></a>

- [ ] **DOC1 – Sichtprüfung durch den Nutzer:** Anleitung und aktuelle Bilder
  sind erstellt und streng gebaut. Auf Nutzerwunsch erfolgt die abschließende
  Sichtprüfung erst am Schluss; sie blockiert Schritt 3 nicht.
  [Redaktioneller Abschluss](archive/toolpath-refactoring-completed.md#doc1-machining).
- [ ] **Optionale Maschinenabnahme:** die Grbl-1.1-Laser- und LinuxCNC-2.9-
  Heißdraht-/Drehdemonstrationen bei Bedarf für einen konkreten realen Aufbau
  anpassen und gesondert abnehmen. Geladene Demoprofile und synthetische
  Ausgabeprüfungen sind keine Controller-/Material-/Maschinenfreigabe.
  Weitere macOS-/CNC-/ATC-/manuelle Abnahmen bleiben bei konkretem Bedarf separat;
  die aktuelle Installationsmatrix ist unter M1 zusammengeführt.

Wiederaufnahme und technische Vorschau: [Übergabebericht](migration/zensical-prototype.md).
Die fachlichen Notizen ersetzen keine Inhaltsabnahme oder Veröffentlichungsfreigabe.
