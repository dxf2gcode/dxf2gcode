# A1: Detaillierter Abschlussplan

Stand: **06.11.2026**. **Vollständige Variante V abgeschlossen (P0–P4,
I0–I5)**. [Ergebnis, Prüfnachweise und Grenzen](../archive/toolpath-refactoring-completed.md#a1-complete).
Die folgenden Abschnitte bewahren den beschlossenen Plan und den damaligen
Ausgangsstand; sie sind keine Liste offener Aufgaben.

## Was bereits umgesetzt ist

Der bisherige Werkzeugwegumbau bleibt abgeschlossen: explizite Planeingaben,
unveränderlicher `ToolpathPlan`, reine Geometrie-/Planungsmodule, gemeinsame
2D-/3D-Projektionen und getrennte G-Code-Serialisierung. Auch die B1/B2-Regeln
für Bohren, Taschen und G40/G41/G42 sind vorhanden. A1 ist kein Neuaufbau
dieser Architektur.

Die [Bestandsaufnahme](architecture-acceptance.md) ordnet vorhandene Tests
zu und dokumentiert 41 bestandene fokussierte Prüfungen. Zwei Dinge waren
dadurch noch nicht erledigt: eine vollständige Regel für die konkret
gefundenen Pocket-Sonderzustände und die ursprünglich weiter gefasste
Importfreiheit sämtlicher Domain-/Application-Module.

## Zwei mögliche Abschlussgrenzen

| Variante | Was danach als abgeschlossen gelten darf | Was ausdrücklich offen bleibt |
| --- | --- | --- |
| **K: Funktionslücken schließen, Kern abnehmen** | P0–P4 unten; reine Geometry-/Toolpath-Pakete und benannte bereits geprüfte weitere Module | Shape-/Layer-/Project-/CLI-Entkopplung I0–I5 als eigenes Refactoring |
| **V: Vollständige zusätzliche Entkopplung** | P0–P4 und anschließend I0–I5; erweiterte Importgrenzen tatsächlich geprüft | Paket-, Plattform-, GPU- und Maschinenabnahmen bleiben separat |

Die nicht gewählte Variante K reduziert den ursprünglichen pauschalen Abnahmeumfang und darf
deshalb nur nach ausdrücklicher Entscheidung so als A1-Abschluss bezeichnet
werden. Ohne diese Entscheidung ist die weitere Entkopplung weiterhin
unerledigt. Variante V ist ein größeres, schrittweises Refactoring; eine
bloße Aktualisierung der Abnahmetexte erfüllt sie nicht.

Empfohlene Reihenfolge bei beiden Varianten: zuerst P0–P4, weil dort
konkrete Modellzustände ohne passende Rückmeldung beobachtet wurden.
Die Architektur anschließend nach der gewählten Variante abschließen.

## P0 – Fachliche Gültigkeitsregeln festlegen

Die folgende Tabelle beschreibt den untersuchten Ausgangsstand und die
inzwischen bestätigten Sollwerte.

| Zustand | Beobachteter Iststand | Vorgeschlagener Vertrag / Entscheidung |
| --- | --- | --- |
| Fräsen, Softwarekompensation, Pocket, G40/G41/G42 | Bestehende Taschenpläne und Regressionen | Verhalten erhalten |
| Fräsen, Maschinenkompensation, Pocket | GUI bietet Pocket nicht an; direkt gesetzter Zustand liefert Plan ohne Pocket-Aktionen | Als nicht unterstützt diagnostizieren; Pocket-Wert erhalten, kein exportierbarer Plan für dieses Shape |
| Schleppmesser, Pocket | GUI bietet Pocket nicht an; direkt gesetzter Zustand liefert Plan ohne Pocket-Aktionen | Entsprechend blockieren und diagnostizieren |
| Drehen, Softwarekompensation, Pocket | Menü bietet Pocket an; Plan enthält Pocket-Aktionen | Nach ausdrücklicher Nutzerentscheidung sperren, Werte erhalten und Diagnose liefern |
| Drill mit Pocket bzw. G41/G42 | `machining.conflict`, Projektwerte bleiben erhalten | Bestehenden B1/B2-Vertrag unverändert erhalten |

Bestätigter Auftragsvertrag: Ein aktives blockiertes Shape lehnt den gesamten
Export ab. Kein Überschreiben vorhandener Dateien und keine stdout-Ausgabe.
Die Rückmeldung beim Maschinen-/Kompensationswechsel sowie GUI-/CLI-Status
müssen bei der noch offenen Anbindung diesen Vertrag umsetzen. Eine
Shape-Sperre allein ist noch kein Nachweis dieses auftragsweiten Verhaltens.

**Ergebnis:** eine entschiedene kleine Gültigkeitstabelle und eindeutig
beschriebene Shape-/Auftragsfehler, keine neue universelle Maschinenmatrix.

## P1 – Eine gemeinsame reine Gültigkeitsprüfung

Betroffene Stellen:

- `domain/project/machining.py`: bestehende Zustandsregel erweitern oder um
  eine reine Fähigkeitsprüfung ergänzen. Eingaben sind Maschinenart,
  Kompensationsverantwortung, Drill/Pocket und G40/G41/G42.
- `domain/toolpath/diagnostics.py`: stabile Diagnosecodes und übersetzbare
  Quellen für die beschlossenen nicht unterstützten Kombinationen.
- `domain/toolpath/planner.py`: vor Auswahl einer Strategie dieselbe Regel
  anwenden und bei Fehler `ToolpathPlanningResult(plan=None, ...)` liefern.

Bestehende Zustandsübergänge nicht durch eine neue Vorrangregel ersetzen.
Ein ungültiger geladener Zustand ist eine Diagnose, kein Auftrag zum
Zurücksetzen von Pocket, Drill oder Kompensation.

**Abnahme:** direkter Planeraufruf kann GUI-Sperren nicht umgehen;
positive Fälle erzeugen unverändert dieselben Aktionen, negative keinen Plan.

## P2 – Vorbereitung, Projekte und Oberflächen anschließen

- `adapters/toolpath/preparation.py` und `domain/toolpath/stmove.py`:
  ungültige Fälle vor Offset-/Pocket-/Messergeometrie erkennen; dieselbe
  Regel verwenden und keine zweite abweichende Tabelle anlegen.
- `domain/project/project.py` und die Qt-Ladekoordination:
  gespeicherte Werte unverändert wiederherstellen und die Diagnose nach
  dem Laden bzw. nach Maschinen-/Konfigurationswechsel neu auswerten.
- `presentation/qt/canvas.py` und Parameter-/Vorschauaktualisierung:
  Menüfreigaben, Warnung und fehlende Bearbeitungsüberlagerung auf den
  gemeinsamen Vertrag abstimmen. Originalgeometrie bleibt sichtbar.
- Nach ausdrücklicher Korrektur der Werte muss das Shape wieder ohne
  Neuladen nutzbar sein.

**Abnahme:** kein stilles Reparieren alter Projekte, kein veralteter Plan,
keine widersprüchliche Freigabe zwischen Menü und geladenem Modell.

## P3 – Export und gezielte Regressionen

Die bereits vorhandenen Tests erweitern, statt dieselben Abläufe nochmals
mit neuen Testfassaden abzubilden:

| Ebene | Gezielte Nachweise |
| --- | --- |
| Reine Regel/Planer | Je beschlossener ungültiger Kombination eine stabile Diagnose; positive Software-Pockets G40/G41/G42 und bestehende Drill-Konflikte erhalten |
| Vorbereitung | Keine aufwendige Geometrieerzeugung und kein stehengebliebener alter Plan für ein blockiertes Shape |
| Projekt-Roundtrip | Echter gespeicherter Pocket-Wert bleibt erhalten; Maschinen-/Kompensationswechsel und ausdrückliche Auflösung aktualisieren die Diagnose |
| GUI/Vorschau | Menüfreigabe und Warnung stimmen mit Planung überein; Originalkontur bleibt, ungültige Werkzeugbahn fehlt; nach Korrektur wieder sichtbar |
| Export | Direkter Plan-/Dateiexport und CLI eines Projekts erkennen denselben Zustand; gültiges und ungültiges Shape gemeinsam nach P0-Vertrag prüfen |
| LinuxCNC-stdout-Filter | Nicht unterstützter Projekt-/Modellzustand führt zu Fehlerstatus und leerem stdout, nicht zu erfolgreicher Konturausgabe statt Pocketing |

Geeignete vorhandene Dateien: `dxf2gcode_machining_modes_test.py`,
`dxf2gcode_pocket_comp_mode_test.py`, `dxf2gcode_toolpath_contract_test.py`,
`dxf2gcode_toolpath_preview_test.py`, Projekt-/Export-Anwendungstests und
`dxf2gcode_linuxcnc_filter_test.py`. Den falsch benannten Lathe-Menütest
erst nach der Entscheidung in P0 an den tatsächlichen Sollvertrag anpassen.

GUI-Vertrag unter PyQt5 und PyQt6 prüfen. Neue sichtbare Meldungen in DE/FR/RU
übersetzen, QM-Dateien regenerieren und die geänderten Übersetzungen prüfen.
Die Kopfzeilenkorrektur und die aktuelle LinuxCNC-Filterlogik erhalten.

## P4 – Funktionalen Abschluss nachweisen

Pro Kombination festhalten: Entscheidung, betroffene Einstiege, vorhandene
oder ergänzte Regression und verbleibende Grenze. Keine neuen Golden-Dateien
für unveränderte positive Fälle nur zur Bestätigung erzeugen; vorhandene
Referenzen verwenden. Bei absichtlicher Verhaltensänderung den Grund benennen.

**Fertig, wenn:** die beschlossene Gültigkeit über Vorbereitung, Planung,
Projekt, GUI/CLI und Vorschau konsistent gilt und P3 bestanden ist. Danach
ist die konkrete Pocket-Lücke geschlossen, die allgemeine Importentkopplung
aber nur bei Variante K ausdrücklich aus diesem Abschluss ausgeklammert.

## I0 – Importziel und Laufzeitmetadaten vorbereiten

Nur bei Variante V oder eigenem Folgeauftrag:

- Direkte und transitive Abhängigkeiten von `domain/project`,
  `domain/constants`, `application/drawings` und `application/cli_export`
  erfassen; bestehenden Geometry-/Toolpath-Importtest als feste Grenze halten.
- Qt-abhängige Runtime-Versionsbildung aus `domain/constants.py` an den
  Laufzeit-/Präsentationsrand verlagern. Reine Namen/Pfade/Konstanten und
  Metadaten nicht mehr durch denselben Qt-Import koppeln.
- Vorhandene Ports, `ToolSettings`, Diagnosen und `ApplicationContext`
  wiederverwenden. Neue Schnittstellen nur für tatsächlich notwendige Werte.

**Abnahme:** bisher reine Module bleiben rein; G-Code-Kopf und Infofenster
zeigen weiterhin korrekte Herkunft/Version ohne verschachtelte Kommentare.

## I1 – Shape und Layer von Runtime/Qt lösen

- `shape.py`: globale Defaults, Meldungsdarstellung und sonstige Qt-Aufrufe
  durch explizite Einstellungswerte, Rückgaben/Diagnosen und bereits
  vorhandene optionale Darstellungs-Callbacks ersetzen.
- `layercontent.py`: Werkzeugtabelle, Layerparser-Vorgaben und geerbte
  Bearbeitungswerte explizit übergeben; Auswahl-/Qt-Übersetzung außerhalb.
- Konstruktoraufrufe am gemeinsamen Modellaufbau und an GUI-/CLI-Rändern
  umstellen. Keine Domain-Abhängigkeit auf eine neue Bootstrap-Fassade.

**Abnahme:** Shape/Layer sind ohne PyQt und ohne `runtime_state` importierbar
und mit expliziten Testwerten verwendbar. Werkzeugvererbung, Shape-Overrides,
Einheiten, Layernamen und Bearbeitungswerte bleiben unverändert.

## I2 – Projektmodell, Codec und GUI-Koordination trennen

- Den vorhandenen `.d2g`-Codec und Repository verwenden; aktuell unterstützte
  Versionen **1.1–1.5** einschließlich der neuen Messerwerte erhalten.
- Direkten Codec-Import, TreeHandler-/Canvas-/Cursor-/`processEvents`-Aufrufe
  aus `domain/project/project.py` an Adapter bzw. Anwendungs-/Qt-Koordination
  verschieben. Modelloperationen erhalten explizite Daten und liefern Werte.
- Dieselbe Projektanwendung für GUI und CLI nutzen; die heutige
  `_HeadlessProjectSession` mit GUI-No-ops schrittweise entbehrlich machen.

**Abnahme:** Laden, Speichern, Reload, Transformieren und Roundtrip erhalten
Reihenfolge, Startpunkte, Werkzeugüberschreibungen, Einheiten, Konfliktwerte
und Messeroptionen. Ein fehlender Zeichnungspfad benötigt in der CLI keine
nachgebildeten GUI-Methoden; die GUI kann weiterhin einen Ersatzpfad wählen.

## I3 – Modellaufbau und CLI nur über explizite Abhängigkeiten

- `application/drawings.py` gegen die nun reinen Modelle führen; Parserdaten
  nicht zusätzlich in ein paralleles Projektmodell kopieren.
- In `application/cli_export.py` Reader, Vorbereitung, Projektanwendung und
  Exportdienst injizieren. Konkrete Adapterauswahl nach `bootstrap/composition.py`.
- Qt-spezifische Übersetzung und Dateidialoge an der Präsentationsgrenze
  halten; Dateiexport, stdout-Filter und headless CLI als getrennte Einstiege
  mit gemeinsamem fachlichem Plan erhalten.

**Abnahme:** keine konkreten Adapter-/Presentation-/Runtime-Importe mehr in
den ausdrücklich erweiterten Application-Modulen; vorhandene Endpunkte und
Fehlerstatus bleiben erhalten. Keine zweite Planung für CLI oder Vorschau.

## I4 – Erweiterte Grenze tatsächlich testen

- Nach jeder umgestellten Scheibe frische Importprozesse ohne Qt/Runtime
  prüfen; am Ende alle vereinbarten Domain-/Application-Module transitiv.
- Neben Importen echte Konstruktion/Modelloperationen mit expliziten Werten
  ausführen, damit Abhängigkeiten nicht nur in Funktionskörper verschoben sind.
- Projekt-, GUI-/CLI-, Preview-/Export- und Golden-Nachweise passend zur
  jeweiligen Änderung einmal ausführen; keine komplette Testserie pro Datei.

Ein reiner Importtest allein beweist weder vollständige Laufzeitentkopplung
noch unverändertes Bearbeitungsverhalten.

## I5 – Erweiterte Architekturabnahme abschließen

**Fertig, wenn:** Zielmodule ohne Qt/Runtime/konkrete Außenadapter importierbar
und ausführbar sind, Adapter im Composition Root erzeugt werden und die
Verhaltensverträge aus I1–I4 bestehen. Bis dahin bleibt Variante V offen.
Erst dann die Architekturtexte auf den tatsächlich erreichten Umfang ändern.

## Reihenfolge, Commitgrenzen und Prüfaufwand

1. P0 entscheiden, P1–P3 als zusammenhängende fachliche Korrektur umsetzen,
   P4 nachweisen. Bei Bedarf eigene kleine Commits für Regel/Anbindung und
   Integration, jeweils in funktionsfähigem Zustand.
2. Bei Variante K den begrenzten A1-Abschluss und die gesondert offenen
   I-Arbeiten dokumentieren. Bei Variante V I0, I1, I2 und I3/I4 als getrennte
   verhaltensbewahrende Scheiben bearbeiten, danach I5.
3. Vor Quellcode-/Testcommits die Fast-Suite genau über den Hook ausführen;
   bereits bestandene gezielte Checks nicht ohne Anlass wiederholen.
4. Reine Planungs-/Dokumentationscommits benötigen nur passende Dokumentchecks.
   Vollsuite, erneute Debian-/SSH-, Release-/MSI- und Maschinenprüfungen sind
   hiermit nicht freigegeben; GitHub-CI bleibt der reguläre Vollprüfweg.

Die funktionale Korrektur P ist begrenzt. I betrifft mehrere Laufzeit- und
Persistenzgrenzen und ist entsprechend deutlich umfangreicher. Eine belastbare
Zeitangabe wäre erst nach Wahl der Variante und P0-Entscheidungen sinnvoll.
