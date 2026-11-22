# VisPy: GL-/AGG-Linienvergleich an einer mittleren DXF

Stand: **16.11.2026**. Expliziter Nutzerauftrag zur Performance und zum
Arbeitsspeicher bei einer einheitlichen Linienmethode. Das Experiment ändert
keine Produktionsansicht und entscheidet noch keine Rendererübernahme.

## Umfang und Umgebung

- `dxf/AFluegel Rippen b2 0201.dxf`, 405.726 Bytes, 63 Originalkonturen,
  63 Bearbeitungen und 21.647 projizierte Segmente einschließlich Originalen.
  Der SHA-256-Wert steht in den Rohdaten.
- Windows-Kernel 10.0.26200, AMD Ryzen 5 5600, AMD Radeon RX 6700 XT,
  OpenGL 4.6 Compatibility, Treiberversion laut GL 26.2.2.260218.
- Python-, PyQt-/Qt-Version und VisPy-Version stehen in den Rohdaten;
  PyQt/Qt 6.12.0 und VisPy 0.17.0.
- Draufsicht, logischer Canvas 805 × 705, Framebuffer 1006 × 881 Pixel,
  Skalierung 125 %. Keine transparenten Werkzeugkörper, kein Qt-Quick-Vergleich.
- Frischer Prozess und temporäre Konfiguration je Variante; identische DXF,
  Ansicht, Stifte und Auswahlfolgen. Projektinhalt am Ende unverändert geprüft.

Das Werkzeug [benchmark_vispy_lines.py](../../tools/benchmark_vispy_lines.py)
verwendet dieselbe Anwendung, Planung und Auswahlverarbeitung. Nur der
experimentelle VisPy-Adapter erzwingt eine Linienmethode. Beide Varianten
setzen Alpha-Blending explizit. Die zuletzt eingeführte AGG-Breitenreduktion
wird im Experiment nicht angewendet: verglichen werden dieselben Stiftwerte,
noch keine optisch exakt abgeglichenen Strichstärken.

Die Zeichnung wird vor dem ersten Linienupload eingepasst. Der aktuelle
Produktionspfad lädt zunächst Linien bei noch nicht eingepasster Kamera;
dessen riesige vorübergehende Strichanzahl soll den Methodenvergleich nicht
verfälschen. Ein erster Vorversuch ohne diese Korrektur ist kein Vergleichswert.

## Varianten

**GL:** Linien nach Farbe, Breite und Zeichenebene bündeln, Striche explizit
aufteilen und als GL-Segmente zeichnen.

**Einfaches AGG:** Jeder zusammenhängende Pfad bzw. getrennte Strich wäre ein
eigenes `LineVisual`. Bei eingepasster Zeichnung wurden bereits **4.962 Visuals**
benötigt. Der Lauf wurde vor deren Erzeugung an der Schutzgrenze von 1.500
Visuals gestoppt. Das ist keine gemessene Laufzeit oder Speicherspitze für diese
Variante; die Konstruktion ist für eine Übernahme nicht sinnvoll.

**Gebündeltes AGG:** Unabhängige Pfade und Striche in gemeinsame Vertex-/Index-
Puffer je Stil und Ebene übernehmen. Ecken, Endkappen und Strichlücken bleiben
getrennt. Im Versuch sind 3 Visuals ohne Auswahl, 6 bei Einzelauswahl und 8 bei
Mehrfachauswahl nötig, wie bei GL. Dafür wird VisPy 0.17s privater
`_AggLineVisual._agg_bake` im Experiment verwendet. Diese Abhängigkeit ist
vor einer Produktivübernahme abzusichern bzw. durch einen eigenen Adapter
mit klaren Kompatibilitätsgrenzen zu kapseln.

Veraltete Visuals werden in beiden Testadaptern entfernt. Die Werte messen
somit nicht unverändert die Speicherhaltung des bisherigen Mischadapters.

## Ergebnisse

Median in Millisekunden, zwei Aufwärmaktualisierungen, danach zwölf Proben pro
Navigationsphase bzw. acht Auswahlwechsel. Jede Probe enthält CPU-Aktualisierung,
Rendering und synchronen Framebuffer-Readback. **Keine Bildschirm-FPS-Messung**;
die Qt-Beschriftungsauflage ist im GPU-Readback nicht enthalten.

| Vorgang | GL | Gebündeltes AGG |
| --- | ---: | ---: |
| Unverändertes Bild rendern/readback | 7,15 | 10,12 |
| Verschieben, ohne Auswahl, mit Linien-Neuaufbau | 144,10 | 498,46 |
| Zoomen, ohne Auswahl, mit Linien-Neuaufbau | 127,88 | 499,94 |
| Einzelauswahl wechseln | 409,21 | 820,17 |
| Mehrfachauswahl wechseln, bis 24 Bearbeitungen | 426,88 | 630,09 |
| Verschieben mit Mehrfachauswahl und Neuaufbau | 123,84 | 317,04 |
| Zoomen mit Mehrfachauswahl und Neuaufbau | 130,80 | 302,71 |
| Verschieben, alle 63 Bearbeitungen ausgewählt | 102,72 | 145,40 |

Der überwiegende Aufwand liegt im Python-/Geometrie-Aktualisierungspfad.
Beispiel Mehrfachauswahl/Verschieben: CPU-Aktualisierung ca. 114 ms bei GL und
306 ms bei AGG; einschließlich GPU/Readback ca. 124 bzw. 317 ms.
Selbst GL ist mit diesem vollständigen Neuaufbau pro Bewegung nicht flüssig.

Die einmaligen DXF-Ladezeiten betrugen 0,79 s (GL) und 0,69 s (AGG); danach
bis zur ersten VisPy-Ansicht 1,32 s bzw. 2,30 s. Diese Einzelwerte sind keine
statistisch abgesicherte Startzeit-Rangliste.

### Getrennte Gegenprobe: Kamera verschieben, Geometrie behalten

Je 30 Proben nach zwei Aufwärmaktualisierungen, wieder frische Prozesse.
Nur die Kamera wird verschoben; keine Linienuploads, per Beobachtung aller
`set_data`-Aufrufe geprüft. Ein Pan verändert keine Strichlängen; diese Probe
verzichtet daher nicht zugunsten der Geschwindigkeit auf deren Pixelmaß.

| Vorgang | GL Median / P95 | AGG Median / P95 |
| --- | ---: | ---: |
| Kamera verschieben, ohne Auswahl | 7,52 / 9,93 ms | 9,66 / 11,89 ms |
| Kamera verschieben, 24 ausgewählt | 8,23 / 8,47 ms | 11,22 / 12,25 ms |

Das belegt eine schnelle **reine Darstellungsbasis** für beide Methoden auf
diesem Rechner. Der Cache-Pfad ist ein isolierter Nachweis, noch keine
umgesetzte Navigation. Insbesondere Zoomen bei konstanten Strichlängen und
Auswahländerungen sind damit nicht optimiert oder abgenommen.

## Arbeitsspeicher

Windows-Prozesszähler umfassen Python, Qt, Geometrie und native/treiberseitige
Prozessallokationen. Working Set bezeichnet residenten Prozessspeicher;
Private Commit ist zugesicherter privater Speicher und nicht gleichbedeutend
mit aktuell belegtem RAM. Dedizierter GPU-Speicher/VRAM ist nicht gemessen.

| Gesamter Prozess, vollständiger Versuch | GL | Gebündeltes AGG |
| --- | ---: | ---: |
| Working Set nach DXF-Laden, vor VisPy | 170 MiB | 170 MiB |
| Working Set nach erster VisPy-Ansicht | 329 MiB | 365 MiB |
| Höchster Working Set bis Versuchsschluss | 448 MiB | 497 MiB |
| Höchster Private Commit | 830 MiB | 884 MiB |

AGG benötigte in diesem Ablauf rund **49 MiB mehr maximales Working Set**.
In der getrennten Kamera-Gegenprobe mit weniger Auswahlwechseln lagen die
Spitzen bei 354 bzw. 410 MiB. Speicheränderungen über kurze Auswahlfolgen
sind enthalten, aber dies ist kein Langzeitnachweis gegen Speicherlecks.
Schutzgrenzen: höchstens 1.500 Visuals bzw. 1.800 MiB Private Commit.

## Vorläufige Folgerung vor der Nutzerentscheidung

Eine sofortige Umstellung aller Linien auf das einfache AGG-Verfahren ist
nicht empfehlenswert. **Gebündeltes AGG ist als Ziel für die Draufsicht plausibel**:
Die GPU-Darstellung ist im Test schnell, der zusätzliche Prozessspeicher
überschaubar. Vor einer Übernahme sind aber Linien-Bündelung und Cache-Grenzen
für Verschieben, Zoomen und Auswahl zu implementieren und gezielt abzunehmen.
Die aktuelle Kombination mit vollständigem Neuaufbau ist dafür zu langsam.

GL bleibt schneller, löst aber die bisher beobachteten Unterschiede bei
Strichbreiten und Eckverbindungen nicht automatisch. Bei einer einheitlichen
Methode müssen außerdem Kantenglättung, Deckungsgleichheit, Farben und
logische/physische Pixel sauber abgestimmt werden. Native `LineVisual`-AGG-Pfade
in diesem Versuch sind zweidimensional; daraus folgt keine AGG-Freigabe für
die räumliche Ansicht. Keine Debian-/andere GPU-/Paket-/Releaseabnahme.

## Reproduzieren und Rohdaten

Jeder Befehl startet einen eigenen Prozess. Andere GPU-intensive Aufgaben
während des Vergleichs vermeiden. Die JSON-Dateien enthalten auch P95,
Maximalzeiten, Zählerstände pro Phase, Umgebungsdaten und DXF-Prüfsumme.

```powershell
.tox/package-build/Scripts/python.exe tools/benchmark_vispy_lines.py --method gl --output .tox/vispy-lines-gl.json
.tox/package-build/Scripts/python.exe tools/benchmark_vispy_lines.py --method agg-batched --output .tox/vispy-lines-agg-batched.json
.tox/package-build/Scripts/python.exe tools/benchmark_vispy_lines.py --method agg --output .tox/vispy-lines-agg.json
.tox/package-build/Scripts/python.exe tools/benchmark_vispy_lines.py --method gl --camera-only --samples 30 --output .tox/vispy-lines-gl-camera.json
.tox/package-build/Scripts/python.exe tools/benchmark_vispy_lines.py --method agg-batched --camera-only --samples 30 --output .tox/vispy-lines-agg-camera.json
.tox/package-build/Scripts/python.exe tools/benchmark_vispy_lines.py --method current --output .tox/vispy-lines-current.json
```

- [GL](benchmarks/2026-11-16-vispy-gl.json)
- [Gebündeltes AGG](benchmarks/2026-11-16-vispy-agg-batched.json)
- [Einfaches AGG: Schutzgrenze](benchmarks/2026-11-16-vispy-agg-stopped.json)
- [GL: Kamera-Gegenprobe](benchmarks/2026-11-16-vispy-gl-camera.json)
- [AGG: Kamera-Gegenprobe](benchmarks/2026-11-16-vispy-agg-camera.json)
- [Optimierter GL-Prototyp](benchmarks/2026-11-16-vispy-gl-optimized.json)

Der Rohdatenstatus des gestoppten Versuchs darf nicht als erfolgreiche
AGG-Performanceabnahme interpretiert werden. Die erzeugten lokalen Bilder
zeigen die gerenderte Zeichnung; überlagerte Beschriftungen bei Gesamtauswahl
sind ein bestehendes, getrenntes Darstellungsthema.

<a id="nachtrag-gl-optimierung"></a>
## Nachtrag: GL-Optimierung nach Nutzerentscheidung

Der Nutzer hat GL für Drauf- und Raumansicht gewählt, da das untersuchte
AGG-LineVisual auf 2D beschränkt ist. Der Produktionsprototyp verwendet jetzt
einheitlich GL für Modell-/Werkzeugweglinien. Der AGG-Adapter und dessen
Muster bleiben ausschließlich historisches Vergleichsmaterial; die aktuelle
Linienmethode erfordert keine privaten VisPy-Schnittstellen.

Umgesetzt: Snapshot-/Ansichtscache für Projektionen und Arrays, maßabhängiger
Strichcache, Upload nur bei geänderter Gruppenzusammensetzung, Entfernen
veralteter Stilobjekte, Einpassen vor dem ersten Upload. Alpha-Blending ist
explizit gesetzt. Exakt deckungsgleiche nicht ausgewählte Schnittsegmente
werden in der Draufsicht unter der Originalkontur ausgespart; der Plan und
die räumliche Darstellung werden dadurch nicht verändert.

Bei unverändertem Projekt/Transform/Konfiguration/Postprozessor werden reine
VisPy-Auswahländerungen ohne Neuaufbau der versteckten Legacy-Vorschau
übernommen. Der bisherige Canvas wird bei Rückkehr oder Grafikfehler
nachgezogen. Parameter-/Geometrieänderungen durchlaufen weiter die vollständige
Aktualisierung. Bei aktivierter automatischer Exportreihenfolge bleibt ebenfalls
der vollständige Pfad erhalten. Diagnosen stammen aus dem aktuellen Snapshot.

Die Wiederholungsmessung verwendet `--method current` und damit den aktuellen
GL-Code statt des experimentellen Adapters. Gleiche DXF, Hardware, Größe und
Probenzahlen wie oben; bei diesem Lauf automatische Exportreihenfolge aus.

| Vorgang | Vorher: GL mit Neuaufbau | Jetzt: optimierter GL-Prototyp |
| --- | ---: | ---: |
| Verschieben mit Mehrfachauswahl | 123,84 ms | 9,98 ms |
| Zoomen mit Mehrfachauswahl | 130,80 ms | 20,99 ms |
| Einzelauswahl wechseln | 409,21 ms | 22,03 ms |
| Mehrfachauswahl wechseln | 426,88 ms | 26,21 ms |
| Peak-Working-Set, kompletter Prozess | 448 MiB | 356 MiB |
| Peak-Private-Commit | 830 MiB | 755 MiB |

Kein direkter AGG-Nachher-Vergleich: Die Umsetzung folgt bewusst der
GL-Entscheidung. Zeiten weiterhin inklusive synchronem Bildabruf, keine
Bildschirm-FPS; aus dem kurzen Lauf folgt keine Langzeit-Leckfreiheit.

Native Prüfungen belegen: Pan ohne Projektion, Strichberechnung oder Upload;
Zoom invalidiert Strichdaten, nicht feste Schnittarrays; unveränderte Auswahl
lädt keine Daten; Auswahl ändert keine Projektion; neuer Snapshot invalidiert
die Caches. Veraltete Stilobjekte sammeln sich nicht an. Stegbearbeitung,
Projektänderung, Raumansicht, transparente Körper und Rückkehr zum bisherigen
Canvas sind fokussiert geprüft. Nutzerprüfung von Linienqualität/Ecken und
Optik bleibt wegen GL-/Treibergrenzen erforderlich.

<a id="canvas-klickpfad"></a>
## Nachtrag: Canvas-Klickpfad einschließlich Trefferprüfung

Nach Nutzerhinweis auf weiterhin langsames Selektieren am 16.11.2026 wurde
der tatsächliche Qt-Mauspfad gemessen. Die vorherige Auswahlmessung begann bei
der Baum-Auswahl und enthielt die Canvas-Trefferprüfung nicht. Deren Schleife
projizierte jeden Segmentendpunkt separat durch den VisPy-Szenengraphen und
berechnete Planprojektionen erneut. Bei keinem Bearbeitungstreffer folgte eine
weitere komplette Suche der Originalgeometrie. Das erklärte Sekunden pro Klick
trotz schneller Darstellung und bereits optimierter Baum-Auswahl.

Jetzt werden die vorhandenen Snapshot-Projektionen auch für das Picking
verwendet. Alle Endpunkte werden gesammelt transformiert und die Punkt-Segment-
Abstände mit NumPy berechnet. Ein Cache mit homogener Transformationsbasis
invalidiert die Bildschirmdaten bei Kamera-, Größen-/Skalierungs- oder
Ansichtsänderung; neue Snapshots löschen ihn. Einzelne Segmentendpunkte
durchlaufen nicht mehr jeweils den Szenengraphen. Filtern deaktivierter Pfade,
7-Pixel-Toleranz und Reihenfolge mehrerer Treffer bleiben erhalten.
Klick ins Leere leert aktuelle Zeile und Auswahl gesammelt, statt mehrfach
über native Signale plus expliziten Aufruf zu aktualisieren. Das gilt auch für
den gemeinsamen Leerraum-Auswahlpfad von Qt Quick; dessen Treffermethode wurde
nicht auf den VisPy-Cache umgestellt.

Messung: gleiche Rippen-DXF, Gerät und Canvasgröße, echte `QTest.mouseClick`-
Ereignisse. Zwei Aufwärmabläufe und je drei Proben, inklusive GPU-Bildabruf;
bei mehreren Treffern wird im Test deterministisch der erste Menüeintrag
gewählt. Produktionsbedienung behält die Auswahlfrage. Wiederholte Auswahl am
gleichen Konturpunkt; der Leerraum-Ablauf enthält **Auswahl und anschließendes
Abwählen**. Die JSON-Metrik `canvas_clear` bezeichnet diesen gesamten Zyklus,
nicht die isolierte Leerraumaktion.

| Ablauf | Vor Picking-Korrektur | Nach Picking-Korrektur |
| --- | ---: | ---: |
| Auswahlklick im Canvas | 2.487 ms | 71 ms |
| Auswahlklick und danach Leerraumklick | 8.097 ms | 93 ms |
| Peak-Working-Set im kurzen Klicktest | 350 MiB | 356 MiB |

Die Werte sind keine FPS und keine Langzeitmessung. Der Transformationscache
benötigt zusätzlichen begrenzten Speicher; kein Hinweis auf Speicherlecks aus
diesem kurzen Lauf ableitbar. Rohdaten:
[vorher](benchmarks/2026-11-16-vispy-clicks-before.json),
[nachher](benchmarks/2026-11-16-vispy-clicks-after.json).

```powershell
.tox/package-build/Scripts/python.exe tools/benchmark_vispy_lines.py --method current --clicks-only --output .tox/vispy-clicks.json
```

Fokussierte native Prüfungen vergleichen die neue Trefferliste mit der bisherigen
Referenz: Draufsicht/Raumansicht, Zoom/Rotation, überlappende Operationen,
Nullsegmente, Regionen, Originale und deaktivierte Pfade. Bildschirmdaten
werden wiederverwendet und bei leerem/neuem Snapshot gelöscht. Leerraum-
Abwahl erzeugt genau eine logische Auswahländerung und setzt den Kontext zurück.
Native Qt-Quick-/VisPy-Interoperabilität sowie Qt5-/Qt6-Vertragstests bestanden.

<a id="strip-versuch"></a>
## GL-Line-Strip-Versuch auf Nutzerwunsch

**Historischer Versuch, beendet am 16.11.2026:** Der Nutzer sah keinen
erkennbaren Eckvorteil und entschied die Rückkehr zum vorherigen Segmentweg.
Der Prototyp verwendet wieder gebündelte GL-Segmente in beiden Ansichten.
Der experimentelle Schalter, Strip-Objektpool und Strip-Caches sind entfernt;
Rendering-/Picking-Optimierungen bleiben erhalten. Die folgenden Zahlen und
Schalterangaben beschreiben ausschließlich den damaligen Versuch.

Am 16.11.2026 ausdrücklich `connect='strip'` für zusammenhängende Konturen
erprobt. Der damalige Prototyp-Schalter `VispyView.SOLID_CONNECT = 'strip'`
aktivierte diesen Weg in Drauf- und Raumansicht. Striche/Punkte blieben als
unabhängige GL-Segmente gebündelt, damit ihre Lücken nicht verbunden werden.
Es bleibt durchgehend `method='gl'`, kein AGG. Getrennte Konturen oder
unterbrochene Pfadstücke bekommen eigene LineVisuals statt einer gemeinsamen
Strip-Verbindung. Es werden keine NaN-Trennpunkte und keine privaten
OpenGL-Schnittstellen verwendet.

Die öffentliche GL-LineVisual-Schnittstelle zeichnet einen Strip pro Visual.
Daher steigt die Objektanzahl auf dieser DXF: ohne Auswahl **260**, bei
Einzelauswahl **262**, bei Mehrfachauswahl **322**, bei Gesamtauswahl **462**.
Der vorherige GL-Segmentweg benötigte im entsprechenden Ablauf 3/6/8/5 Visuals.
Ein Visual pro zusammenhängendem Stück ist dabei nicht dasselbe wie ein Visual
pro DXF-Kontur; kleine Unterbrechungen und getrennte Bewegungsrollen erzeugen
weitere Stücke. Es werden keine Konturen geometrisch repariert oder verbunden.

Ein erster Versuch erzeugte bei Stil-/Auswahlwechseln viele Strip-Objekte
erneut und war besonders langsam. Die erprobte Fassung hält deshalb pro Snapshot
und Ansicht einen begrenzten Pool pro Pfadstück. Farben/Breiten werden am
vorhandenen Objekt aktualisiert; erneute Auswahl erzeugt nicht erneut dieselben
GL-Objekte. Der Pool wird bei Snapshot-Wechsel gelöscht. Die folgende Messung
bezieht sich auf diese Fassung, nach denselben zwei Aufwärmabläufen wie zuvor.
Die erstmalige Erzeugung bislang nicht gezeichneter Strip-Objekte ist darin
nicht als separate Kaltstartmetrik ausgewiesen.

| Ablauf, einschließlich Readback | Gebündelte GL-Segmente | GL-Strips |
| --- | ---: | ---: |
| Verschieben, Mehrfachauswahl | 9,98 ms | 88,44 ms |
| Zoomen, Mehrfachauswahl | 20,99 ms | 103,62 ms |
| Mehrfachauswahl wechseln, Baum-Pfad | 26,21 ms | 103,30 ms |
| Verschieben, alle ausgewählt | 9,25 ms | 125,35 ms |
| Peak-Working-Set | 356 MiB | 447 MiB |
| Peak-Private-Commit | 755 MiB | 833 MiB |

Gleiche Rippen-DXF, Hardware, Fenstergröße und Probenzahlen. Der Versuch zeigte
eine klare Performanceverschlechterung und wurde nicht als endgültige Lösung
freigegeben. Native GL-Eckverbindungen bleiben treiberabhängig; die anschließende
Nutzerprüfung sah keinen erkennbaren Vorteil gegenüber dem schnelleren
Segmentweg. Rückkehr zum Segmentweg erfolgt, kein Umschalter mehr vorhanden.

## Präzisierung der AGG-/3D-Grenze (16.11.2026)

Auf Nutzernachfrage separat mit der öffentlichen `scene.visuals.Line`-API,
`method='agg'`, `connect='strip'` und echtem Renderaufruf geprüft, VisPy 0.17.0:
zwei XY-Punkte wurden in einer Turntable-Szene erfolgreich gerendert; zwei
XYZ-Punkte `[[0,0,0], [1,1,1]]` scheiterten beim Rendern mit
`ValueError: cannot reshape array of size 6 into shape (2,2)`.
Der direkt geprüfte interne Baker zeigte dieselbe Grenze.

Bestätigt ist damit die fehlende direkte Verarbeitung von XYZ-Punktarrays im
untersuchten Standard-AGG-LineVisual. XY-Linien können trotzdem Teil einer
räumlichen Szene sein. Daraus folgt keine allgemeine Unmöglichkeit von
AGG-basierten 3D-Ansätzen oder angepassten Adaptern; solche Lösungen wurden
hier nicht geprüft. Die frühere Kurzform „AGG unterstützt nur 2D“ ist ohne diese
Eingrenzung zu pauschal. Im VisPy-Projekt existiert ein entsprechender
[3D-AGG-Fehlerbericht für ArrowVisual](https://github.com/vispy/vispy/issues/2733),
der ebenfalls von LineVisual abgeleitet ist. Keine Änderung des aktiven GL-Wegs.

[Strip-Rohdaten](benchmarks/2026-11-16-vispy-gl-strip.json). Der Befehl mit
`--method current` prüft jetzt wieder den gebündelten Segmentweg, nicht den
hier dokumentierten historischen Strip-Stand. Die ältere GL-Optimierungstabelle oben beschreibt den damaligen
Segmentmodus und darf nicht als Performance des Strip-Modus gelesen werden.

Native Prüfungen: zwei getrennte geschlossene Stücke innerhalb einer Kontur
und eine weitere Kontur erhalten getrennte Strips; Framebuffer-Proben in den
Zwischenräumen bleiben weiß. Strichlinien bleiben Segmente. Wechsel zum
Segmentweg und zurück funktioniert; Strip-Poolobjekte bleiben bei wiederholter
Auswahl identisch und werden bei neuem Snapshot ersetzt. Cache-, Picking-,
Steg-, Drauf-/Raumansichts- und GPU-Interoperabilitätsprüfungen bestanden.
