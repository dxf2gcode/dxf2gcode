# GUI1 – Vergleich von VisPy und Qt Quick 3D

Stand: **22.11.2026**. Der Arbeitszweig `ribbon-2d-3d` ist in `develop`
integriert. Die Vergleichsphase dokumentiert die Auswahl von VisPy.
[Abschlussnachweis und Dev-Release](../archive/toolpath-refactoring-completed.md#gui1-dev14).

## Ziel und Grenzen

Den geprüften 2D-Canvas erhalten und zwei mögliche Grundlagen für eine integrierte
Bearbeitungs- und räumliche Ansicht vergleichen:

1. **VisPy mit PyQt6**.
2. **Qt Quick 3D mit PyQt6**.

PySide6 ist kein Nachfolger von PyQt6 und für Qt Quick 3D nicht erforderlich.
In der vorhandenen Umgebung `.tox/package-build` ließ sich am 15.11.2026
`PyQt6.QtQuick3D.QQuick3DGeometry` unter PyQt 6.12.0 importieren. Das ist kein
Nachweis für Rendering, QML-Paketierung oder Plattformabnahme. Q1 bleibt separat.
ModernGL wird vorerst zurückgestellt; kein dritter Prototyp.

Langfristig kann der gewählte Renderer auch die präzise Bearbeitung in einer
festen Draufsicht übernehmen. Ob er den bestehenden Canvas ersetzt, wird erst
nach nachgewiesener Bedienqualität entschieden. Ohne geeignete 3D-Unterstützung
bleibt der bestehende 2D-Weg verfügbar, einschließlich Laden und Export.

Zunächst nur ein kleines Ansichts-Menüband planen. Das vollständige Ribbon,
seine Bibliotheksentscheidung einschließlich SARibbon, Materialabtragssimulation
und weitere Bearbeitungsfunktionen gehören nicht zum Vergleich.

## Gemeinsamer technischer Vertrag

- Ein Projekt und dieselben Planungsergebnisse für beide Renderer; kein neuer
  DXF-Import und keine separate Werkzeugwegplanung beim Ansichtswechsel.
- Darstellungsdaten mit stabilen IDs für Originalgeometrie, Bearbeitung und
  Stegregion; Verknüpfungen und unterschiedliche Auswahlrollen erhalten.
- 2D-Projektion ohne übereinander gezeichnete Tiefenpass-Duplikate; räumliche
  Ansicht mit tatsächlichen Z-Werten, Leads und Steghöhen.
- Vorhandene semantische Farben beibehalten. Hervorhebung über Linienstärke und
  Linienart; keine künstliche Verschiebung von Geometrie oder Werkzeugwegen.
- Renderer zeichnen und melden Interaktionen zurück. Projektänderungen erfolgen
  über gemeinsame Befehle mit Undo/Redo, nicht durch renderer-eigene Modellkopien.
- Projektdaten, Darstellungsaufbereitung und renderer-eigene GPU-Ressourcen
  trennen. Gezielte Aktualisierung statt vollständigem Neuaufbau bei Auswahl.
- Optionale Abhängigkeiten; der normale 2D-/CLI-Weg darf keine erfolgreiche
  3D-Initialisierung voraussetzen. Paketimport und nutzbare Grafik unterscheiden.
- Einen schmalen Adapter aus den tatsächlich benötigten Funktionen ableiten;
  kein allgemeines Grafikframework entwickeln.

## Geplante Schritte und Prüfpunkte

Startweg und bekannte Grenzen: [Bediennotizen](../documentation-notes/view-renderer-comparison.md).
Das größere Vergleichsprojekt `dxf/temple_noir_aplats_negatif.dxf` war für P4
vorgesehen. Es gehört nicht zu den durchgeführten Vergleichsmessungen.

Die P3-Implementierung und der native Windows-Nachweis stehen im
[Abschlussnachweis](../archive/toolpath-refactoring-completed.md#gui1-p3).

### P4 – Vergleich und erste Nutzerprüfung

Der am 16.11.2026 beauftragte VisPy-interne GL-/AGG-Vergleich mit
`AFluegel Rippen b2 0201.dxf` ist lokal durchgeführt und
[mit Zeiten, RAM und Rohdaten dokumentiert](../documentation-notes/vispy-line-benchmark.md).
Der Nutzer hat anschließend GL für beide VisPy-Ansichten gewählt. Die lokale
Umstellung und Cache-Optimierung ist umgesetzt und gezielt geprüft;
[Vorher-/Nachher-Messung](../documentation-notes/vispy-line-benchmark.md#nachtrag-gl-optimierung).

Der frühere [Debian-Vergleich](../documentation-notes/view-renderer-comparison.md#isolierter-debian-teststand)
nutzte einen separaten Teststand. Die Vergleichsphase ist mit der Übernahme von
VisPy beendet. Die Bedienungsabnahme der integrierten Ansicht erfolgt in P6.

### P5 – Gezielter Bearbeitungsnachweis

Die feste VisPy-Draufsicht verwendet dieselbe Stegbearbeitung wie der 2D-Canvas,
einschließlich Zeichnen, Auswahl, Verschieben, Maßfeld, Strg-Fang und Undo/Redo.
Der Stegmodus schaltet aus der Raumansicht in die Draufsicht. Der Wechsel zurück
in die Raumansicht beendet den Modus.
[Umsetzung und lokale Prüfung](../archive/toolpath-refactoring-completed.md#gui1-p5-vispy).

Nutzerprüfung der Stegbedienung und Maßfelder bei verschiedenen Zoomstufen siehe P6.

### P6 – Auswahl und Übernahmeplan

Die gemeinsamen Zeichenregeln wurden am 21.11.2026 bestätigt.
Die Übernahme in den Anwendungsstart, Konfiguration, Ansichtsband und
Paketierung ist lokal umgesetzt. Die Entscheidungen und Prüfungen stehen im
[Abschlussnachweis](../archive/toolpath-refactoring-completed.md#gui1-vispy-adoption).

Der Nutzer hat den Stand für das Dev-Release freigegeben. Die GitHub-CI
prüfte die Qt5- und Qt6-Suite, frische Wheel-Installationen sowie den
Windows-Start und DXF-Export aus ZIP und installiertem MSI. Nach dem Merge
wurden die Release-Pakete aus dem `develop`-Commit erneut gebaut und geprüft.
[Abschlussnachweis](../archive/toolpath-refactoring-completed.md#gui1-dev14).

## Plattformen und Validierungsumfang

Windows und Debian/Linux sind Zielplattformen; macOS beim Architekturvergleich
berücksichtigen. VisPy benötigt OpenGL, Qt Quick 3D kann auch Direct3D/Metal/Vulkan
verwenden. Grafikfunktionen einer VM müssen im Gast tatsächlich verfügbar sein.
Nicht verfügbare Hardware oder Plattformen ausdrücklich als ungeprüft benennen.

Zunächst kurze lokale Prüfungen und gezielte GUI-Sichtprüfungen je Etappe.
Debian-/SSH-Läufe, Vollsuiten, komplette Paket-/MSI-Builds und macOS-Abnahmen nur
nach gesondertem Auftrag oder Annahme eines konkreten Prüfvorschlags. Vor
Code-Commits gilt der schnelle Pre-Commit-Hook; neue GUI-Texte benötigen DE/FR/RU.
Mock-Tests und erfolgreicher Import ersetzen keine echte Grafikprüfung.

## Quellen und spätere Pflege

Recherche vom 15.11.2026; Versionen und Plattformanforderungen vor Installation
erneut anhand der gewählten Paketversion prüfen:

- [VisPy: Installation, Qt-Backends und Grafikvoraussetzungen](https://vispy.org/installation.html)
- [VisPy: Linienverfahren](https://vispy.org/api/vispy.visuals.line.line.html)
- [VisPy: stabiler Stand und experimentelle Nachfolgearchitektur](https://vispy.org/)
- [Qt Quick 3D: Überblick](https://doc.qt.io/qt-6/qtquick3d-index.html)
- [Qt Quick 3D: Grafikvoraussetzungen und Backends](https://doc.qt.io/qt-6/qtquick3d-requirements.html)
- [Qt Quick: Widgets-Einbettung und Performancegrenzen](https://doc.qt.io/qt-6/qquickwidget.html)
- [PyQt6-Veröffentlichungen](https://www.riverbankcomputing.com/news)

Abgeschlossene Etappen aus aktiven Checklisten entfernen; Ergebnisse,
Prüfnachweise und verbleibende Grenzen im
[Abschlussnachweis](../archive/toolpath-refactoring-completed.md) festhalten.
Nutzbare Bedieninformationen später in Dokumentationsnotizen übernehmen.
