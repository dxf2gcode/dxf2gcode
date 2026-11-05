# DXF2GCODE: offene Aufgaben

Stand: **05.11.2026**.

Diese Liste enthält ausschließlich offene Arbeiten und Entscheidungen.
Die Reihenfolge ist ein Vorschlag, kein pauschaler Umsetzungsauftrag.
[Abschlüsse und Prüfnachweise](archive/toolpath-refactoring-completed.md),
[Detailanforderungen](planning/open-task-details.md),
[Dokumentationsnotizen](documentation-notes/README.md) und
[Arbeits-/Prüfregeln](working-agreements.md) werden getrennt gepflegt.

## Empfohlene Reihenfolge

**Release-Freigabe:** Version **2.0.0** wird erst nach Abarbeitung der gesamten
Todo freigegeben. Ein manueller Develop-Release samt Downloadprüfung und die
anschließende Paket-/Debian-Abnahme sind aktuell zurückgestellt; dafür liegt
kein neuer Ausführungsauftrag vor.

| Priorität | Offenes Thema | Vor Umsetzung klären |
| --- | --- | --- |
| Vorläufig zurückgestellt | [CI1 – Betriebsabnahme](#ci1), [M1 – Paketabnahme](#m1) | Neuer ausdrücklicher Prüfauftrag; stabile Veröffentlichung erst nach der gesamten Todo |
| Vor Umsetzung abstimmen | [A1 – Abnahmegrenzen](#a1) | Konkrete Abdeckungslücken |
| Optional | [LC1 – Automatischer LinuxCNC-CLI-Filter](#lc1) | Bedarf zusätzlich zum abgenommenen interaktiven GUI-Filter |
| Fachliche Rückmeldungen | [DOC1 – Dokumentationsabnahme](#doc1) | Konkrete Korrekturen zur veröffentlichten Anleitung |
| Zurückgestellt | [R3 – Bedienmodell](#r3), [R1b – Layerwechsel](#r1b), [Teilkonturen](#teilkonturen) | Gemeinsamer Bedien-, Modell- und Persistenzentwurf |
| Optional | [Q1 – PySide6](#q1) | Konkreter Nutzungsbedarf und dauerhafter Prüfaufwand |
| Optional | [GUI1 – Ribbon-Menüband](#gui1) | Bedienentwurf, Bibliothekswahl und Windows-/Linux-Kompatibilität |

Alle geplanten Dokumentationsthemen **WP1–WP13** sind ausgearbeitet und
veröffentlicht. Als nächstes konkrete fachliche Rückmeldungen einpflegen;
weitere Software-/Plattform-/Maschinenabnahmen bleiben gesonderte Aufgaben.
Der interaktive LinuxCNC-Dateifilter ist unter PyQt5/PyQt6 lokal und in einer
realen Debian-/AXIS-Simulation geprüft; [Nachweis und Grenzen](archive/toolpath-refactoring-completed.md#lc1-axis).

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

<a id="lc1"></a>

- [ ] **LC1 – Optionaler automatischer LinuxCNC-CLI-Filter:** bei Bedarf
  entscheiden, ob zusätzlich zum interaktiven GUI-Filter ein ausdrücklicher
  automatischer stdout-Export ohne Bearbeitungsfenster angeboten werden soll.
  [Verbleibender Umfang](planning/open-task-details.md#lc1).

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

- [ ] **DOC1 – Fachliche Rückmeldungen:** konkrete Kapitelkorrekturen zur
  veröffentlichten vollständigen Anleitung einarbeiten.
  [Abschluss und Veröffentlichung WP9–WP13](archive/toolpath-refactoring-completed.md#doc1-wp9-wp13),
  [Erstansicht WP1–WP8](archive/toolpath-refactoring-completed.md#doc1-wp3-wp8-publication).
- [ ] **Optionale Maschinenabnahme:** die Grbl-1.1-Laser- und LinuxCNC-2.9-
  Heißdraht-/Drehdemonstrationen bei Bedarf für einen konkreten realen Aufbau
  anpassen und gesondert abnehmen. Geladene Demoprofile und synthetische
  Ausgabeprüfungen sind keine Controller-/Material-/Maschinenfreigabe.
- [ ] **Optionale historische Wiederverwendung:** Rechte für Wiki-Texte,
  Screenshots, fremde DXFs und Git-Flow-Grafik klären, falls sie übernommen
  werden sollen; fehlendes `Spant.png` (404) nur mit geklärter Herkunft
  wiederherstellen/ersetzen. Die neue Anleitung benötigt diese Originale nicht.
- [ ] Frische Windows-/Ubuntu-/PyQt6-Installationen und macOS-Pakete sowie
  CNC-/ATC-/manuelle Maschinenabnahmen separat planen und freigeben.

Wiederaufnahme und technische Vorschau: [Übergabebericht](migration/zensical-prototype.md).
Die fachlichen Notizen ersetzen keine Inhaltsabnahme oder Veröffentlichungsfreigabe.
