# DXF2GCODE: offene Aufgaben

Stand: **02.11.2026**.

Diese Liste enthält ausschließlich offene Arbeiten und Entscheidungen.
Die Reihenfolge ist ein Vorschlag, kein pauschaler Umsetzungsauftrag.
[Abschlüsse und Prüfnachweise](archive/toolpath-refactoring-completed.md),
[Detailanforderungen](planning/open-task-details.md),
[Dokumentationsnotizen](documentation-notes/README.md) und
[Arbeits-/Prüfregeln](working-agreements.md) werden getrennt gepflegt.

## Empfohlene Reihenfolge

| Priorität | Offenes Thema | Vor Umsetzung klären |
| --- | --- | --- |
| 1 | [CI1 – Betriebsabnahme](#ci1), [M1 – Paketabnahme](#m1), [A1 – Abnahmegrenzen](#a1) | Prüffreigabe und konkrete Abdeckungslücken |
| Eigener Arbeitsstrang | [DOC1 – Dokumentationsinhalte](#doc1) | WP1 zuerst; Quellenrechte und fehlende Medien |
| Zurückgestellt | [R3 – Bedienmodell](#r3), [R1b – Layerwechsel](#r1b), [Teilkonturen](#teilkonturen) | Gemeinsamer Bedien-, Modell- und Persistenzentwurf |
| Optional | [Q1 – PySide6](#q1) | Konkreter Nutzungsbedarf und dauerhafter Prüfaufwand |

Nächster Vorschlag: **M1** anhand der jetzt verfügbaren CI-Pakete konkret
abstimmen (Zielrechner und Debian-Prüfumfang); dies startet noch keinen
zusätzlichen lokalen Build oder Debian-/SSH-Lauf.

## Bereitstellung und Abnahme

<a id="ci1"></a>

- [ ] **CI1 – Verbleibende Betriebsabnahme:** echten PR-Paketablauf und den
  ersten bewusst freigegebenen stabilen Release nachvollziehen;
  Codesignierung nach Zertifikatsbereitstellung ergänzen. Implementierung
  und Develop-Aktivierung sind [abgeschlossen](archive/toolpath-refactoring-completed.md#ci1).
  [Verbleibende Prüfpunkte](planning/open-task-details.md#ci1).

<a id="m1"></a>

- [ ] **M1 – Paket-/Debian-Abnahme:** nach gesonderter Freigabe reale
  Wheel-/Quell-/Windows-Artefakte einschließlich Herkunft und Start prüfen;
  das freigegebene Wheel im isolierten Debian-Ablauf abnehmen.
  [Prüfumfang und Freigabegrenze](planning/open-task-details.md#m1).

<a id="a1"></a>

- [ ] **A1 – Architekturabnahme:** konkrete verbleibende Fallmatrix-Lücken
  und den gewünschten Umfang weiterer Importentkopplung benennen.
  [Offene Entscheidungen](planning/open-task-details.md#a1).

## Zurückgestellte Erweiterungen

<a id="r3"></a>

- [ ] **R3 – Geometrie und Bearbeitung trennen:** Bedienmodell mit
  Bearbeitungsgruppen, referenzierten Konturen, Reihenfolge und Persistenz
  gemeinsam entwerfen. [Planungsumfang](planning/open-task-details.md#r3).

<a id="r1b"></a>

- [ ] **R1b – Layerwechsel:** erst zusammen mit R3 planen. Semantik von
  Verschieben/Kopieren, expliziten Konturwerten und geerbten Werkzeugwerten
  festlegen. [Planungsumfang](planning/open-task-details.md#r1b).

<a id="teilkonturen"></a>

- [ ] **Teilkonturen:** eigene Startpunkte, Leads und Überfahrten je
  resultierender Teilkontur sowie stabile Zuordnung bei Neuberechnung und
  Projekt-Roundtrip entwerfen. [Planungsumfang](planning/open-task-details.md#teilkonturen).

<a id="q1"></a>

- [ ] **Q1 – PySide6:** zusätzliche Qt-Bindung nur bei konkretem Bedarf
  gesondert beauftragen; PyQt5/PyQt6 erhalten.
  [Kompatibilitäts- und Prüfplan](planning/open-task-details.md#q1).

## Dokumentationsinhalte

<a id="doc1"></a>

- [ ] **DOC1 / WP1:** vom aktuellen `develop` einen Inhaltsbranch
  `docs/wiki-migration` anlegen; „First DXF to G-code“ mit eigenem kleinen
  Beispiel und ausdrücklich benannten Profilannahmen schreiben.
- [ ] Danach User Guide (WP2–WP7), Configuration/Postprozessoren (WP8–WP10),
  Developer Guide (WP11–WP12) und historische Inhalte (WP13) bearbeiten.
  [Migrationsmatrix und Reihenfolge](migration/wiki-migration-plan.md).
- [ ] Bei den jeweiligen Inhaltspaketen die
  [gesammelten Fach- und Quellenhinweise](documentation-notes/README.md)
  abgleichen und externe Wiki-/Forum-Verweise prüfen.
- [ ] Rechte für Wiki-Texte, Screenshots, fremde DXFs und Git-Flow-Grafik
  klären; ungeklärte Inhalte nicht übernehmen.
- [ ] Fehlendes `Spant.png` (404) klären oder autorisiert ersetzen.
- [ ] Optional das veröffentlichte Symbol und den Header zusätzlich visuell
  kontrollieren.
- [ ] Frische Windows-/Ubuntu-/PyQt6-Installationen und macOS-Pakete sowie
  CNC-/ATC-/manuelle Maschinenabnahmen separat planen und freigeben.

Wiederaufnahme und technische Vorschau: [Übergabebericht](migration/zensical-prototype.md).
Die fachlichen Notizen ersetzen keine Inhaltsabnahme oder Veröffentlichungsfreigabe.
