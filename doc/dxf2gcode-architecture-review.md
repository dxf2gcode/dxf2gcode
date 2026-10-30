# DXF2GCODE: Zielstruktur und Migrationsstand

**Stand:** 29. Oktober 2026
**Ziel:** Eine eindeutige Paketstruktur ohne parallele alte Paketbereiche.

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

## Noch offene Architekturgrenzen

Die Paketnamen und Dateipfade sind vereinheitlicht; die inhaltliche Entkopplung
ist noch nicht vollständig. Diese Punkte sind sichtbar und dürfen nicht als
abgeschlossene Zielarchitektur behandelt werden:

- Mehrere Domain-Module greifen noch auf `bootstrap.runtime_state` zu; einige
  verwenden zudem Qt für Übersetzung oder Warnmeldungen.
- `presentation.qt.application` enthält weiterhin CLI-Start, Laufzeitaufbau
  und GUI-Orchestrierung neben dem Hauptfenster.
- `adapters/dxf/parser.py` enthält den bestehenden Parser und liefert noch
  legacy-orientierte Modellobjekte.
- Alle Shape-Exporte laufen über einen `ToolpathPlan` mit semantischen
  Aktionen. `domain/toolpath/planner.py` wählt reine Strategien für einfache
  Fräsfälle, Konturen und Schleppmesser. Ein Adapter übergibt unveränderliche
  Geometrie-, Einstellungs- und Fähigkeitsdaten. Die Planung führt keine
  Postprocessor-Methoden mehr aus; Shape-Builder und Recorder sind entfernt.
  Die vorbereiteten Offset-/Pocket-/Lead-Geometrien stammen weiterhin aus
  den bestehenden Algorithmen. Deren globale und Qt-Kopplungen sowie die
  vollständige fachliche Fallmatrix bleiben weitere Arbeitsschritte.
- Projektserialisierung und Teile der Bearbeitungslogik liegen noch in den
  Domain-Modellen, statt vollständig über Ports und Adapter zu laufen.

Die nächsten Schritte verlagern diese Zuständigkeiten in kleinen Scheiben:
Laufzeitkonfiguration explizit an Anwendungsfälle übergeben, Importdaten
normalisieren, den Werkzeugwegplan auf alle Maschinenarten ausweiten und
schließlich die Start- und UI-Koordination trennen. Erst danach sind die
Abhängigkeitsregeln der Zielstruktur vollständig erfüllt.

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

## Weiterführende Dokumente

- [Umsetzungsplan Werkzeugweg und G-Code](toolpath-refactoring-plan.md)
- [Testübersicht](../tests/README.md)
