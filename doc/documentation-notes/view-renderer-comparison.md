# Redaktionsnotizen: Renderer-Vergleich

Zuordnung: **GUI1 P1–P3**. Stand: **15.11.2026**. Experimenteller Stand auf
`ribbon-2d-3d`, keine Freigabe für `develop` oder einen Release.

## Start und Bedienung

Im Checkout mit der vorhandenen PyQt6-Umgebung:

```powershell
$env:DXF2GCODE_QT = '6'
.\.tox\package-build\Scripts\python.exe .\source\dxf2gcode.py
```

Die VisPy-Abhängigkeiten wurden für die lokale Erprobung in dieser Umgebung
installiert. Für andere Umgebungen bietet `source/pyproject.toml` das optionale
Extra `view-vispy`; dies ist noch keine Abnahme eines installierten Pakets.
Qt Quick 3D nutzt das bereits vorhandene PyQt6; das Extra `view-quick3d` benennt
die optionale Voraussetzung. Ein Wechsel zu PySide6 ist nicht erforderlich.
Die QML-Datei wird relativ zum installierten Python-Modul geladen und ist in
Paketdaten und Source-Manifest eingetragen; Paket-/MSI-Abnahme steht noch aus.
Die bisherige Konfiguration muss den vorhandenen 2D-Canvas als Startmodus
verwenden. Der alte globale 3D-Startmodus wird durch den Prototyp nicht ersetzt.

Eine zusätzliche Leiste enthält:

- **2D-Canvas:** bisherige Bearbeitung mit unverändertem Canvas.
- **VisPy: Draufsicht:** feste Ebene; Ziehen mit linker Maustaste verschiebt,
  das Mausrad zoomt.
- **VisPy: räumliche Ansicht:** Ziehen mit linker Maustaste dreht;
  Umschalt+Ziehen mit linker Maustaste verschiebt, Mausrad zoomt.
- **Qt Quick 3D: Draufsicht / räumliche Ansicht:** gleicher Funktionsumfang;
  feste Draufsicht mit Verschieben oder räumliches Drehen mit linker Maustaste,
  Umschalt+Ziehen verschiebt, das Mausrad zoomt um die Cursorposition.
- **Alles einpassen:** wirkt auf die aktuell sichtbare Ansicht.
- Die vorhandene Aktion zum Anzeigen deaktivierter Pfade ist ebenfalls nutzbar.
- **Transparente Werkzeuge (Test):** ein-/ausschalten und eine oder mehrere
  Bearbeitungen auswählen. Pro ausgewählter aktivierter Bearbeitung mit gültigem
  Plan erscheint ein Zylinder am Startpunkt. Mehrfachauswahl erzeugt mehrere
  Körper für den visuellen Lastvergleich. Dieselbe Einstellung gilt für beide
  Prototypen; der bisherige Canvas wird dadurch nicht verändert.

Die Testkörper verwenden den geplanten Werkzeugradius und **25 % Deckkraft**.
Die Länge beträgt ausdrücklich **vier Durchmesser** und kommt nicht aus einer
Werkzeuglängenmessung. Beide Kandidaten verwenden dasselbe geschlossene
Zylindernetz mit 48 Seiten (194 Vertices, 192 Dreiecke); Licht und Transparenz-
Sortierung sind rendererabhängig. Körper stehen entlang Z am Startpunkt, sie
fahren noch nicht den Werkzeugweg ab. Keine Kollisions-/Materialabtragsprüfung.
Die Darstellung ändert weder Projektwerte noch G-Code. „Alles einpassen“
berücksichtigt sichtbare Testkörper.

Klick wählt eine Bearbeitung, Strg+Klick ergänzt oder entfernt sie. Bei mehreren
Treffern erscheint eine Auswahl der Bearbeitungen/Regionen. Wird nur eine
Originalkontur getroffen, gilt die bisherige Geometrieauswahl mit ihren
Verknüpfungen. Parameter werden weiterhin im bestehenden linken Bereich geändert.
Stegregionen sind sichtbar und auswählbar; Zeichnen, Ziehen und Maßänderung im
neuen Renderer gehören erst zum späteren Bearbeitungsnachweis P5. Dafür bislang
zum bisherigen 2D-Canvas wechseln.

Ohne PyQt6 sind beide Prototypen deaktiviert. Fehlendes VisPy deaktiviert nur
VisPy; fehlende Qt-Quick-3D-Module nur Qt Quick 3D. Tooltips nennen den Grund.
Bei erkannter Initialisierungs-/Renderingstörung wird zum bestehenden
Canvas zurückgekehrt und der Grund im Log ausgegeben. Es werden keine Pakete
automatisch beim Start installiert. Betriebssystem-/Treiberabstürze können durch
Python-Fehlerbehandlung nicht generell abgefangen werden.

## Gemeinsame Grundlage und Grenzen

`application/view_scene.py` enthält Qt-/VisPy-freie Datensätze, die bestehende
Planprojektion für die Draufsicht und Trefferprüfung über stabile IDs.
`view_scene_adapter.py` erzeugt die Daten aus den vorhandenen Planungsadaptern.
Ein unveränderter Projekt-/Konfigurationsstand nutzt denselben Snapshot bei
Auswahländerungen; Projektänderungen erzeugen ihn neu. Der Prototyp besitzt
keine eigene Exportplanung oder Projektdatei.

VisPy bündelt Linien nach Darstellungsstil. Gestrichelte/gepunktete Linien werden
in Segmente zerlegt; Texte und Start-/Endmarkierungen liegen in einer Qt-Auflage.
Die Linienglättung und -breiten hängen auch vom OpenGL-Treiber ab. Der Nutzer
hat den VisPy-Prototyp am 15.11.2026 als soweit erwartungsgemäß funktionierend
bestätigt. Die gemeinsame Nutzerprüfung, große Datenmengen und die abschließende
Rendererentscheidung bleiben Gegenstand von P4.

Qt Quick 3D verwendet ein natives `QQuickView` innerhalb eines Qt-Containers,
damit dessen RHI-Backend unabhängig vom VisPy-OpenGL-Widget bleiben kann. Im
lokalen Windows-Lauf wurde **Direct3D 11** verwendet; Vulkan/Metal und andere
Zielplattformen sind damit nicht geprüft. Bei einer Einbettung als `QQuickWidget`
wäre die gemeinsame Grafik-API des übergeordneten Fensters zu berücksichtigen.

`view_interaction.py` enthält gemeinsame Farben, Linienarten und Treffer-/Auswahl-
regeln. Qt Quick 3D zeichnet Bildschirmbreiten als kamerazugewandte Dreiecke mit
Vertexfarben; gestrichelte Linien nutzen dieselbe Segmentzerlegung wie VisPy.
Das vermeidet die Beschränkung nativer Linienbreiten, benötigt aber mehr
Geometrie. Beim Verschieben bleibt der GPU-Puffer unverändert; Drehen und
Zoomen aktualisieren die Bänder weiterhin. Endpunkte, Grenzen und Projektionen
werden wiederverwendet, statt bei jeder Bewegung vollständig neu berechnet.
Linienecken,
Antialiasing und Reaktionszeit bei großen Datenmengen gehören in den Vergleich.
Beschriftungen und Start-/Endmarkierungen zeichnet eine QML-Canvas-Auflage.
Kamera- und Beschriftungssignale sind getrennt; die Auflage wird nur bei
geänderten Beschriftungsdaten neu gezeichnet. Der 16-ms-Timer bündelt Ereignisse,
ohne seinen Termin bei jeder weiteren Bewegung nach hinten zu schieben.
Das ist keine Zusage von 60 FPS. Die begrenzte lokale Vorher-/Nachher-Messung
steht im [Nachweis zur Navigation](../archive/toolpath-refactoring-completed.md#gui1-quick-navigation).
Eine anschließende CPU-Gegenprobe mit VisPy ist im selben Abschlussnachweis
festgehalten: auf dem kleinen Beispiel VisPy günstiger bei Drehen/Zoomen,
optimiertes Qt Quick günstiger beim Verschieben. Beide Mess-Worker erfassen
auch die Kamerazuweisung; daraus folgt keine allgemeine FPS-Rangliste.

Die Grafikprüfung erfolgt erst nach dem ersten nativen Frame. Ein früher
synchroner Framebuffer-Abruf ließ Qt Quick 3D unter der geprüften Qt-6.12-/D3D11-
Kombination leer bleiben. QML-/Grafikfehler und ein ausbleibender erster Frame
führen zum bisherigen Canvas zurück; der andere Kandidat bleibt freigeschaltet.

Für die Transparenz-Gegenprobe stehen zusätzlich die nativen Worker
`--vispy-tools-benchmark` und `--quick-tools-benchmark` in
`tests/dxf2gcode_view_scene_test.py` bereit. Sie vergleichen eingeschaltete und
ausgeschaltete Körper beim Drehen einschließlich Bild-Readback. Die APIs und
gerenderten Auflagen unterscheiden sich; die Werte sind keine Bildschirm-FPS
und keine belastbare Rangliste aus wenigen Proben. Für den Nutzervergleich
dieselbe Zeichnung, Auswahl und Fenstergröße verwenden und den Schalter beim
Navigieren umlegen.

Die bisherige Einstellung zur Anzeige von Pfadrichtungen und das alte Canvas-
Kontextmenü steuern den Prototyp nicht vollständig. Dort werden zunächst
Werkzeugwege dargestellt, markierte Bearbeitungen erhalten Start-/Endmarkierungen.
Das ist eine begrenzte Vergleichsansicht, noch kein Ersatz aller Canvas-Aktionen.

## Isolierter Debian-Teststand

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

Im aktuellen Versuch teilen Drauf- und Raumansicht die XYZ-Werkzeugwege.
Die feste Draufsicht schaut senkrecht auf dieselben Tiefendurchgänge. VisPy
verwendet für durchgezogene Linien die gemeinsamen XYZ-Segmente. Nur für
Strichmuster wird die sichtbare XY-Länge verwendet und jede deckungsgleiche
Strecke pro Bearbeitung und Bewegungsart einmal gemustert. In der Raumansicht
erhalten wiederholte horizontale Abschnitte dieselbe Strichfolge auf ihren
jeweiligen Tiefen. Die Draufsicht behält ihre
Zeichenreihenfolge, blendet deckungsgleiche nicht ausgewählte Schnittsegmente
unter der Originalkontur wie bisher aus und bietet die Stegbearbeitung an.

In der VisPy-Draufsicht werden Linien ohne Tiefentest in fester Reihenfolge
gezeichnet: nicht ausgewählte Bearbeitungen, Originalgeometrie und zuletzt
ausgewählte Bearbeitungen. Deckungsgleiche G40-Pfade erhalten damit eine eindeutige
Überlagerung. Die räumliche Ansicht verwendet weiterhin den Tiefentest;
Farben, Linienarten und Werkzeugwegdaten bleiben erhalten.
Nach Nutzerentscheidung vom 16.11.2026 verwenden Modell- und Werkzeugweglinien
in beiden VisPy-Ansichten ausschließlich `method='gl'`. AGG und dessen Muster
sind nicht in die Produktionsansicht übernommen. Striche/Punkte werden als
GL-Segmente gebündelt. Originale und exakt deckungsgleiche, nicht ausgewählte
Schnittsegmente werden in der Draufsicht nicht doppelt gezeichnet; andere
Bearbeitungsrollen und räumliche Linien bleiben erhalten.

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
