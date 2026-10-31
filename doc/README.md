# Dokumentation

Aktuelle Arbeitsdokumente liegen direkt in diesem Ordner:

| Dokument / Ordner | Inhalt |
| --- | --- |
| [Architektur](architecture.md) | Paketstruktur und geltende Verträge für Geometrie, Planung, Vorschau und Export |
| [Todo](todo.md) | Offene Aufgaben, Prioritäten und noch zu klärende Entscheidungen |
| [Referenzen](references/) | Wissenschaftliche Veröffentlichungen und DXF-Spezifikationen |
| [Archiv](archive/) | Abgeschlossene Arbeiten, frühere Entwürfe und damalige Prüfergebnisse |
| [Ältere Unterlagen](legacy/) | Frühere Word-Dokumentationen, Präsentation, Importskript und archivierte Python-Beispiele |
| [Testübersicht](../tests/README.md) | Testauswahl und Hinweise zum Ausführen |

Die [abgeschlossenen Arbeiten](archive/toolpath-refactoring-completed.md)
dokumentieren den jeweiligen damaligen Stand. Die weiterhin gültigen
Architekturverträge stehen ausschließlich in der aktuellen Architekturdatei.
Der [ältere Lead-in-Entwurf](archive/machine-comp-radius-leadin-plan.md)
bleibt eine historische Referenz.

Die früheren Codebeispiele und Prototypen aus `python_examples/` liegen in
[python_examples.zip](legacy/python_examples.zip). Das ZIP erhält die gesamte
Ordnerstruktur und alle 66 Dateien; der ursprüngliche Ordner wurde nach
Inhaltsvergleich entfernt. Es wurden keine Verweise aus Anwendung, Tests oder
Buildskripten auf diesen Ordner gefunden.

## Referenzen einordnen

Papers bleiben unabhängig von ihrem Umsetzungsstand zusammen. Eine vorhandene
Veröffentlichung bedeutet nicht, dass ihr Verfahren vollständig implementiert
oder geprüft ist. `domain/toolpath/shapeoffset.py` nennt ausdrücklich den
Pair-wise-Offset-Algorithmus als Grundlage; die zugehörige Veröffentlichung
liegt unter [pairwise_offset_algorithm.pdf](references/pairwise_offset_algorithm.pdf).
Die übrigen Papers wurden bei dieser Ablagebereinigung nicht fachlich bewertet.

Die DXF-Spezifikationen sind [DXF 2002](references/dxf2002.pdf) und
[DXF 2010](references/acad_dxf2010.pdf). Die beiden Dateien mit dem Namensanfang
`2-1-23-28` bleiben erhalten: Sie sind gleich groß, aber nicht bytegleich.

## Historischer Projektlink

Die frühere Windows-Verknüpfung `Links/DXF2GCODE Webpage.URL` verwies auf
[DXF2GCODE auf der persönlichen T-Online-Seite](http://www.christian-kohloeffel.homepage.t-online.de/dxf2gocde.html#mozTocId700862).
Die Adresse bleibt als historische Referenz erhalten; ihre Erreichbarkeit
wurde nicht geprüft.

## Ablageregel

Aktuelle Architektur und offene Aufgaben hier pflegen, abgeschlossene
Umsetzungshistorie ins Archiv übernehmen. Ältere Unterlagen gelten nicht
automatisch als aktuelle Bedienungsanleitung. Externe Referenzen und
Originaldateien erhalten; bei Verschiebungen die relativen Links anpassen.
