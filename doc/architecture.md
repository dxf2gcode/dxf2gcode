# DXF2GCODE: Architektur und Verträge

**Dokumentstand:** 31. Oktober 2026.

Dieses Dokument beschreibt Paketstruktur und geltende Architekturverträge.
Zielverträge bedeuten keine vollständige Abnahme aller Altmodule. Offene
Arbeiten stehen in der [Todo](todo.md); zeitgebundene
Migrationsbefunde und Prüfergebnisse im [Archiv](archive/toolpath-refactoring-completed.md).

## Paketübersicht

```text
dxf2gcode/
├── bootstrap/       Launcher und Laufzeitaufbau
├── domain/
│   ├── geometry/    Punkte, Linien, Bögen und weitere Geometrie
│   ├── project/     Projekt-, Layer-, Shape- und Zeichnungsmodelle
│   └── toolpath/    Geometrie, unveränderliche Planeingaben und reine Strategien
├── application/    Import-, Projekt-, Export-, Vorschau- und Optimierungsfälle
├── adapters/
│   ├── config/      Anwendungs- und Postprozessorprofile
│   ├── dxf/         DXF-Parser und Entitätskonvertierung
│   ├── postprocessor/ G-Code-Formatierung und Maschinenprofile
│   ├── project/     Projektdateien und Speicherzugriff
│   └── toolpath/    Planeingaben, Geometrieadapter und G-Code-Serialisierung
└── presentation/
    └── qt/          Hauptfenster, Controller, Ansichten, Qt-Bindings und Ressourcen
```

Die alten Paketverzeichnisse `core`, `dxfimport`, `globals`, `gui`, `postpro`
und `Qt` sind entfernt. Interne Importe und Tests verweisen auf die neuen
Pfade; es gibt keine Re-Export-Pakete unter den alten Namen. Die ausführbare
Datei `source/dxf2gcode.py` ist jetzt ein kleiner Launcher. Qt-Designer-Dateien,
generierte UI-Module und Bilder liegen unter `presentation/qt`.

## Laufzeitwege

```text
Startskript → bootstrap.launcher → presentation.qt.application → MainWindow
GUI/CLI → application use case → adapter → Domain-Modell bzw. Dateiformat
Shape → application.toolpath → semantischer Plan → Preview und G-Code-Ausgabe
```

DXF-Import läuft über `application.importing` und den Adapter in `adapters/dxf`.
Projektdateien werden über `application.projects` und `adapters/project`
geladen und gespeichert. Konfigurationen liegen hinter `adapters/config`.
Die Anwendungsschicht enthält außerdem CLI-Export, Projektaufbau, Shape-Aktionen,
Werkzeugweg-Vorschau und Routenoptimierung.

## Verhaltens- und Formatverträge

- `.d2g`-Versionen 1.1–1.3 sowie Anwendungs- und Postprozessorprofile bleiben
  lesbar und migrierbar.
- Für die bestehenden Golden-Fälle bleibt der G-Code bytegleich.
- GUI-, CLI-, Vorschau- und Projektabläufe bleiben erhalten.
- Alte Python-Importpfade sind kein unterstütztes API und werden nicht
  wiederhergestellt.

Die Vollsuite wird mit `python tests/run_tests.py full` ausgeführt. Importtests
stellen zusätzlich sicher, dass keine alten Paketnamen im Produktionscode
verwendet werden.

## Weitergeltende Architekturverträge

### Ziel und Zuständigkeiten

Erzeugte Geometrie, vollständiger Werkzeugweg und G-Code-Ausgabe haben
getrennte Aufgaben. Darstellung und Export werden aus demselben geplanten
Weg abgeleitet. Der Umbau erfolgt schrittweise mit erhaltenem Verhalten für
bestehende Projekte; eine absichtliche fachliche Änderung wird gesondert
beschlossen und getestet.

```text
Shape + aufgelöste Einstellungen + Maschinenfähigkeiten
                         |
                         v
              Werkzeugwegplanung (domain/toolpath)
          Offset, Leads, Passfolge, Tabs, Pocket, Tipweg
                         |
                         v
             ToolpathPlan (gemeinsame Quelle)
                  /                 \
                 v                   v
       2D-/3D-Projektion       G-Code-Exporter
                                     |
                                     v
                    Postprocessor / Steuerungsdialekt
```

- **Geometrie:** Algorithmen erhalten explizite Eingaben und liefern Geometrie
  zurück. Geometrieklassen kennen weder Postprocessor noch G-Code und greifen
  nicht auf globale GUI-/Konfigurationswerte zu.
- **Planung:** legt die vollständige Reihenfolge je Tiefenpass fest:
  Positionierung, Zustellung, Kontur-/Pocket-Schnitt, Tabs, Richtungswechsel
  und Rückzug. Sie beschreibt Zustände semantisch, erzeugt keine G-Code-Texte
  und zeichnet nicht. Die Verwendung bestehender StMove-Algorithmen ist ein
  Migrationsstand, keine dauerhaft vorgeschriebene Übergangsfassade.
- **Exporter:** serialisiert fertige Bewegungs- und Zustandsaktionen. Er
  berechnet keine Offsets, Passreihenfolgen oder Taschenbahnen.
- **Postprocessor:** formatiert für die konkrete Steuerung und verwaltet
  modale Ausgabezustände wie Zahlenformat, Vorschub und Koordinatenmodus.
  Unterschiede werden über Fähigkeiten oder begrenzte Dialektmethoden
  behandelt, nicht über Maschinenart-Abfragen in Geometrieklassen.

### Planaktionen und Diagnosevertrag

Der kanonische `ToolpathPlan` ist geordnet und unveränderlich; G-Code und Qt
sind kein Bestandteil seines Vertrags. Bewegungsart und fachliche Rolle
bleiben getrennt, etwa Z-Bewegung mit Rolle `plunge`.

| Aktion | Inhalt des Plans |
| --- | --- |
| `rapid_xy`, `rapid_z` | Zielposition für Eilfahrten |
| `linear_z` mit Rolle `plunge`/`retract`, `feed` | Z-Ziel, Vorschub, Bezug auf Oberfläche/Sicherheitsabstand |
| `linear_xy`, `arc` | Start/Ende; bei Bögen Mittelpunkt, Richtung und Öffnungswinkel |
| `compensation_on`/`compensation_off` | Kompensationszustand G40/G41/G42 und Wechselpunkt |
| XY-/Z-Bewegungen mit Rolle `tab` | Betroffener Konturabschnitt, Pass und Tab-Höhe |
| `drill`, `drill_retract` | Bohrposition und geordnete Zustell-/Rückzugstiefen |
| Bewegungen mit Rolle `drag_swivel`/`ramp` | Messer-Schwenken/Rampe samt Messerspitzenweg |
| `pre_cut`, `post_cut` | Bestehende Profilaktionen vor/nach der Kontur |
| `literal` | Expliziter benutzerdefinierter G-Code für CustomGCode; kein Ersatz für Geometrieplanung |

Ein Planlauf liefert `ToolpathPlanningResult`: einen vollständigen Plan oder
Diagnosen ohne exportierbaren Plan. `ToolpathDiagnostic` enthält stabilen
Code, Schweregrad, menschenlesbare Meldung und optional Shape-/Geometriebezug.
Warnungen dürfen einen gültigen Plan begleiten. Die Planung zeigt keine
Dialoge und schreibt keine Diagnosen in G-Code. GUI/CLI übernehmen die
Präsentation; der Exportadapter übernimmt Übersetzung, Anzeige und Logging.
Der Vertrag liegt in `domain/toolpath/plan.py`. Extraktionsmarker machen
Übersetzungsquellen für Qt Linguist auffindbar, ohne Qt im Fachkern zu laden.

### Maschinenart, Kompensation und Steuerungsfähigkeiten

Diese drei Aspekte bleiben unabhängig modelliert:

1. Maschinenart: Fräse, Drehmaschine oder Schleppmesser.
2. Kompensationsverantwortung: Softwareoffset oder G41/G42 durch die Steuerung.
3. Steuerungsdialekt/Fähigkeiten: etwa Bogenbefehle und Kompensationswechsel
   zwischen Pässen.

Strategien bilden die unterstützten Maschinenarten ab. Gemeinsame Bewegungen
können gemeinsam ausgegeben werden; Bohren und Messerschwenken bleiben
fachlich unterscheidbar. Ungültige Kombinationen werden im Planer validiert
und verständlich diagnostiziert, nicht nur durch Menü-Sperren verhindert.

Bei Maschinenkompensation enthält der Plan die programmierte Kontur und
explizite G41-/G42-Übergänge. Bei Softwarekompensation enthält er den
berechneten Werkzeugmittelpunktweg und verwendet G40. Programmierte Bahn und
erwarteter Werkzeugmittelpunktweg dürfen bei gemeinsamer Darstellung nicht
verwechselt werden.

### Tiefenpässe, offene Konturen und Pocketing

- Der Planer berechnet die geordnete Tiefenfolge. Bei offenen Konturen
  bestimmt er die Passrichtung und kehrt die Geometrie bei Bedarf um.
- Bei Richtungsumkehr berücksichtigt er G41-/G42-Seitenwechsel. Ob zwischen
  Pässen ein Zurücksetzen nötig ist, wird als Steuerungsfähigkeit übergeben.
- Tabs/Breaks werden nur für ihre tatsächlichen Pässe in denselben Plan
  aufgenommen. Export und Ansichten treffen keine zweite Passauswahl.
- Pocketing liefert Bahnen als Geometrie-/Planungsergebnis, statt dauerhaft
  `StMove.geos` als gemeinsame veränderliche Ergebnissammlung zu verwenden.
  Kontur, Werkzeug, Offsetstrategie, Richtung, Wandreferenz und Freiraum sind
  explizite Eingaben.
- G40/G41/G42 bestimmen auch bei Taschen die Richtung. `always_inward`
  bleibt entfernt; ältere Profile bleiben ladbar. Die bisherige GUI-Sperre
  für Pocketing bei Maschinenkompensation bleibt zunächst bestehen; siehe
  [B1/B2](archive/toolpath-refactoring-completed.md#b1-b2).
  Die Gültigkeit ist zusätzlich im Planer zu prüfen.

### Vorschau aus demselben Plan

- **Grunddarstellung und Auswahl:** Die importierte Originalgeometrie bleibt
  in 2D und 3D immer sichtbar und bestimmt die Auswahl-/Trefferfläche.
  Erst bei Auswahl wird die geplante Werkzeugbahn zusätzlich eingeblendet;
  beim Abwählen wird diese Zusatzanzeige ausgeblendet. Die vorhandene explizite
  Option zur dauerhaften Anzeige der Zusatzpfade bleibt erhalten.
- **2D-Werkzeugwegvorschau:** jede unterschiedliche XY-Bahn einmal darstellen; keine
  deckungsgleichen Mehrfachlinien aufgrund wiederholter Tiefenpässe oder
  Richtungsumkehr. Tabs, Eilwege, Leads und Pocket-Bahnen bleiben erkennbar.
- **3D-Werkzeugwegvorschau:** XY und Z aus demselben Plan übernehmen. Die bestehende Darstellung
  zwischen Start- und Endtiefe bleibt zunächst erhalten. Werden einzelne
  Pass-Ebenen sichtbar gemacht, stammen auch diese direkt aus dem Plan.
- Programmierte und erwartete kompensierte Bahn eindeutig kennzeichnen.
- Änderungen an Tiefe, Werkzeug, Offset, Tabs, Kompensation und Leads
  invalidieren Plan und beide Projektionen gemeinsam. Keine zweite
  Berechnung von Passfolge, Tabs, Leads oder Rückzügen in den Ansichten.
- Ursprungs-Shape, Operation, resultierende Teilkontur und Tiefenpass bleiben
  unterscheidbar. Eigene Startpunkte/Leads/Overcuts je Teilkontur sind als
  [zurückgestellte Erweiterung](todo.md#teilkonturen)
  vorgesehen, keine jetzt beschlossene Zusatzimplementierung.

## Weiterführende Dokumente

- [Offene Aufgaben und empfohlene Umsetzungsreihenfolge](todo.md)
- [Abgeschlossene Arbeiten und damalige Prüfergebnisse](archive/toolpath-refactoring-completed.md)
- [Testübersicht](../tests/README.md)
