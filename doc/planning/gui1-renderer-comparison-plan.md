# GUI1 – Vergleich von VisPy und Qt Quick 3D

Stand: **15.11.2026**. Geplante Abarbeitung auf `ribbon-2d-3d`.
Statusführung: [Todo](../todo.md#gui1), [Aufgabendetails](open-task-details.md#gui1).
Dieser Plan ist noch keine Rendererentscheidung oder Freigabe für alle Etappen.
P1/P2 sind lokal umgesetzt und vom Nutzer am 15.11.2026 als soweit
erwartungsgemäß funktionierend bestätigt. P3 ist lokal umgesetzt. Nach dem
Vergleich wird VisPy vorläufig bevorzugt; der Nutzer hat den gezielten
Bearbeitungsnachweis P5 für VisPy beauftragt. Qt Quick 3D bleibt als Vergleich
erhalten. Nächster Prüfpunkt ist die Bedienungsabnahme von P5; offene P4-Vergleiche
und die endgültige Rendererentscheidung bleiben separat.
Nachweise und Grenzen stehen im [Abschlussnachweis](../archive/toolpath-refactoring-completed.md#gui1-p1-p2).

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
Das größere Vergleichsprojekt für P4 ist `dxf/temple_noir_aplats_negatif.dxf`;
dessen Messlauf ist noch offen und nicht Teil der bisherigen lokalen Nachweise.

Die P3-Implementierung und der native Windows-Nachweis stehen im
[Abschlussnachweis](../archive/toolpath-refactoring-completed.md#gui1-p3).
Die endgültige Ribbon-Gestaltung bleibt offen.

### P4 – Vergleich und erste Nutzerprüfung

Der am 16.11.2026 beauftragte VisPy-interne GL-/AGG-Vergleich mit
`AFluegel Rippen b2 0201.dxf` ist lokal durchgeführt und
[mit Zeiten, RAM und Rohdaten dokumentiert](../documentation-notes/vispy-line-benchmark.md).
Der Nutzer hat anschließend GL für beide VisPy-Ansichten gewählt. Die lokale
Umstellung und Cache-Optimierung ist umgesetzt und gezielt geprüft;
[Vorher-/Nachher-Messung](../documentation-notes/vispy-line-benchmark.md#nachtrag-gl-optimierung).

- [ ] Nutzer prüft die optimierte GL-Darstellung: Rippen-DXF verschieben/zoomen,
  Einzel-/Mehrfachauswahl wechseln, Linienqualität und Rückkehr zum alten Canvas
  beurteilen. Strichbreiten bleiben treiberabhängig; keine AGG-Übernahme vorgesehen.

Nach der Rückmeldung zur ruckligen Qt-Quick-Navigation wurde deren Python-
Aktualisierungspfad optimiert und lokal gemessen
([Nachweis](../archive/toolpath-refactoring-completed.md#gui1-quick-navigation)).
Den folgenden Nutzervergleich mit diesem Stand durchführen; eine Bewertung
großer Projekte oder eine Bibliotheksentscheidung folgt daraus noch nicht.

Nutzer-Rückmeldung nach dem transparenten Werkzeugtest: beide Kandidaten laufen
aktuell relativ flüssig. Der anschließend beauftragte Debian-Teststand ist
vorbereitet und gezielt technisch geprüft; die manuelle Nutzerprüfung auf dieser
VM steht noch aus. Starter und Software-Rendering-Grenze stehen in den
[Bediennotizen](../documentation-notes/view-renderer-comparison.md#isolierter-debian-teststand).

- [ ] Ergebnisse mit identischen Projekten, Fenstergrößen und Einstellungen
  erfassen: Ladezeit, Kamera-Reaktion, Auswahl und Aktualisierung nach Änderung.
- [ ] Hardware, Betriebssystem, Python-/Qt-/Renderer-Version, Grafik-Backend,
  Datenumfang und Wiederholungsbedingungen bei Messungen festhalten.
- [ ] Linienqualität, Lesbarkeit, Auswahlpräzision und Integrationsaufwand
  gegenüber dem bestehenden 2D-Canvas bewerten; keine pauschale FPS-Rangliste.
- [ ] Nutzerprüfung: dieselbe Originalkontur mit mehreren Bearbeitungen wählen,
  Mehrfachauswahl ändern, zoomen/drehen und Tiefen/Stege visuell vergleichen.
  Dazu in derselben Sitzung zwischen VisPy und Qt Quick 3D wechseln, die
  Draufsicht und die räumliche Ansicht jeweils prüfen und eine Frästiefe ändern.
  `BreakExample_Circle.dxf` für Stege und mehrere Bearbeitungen derselben Kontur
  sowie `1997.DXF` mit G40/G41/G42 und mehreren Tiefenpässen verwenden.
  Den Schalter „Transparente Werkzeuge (Test)“ mit identischer Mehrfachauswahl
  jeweils aus-/einschalten; Navigation, Durchsichtigkeit und Überlagerungen
  beurteilen. Die Körper sind ein Last-/Darstellungstest mit angenommener Länge,
  keine fachliche Werkzeug- oder Kollisionssimulation.
- [ ] Gemeinsam entscheiden: Kandidat bevorzugen, einen Kandidaten verwerfen
  oder beide für die noch offene Bearbeitungsfrage weiterführen.

Keine Schwellenwerte erfinden: gewünschte Reaktionszeiten und akzeptable
Darstellungsabweichungen anhand dieses Vergleichs gemeinsam festlegen.

### P5 – Gezielter Bearbeitungsnachweis

Für VisPy lokal umgesetzt: gemeinsame Stegbearbeitung in fester XY-Draufsicht,
einschließlich Zeichnen, Auswahl, Verschieben, Maßfeld, Strg-Fang und Undo/Redo.
Stegmodus wechselt aus der räumlichen VisPy-Ansicht zur Draufsicht; beim Wechsel
zur räumlichen Ansicht endet der Modus. Projektbefehle, Zuordnung und
automatische/manuelle Bemessung bleiben gemeinsam mit dem bisherigen Canvas.
[Umsetzung und lokale Prüfung](../archive/toolpath-refactoring-completed.md#gui1-p5-vispy).

- [ ] Nutzer prüft die Bedienung im Vergleich zum bewährten Canvas.
- [ ] Nutzer beurteilt Maßfelder und Treffererkennung bei unterschiedlichen
  Zoomstufen; weitere Plattformabnahme nur nach gesondertem Auftrag.

### P6 – Auswahl und Übernahmeplan

- [ ] Versuch mit gemeinsamen XYZ-Werkzeugwegen in VisPy beurteilen. In der
  festen Draufsicht eine Kontur mit mehreren Tiefendurchgängen einpassen, zoomen,
  auswählen und abwählen. Linienbild, Auswahl an Zustellpunkten und Reaktion
  beurteilen. In der Raumansicht dieselben Tiefen kontrollieren. [Lokaler Nachweis](../archive/toolpath-refactoring-completed.md#gui1-shared-xyz).
- [ ] Danach die für den Standardstart erforderlichen Canvas-Funktionen
  festlegen und übernehmen. Prüfkandidaten sind Kontextmenü, Werkstücknullpunkt,
  Rechteckauswahl, Maßstab, Pfadrichtungen und sichtbare Exportreihenfolge.
- [ ] Die vorhandene 3D-Einstellung mit Neustart auf VisPy umstellen und die
  Raumansicht zum Standard machen. Den bisherigen 2D-Canvas als wählbare Option
  und automatischen Rückfall bei fehlendem PyQt6, VisPy oder nutzbarem OpenGL
  erhalten. Grund melden und gespeicherte Präferenz beim Rückfall beibehalten.
  Übernahme alter Profile und GUI-Paketierung festlegen.
- [ ] Das Ansichtsband auf Aktionen der aktiven Ansicht zuschneiden. VisPy
  bietet Draufsicht und Raumansicht innerhalb desselben Fensters. Die Wahl
  zwischen VisPy und bisherigem 2D-Canvas erfolgt in der Konfiguration.
- [ ] Entfernen von Qt-Quick-Vergleichsadapter, QML, Vergleichsschaltern und
  Testwerkzeugen nach ihrer Abnahme entscheiden. Alten `canvas3d.py`-Pfad,
  seine Startzweige, den zugehörigen Stegdialog, Tests und Paketbedarf prüfen.
  Einstellungen, Übersetzungen, Dokumentation und Pakete gemeinsam nachziehen.

Der bisherige 2D-Canvas bleibt als Rückfall erhalten. Der Merge nach `develop`
folgt nach der vereinbarten Prüfung.

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
