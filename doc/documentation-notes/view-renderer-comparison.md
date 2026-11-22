# Redaktionsnotizen: VisPy und Renderer-Vergleich

Zuordnung **GUI1**. Stand **21.11.2026** auf `ribbon-2d-3d`.

## Reguläre Bedienung

- [Oberfläche und Ansichtsband](../../docs/user-guide/interface-and-navigation.md#navigate-the-drawing)
- [VisPy installieren](../../docs/installation.md#enable-the-vispy-view)
- [Renderer-Vergleich und Übernahme](../archive/toolpath-refactoring-completed.md#gui1-vispy-adoption)
- [GL-/AGG-Messungen](vispy-line-benchmark.md)

Beim Start versucht die Anwendung VisPy in der Raumansicht. Zur Bearbeitung
steht seine feste Draufsicht bereit. Der bisherige 2D-Canvas ist per Konfiguration
oder automatischem Rückfall verfügbar. Das Ansichtsband zeigt die Aktionen des
beim Start gewählten Canvas. Die transparenten Zylinder nutzen den geplanten
Werkzeugdurchmesser, vier Durchmesser als schematische Länge und 25 % Deckkraft.

<a id="isolierter-debian-teststand"></a>

## Historischer Debian-Teststand des Renderer-Vergleichs

Am 15.11.2026 nach Nutzerauftrag auf der Debian-Test-VM eingerichtet:
Debian 13.7, Python 3.13.5, PyQt/Qt 6.12.0, VisPy 0.17.0, NumPy 2.5.4.
Eigene Kopie des Arbeitsstands und venv unter
`~/dxf2gcode-test-work/runs/view-comparison-20261115/`.
Starter für die grafische Sitzung:

```sh
~/dxf2gcode-test-work/runs/view-comparison-20261115/start-view-comparison.sh
```

Ein zusätzlicher Desktop-Starter heißt „DXF2GCODE Ansichtsvergleich“ und lädt
`BreakExample_Circle.dxf`. HOME und XDG-Verzeichnisse des Starters zeigen auf
die Testumgebung, nicht auf die Einstellungen der bisherigen Installation.
Das fehlende `libxcb-cursor0` wurde aus der eingerichteten Debian-Paketquelle
nur in das Testverzeichnis entpackt und per lokalem `LD_LIBRARY_PATH` angebunden;
kein Systempaket und keine globale Python-Installation geändert.

Beide nativen Vergleichsworker bestanden in der vorhandenen X11-Sitzung,
einschließlich transparenter Körper und beider Aktivierungsreihenfolgen.
Qt Quick verwendet hier OpenGL. Die virtuelle Virtio-Grafik liefert
**Mesa/llvmpipe, nicht beschleunigt**, OpenGL 4.5. Die VM ist damit ein Test
dieser Software-Rendering-Konfiguration und kein allgemeiner Nachweis der
Debian-/Linux-GPU-Performance. Nutzerprüfung und andere Plattformen bleiben
gesondert zu beurteilen.

## VisPy-Stegbearbeitung prüfen

Im aktuellen Versuch teilen Drauf- und Raumansicht XYZ-Werkzeugwege, GL-Linienpuffer
und Tiefentest. Wiederholte horizontale Abschnitte erhalten dieselbe Strichfolge
auf ihren jeweiligen Tiefen. Vor dem Kamerahandoff entspricht der Maßstab dem
der festen Draufsicht. Bei deckungsgleichen Pfaden gelten die gleichen Regeln
für die Überlagerung in beiden Ansichten. Im Stegmodus übernimmt die Bearbeitungsauflage
die Regionsumrisse, Griffe und Maße.
Nach Nutzerentscheidung vom 16.11.2026 verwenden Modell- und Werkzeugweglinien
in beiden VisPy-Ansichten ausschließlich `method='gl'`. AGG und dessen Muster
sind nicht in die Produktionsansicht übernommen. Striche/Punkte werden als
GL-Segmente gebündelt.

Die feste Draufsicht bildet Z in derselben Richtung ab wie die senkrecht
ausgerichtete Raumkamera. Dadurch entscheidet der gemeinsame Tiefentest bei
deckungsgleichen Linien in beiden Ansichten gleich.

Seit Nutzerkorrektur vom 21.11.2026 gilt in beiden VisPy-Ansichten:

| Auswahl je Originalkontur | Originalkontur | Zugehörige Werkzeugwege |
| --- | --- | --- |
| Keine | Schwarz, 1 | Dünn, 0,6 und gestrichelt |
| Alle zugehörigen Bearbeitungen | Rot, 3 | Alle dünn, 0,6; jeweilige semantische Linienart |
| Weniger als alle | Rot gepunktet, 1 | Gewählte Schnittkontur 3; nicht gewählte dünn, 0,6 und gestrichelt |

Originalkonturen übernehmen keine G41-/G42-Farbe aus einer aktiven Bearbeitung
mehr. Eine einzige gewählte Bearbeitung gilt bei nur einer Verknüpfung bereits
als vollständige Auswahl. Bei Teilauswahl bleiben semantische Werkzeugwegfarben
und Muster erhalten; deren Basisbreite wird für gewählte Bahnen um 1 erhöht
(Schnitt 2 → 3, Taschenbahn 1 → 2). Der im Formular aktive Arbeitsgang erhält
keine zusätzliche Ausnahme gegenüber der Auswahlregel. Bestehende Farben für
deaktivierte Geometrie und Stegregionen bleiben erhalten. Diese Regeln betreffen
VisPy, nicht den bisherigen Canvas oder den Qt-Quick-Vergleichsadapter.

Die Werte sind Stiftparameter, keine Zusage exakt gleicher physischer
Pixelbreiten auf allen Grafiktreibern. GL hat keine AGG-Eckverbindungen.
Die Qt-Auflage für Stegregionen, Maße und Beschriftungen bleibt bestehen.

Für ein vorhandenes Projekt mit Mehrfachbearbeitung kann die native
Auswahlprüfung explizit gestartet werden, beispielsweise:

```powershell
.tox/package-build/Scripts/python.exe tests/dxf2gcode_view_scene_test.py --appearance-project dxf/1997.d2g
```

Die projektbezogene Prüfung ist optional und benötigt die lokal vorhandene
Datei. Der reguläre native Stegworker prüft dieselben Regeln zusätzlich mit
seiner selbst erzeugten Mehrfachbearbeitung aus `BreakExample_Circle.dxf`.

Projektionen und Segmentarrays werden pro Snapshot/Ansicht gespeichert.
Beim Verschieben werden keine Linien neu hochgeladen; Zoom erneuert nur
maßabhängige Strichdaten. Auswahlwechsel aktualisieren die betroffenen
Stilgruppen. Der ausgeblendete bisherige Canvas wird bei unverändertem Projekt
nicht neu aufgebaut und bei Rückkehr aktualisiert. Bei automatischer
Exportreihenfolge bleibt der bestehende vollständige Aktualisierungspfad aktiv.
[Messung vor/nach der GL-Optimierung](vispy-line-benchmark.md#nachtrag-gl-optimierung).
Die Canvas-Trefferprüfung nutzt ebenfalls gecachte Projektionen und gebündelte
Transformationen statt einer Szenengraphabfrage je Segmentendpunkt.
[Gesonderter Klicknachweis](vispy-line-benchmark.md#canvas-klickpfad) einschließlich
Auswahl und Leerraum-Abwahl; die ältere Baum-Auswahlmessung erfasste das nicht.

**Strip-Versuch beendet (16.11.2026):** Der Nutzer sieht keinen optischen Vorteil
und hat die Rückkehr zur gebündelten GL-Segmentdarstellung entschieden.
Modell-/Werkzeugweglinien verwenden wieder durchgehend `connect='segments'`;
Strip-Schalter, Strip-Pool und zugehörige Cache-Zweige sind entfernt. Die schnelle
Trefferprüfung und alle bisherigen GL-Caches bleiben erhalten.
[Historischer Versuch und Messung](vispy-line-benchmark.md#strip-versuch).

Die VisPy-Draufsicht verwendet dieselbe Stegbearbeitung wie der bisherige Canvas.
Im Ansichtsband VisPy wählen und im Bearbeitungstab den Stegmodus einschalten;
aus der räumlichen VisPy-Ansicht wird dabei in die feste XY-Draufsicht gewechselt.
Ein Wechsel zur räumlichen Ansicht beendet den Stegmodus.

Beim Klick auf „VisPy: Draufsicht“ aus der Raumansicht dreht, verschiebt und
zoomt die Kamera in rund 400 ms zum letzten Ausschnitt der festen Draufsicht.
Beim ersten Wechsel wird die Zeichnung eingepasst. Durch erneutes Wählen der
Raumansicht kehrt man zum vorherigen räumlichen Blick zurück. Der automatische
Wechsel beim Einschalten des Stegmodus erfolgt sofort.

Für die Nutzerprüfung `BreakExample_Circle.dxf` laden, eine Bearbeitung auswählen
und eine neue Region aufziehen. Danach eine Region einmal auswählen, durch
erneutes Ziehen verschieben und mit Strg an der Originalkontur ausrichten.
Die Maße an oberer/rechter Kante anklicken, einen Wert bestätigen und
Rückgängig/Wiederherstellen prüfen. Die Maßänderung behält den Mittelpunkt bei
und schaltet automatische Bemessung auf manuell. Während des Ziehens verschwinden
die Maßfelder. Doppelklick öffnet den bestehenden Stegdialog.
Das geöffnete Maßfeld zeigt die konfigurierte Anzeigegenauigkeit (standardmäßig
3 Stellen in mm, 5 in inch). Unverändertes Bestätigen erhält den vollständigen
Geometriewert und den bisherigen Bemessungsmodus; eigene Eingaben werden mit
ihrer eingegebenen Genauigkeit übernommen.
Dies bei stärkerem und schwächerem Zoom mit dem bisherigen Canvas vergleichen.

Der explizite lokale GPU-Test lautet:

```powershell
.tox/package-build/Scripts/python.exe tests/dxf2gcode_view_scene_test.py --vispy-editing-worker
```

Dieser Nachweis gilt für die Stegbearbeitung, nicht für alle bisherigen
Canvas-Aktionen oder die endgültige Rendererwahl. Der bisherige Debian-Teststand
enthält diese später ergänzte Bearbeitung noch nicht.

## Quellen

- [GL-/AGG-Performance- und RAM-Vergleich an AFluegel Rippen](vispy-line-benchmark.md)
- [VisPy: Installation und Qt-Backends](https://vispy.org/installation.html)
- [VisPy: Kameras](https://vispy.org/api/vispy.scene.cameras.html)
- [Qt Quick 3D: eigene Geometrie](https://doc.qt.io/qt-6/qquick3dgeometry.html)
- [Qt: native Quick-Einbettung und Alternative QQuickWidget](https://doc.qt.io/qt-6/qquickwidget.html)
- [Qt Quick 3D: Grafik-Backends](https://doc.qt.io/qt-6/qtquick3d-requirements.html)
- [Offener Vergleichsplan](../planning/gui1-renderer-comparison-plan.md)
- [Lokale Nachweise](../archive/toolpath-refactoring-completed.md#gui1-p1-p2)
- [Qt-Quick-3D-Nachweis](../archive/toolpath-refactoring-completed.md#gui1-p3)
