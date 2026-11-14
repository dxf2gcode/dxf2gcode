# Offene Aufgaben: Anforderungen und Abnahmekriterien

Stand: **14.11.2026** (Kandidaten-Paketabnahme aktualisiert).

Diese Datei bewahrt die Detailanforderungen der [aktiven Todo](../todo.md).
Priorität und Auswahl stehen dort; hieraus entsteht kein zusätzlicher
Umsetzungs- oder Prüfauftrag. Codebefunde behalten ihren ursprünglichen
Stand vom 30./31.10.2026, soweit nicht ausdrücklich anders vermerkt.

## Bereitstellung und Abnahme

<a id="ci1"></a>

### CI1 – Verbleibende Betriebsabnahme

**Stand vom 06.11.2026:** Der manuelle Develop-Release 2.0.0.dev12 samt
Prüfung der veröffentlichten Downloads ist vor der R3-/R1b-Umsetzung
[abgeschlossen](../archive/toolpath-refactoring-completed.md#develop-r3-checkpoint).
Die gesonderte M1-/Debian-Abnahme bleibt zurückgestellt.
Die stabile Version **2.0.0** wird erst nach Abarbeitung der gesamten Todo
freigegeben; kein stabiler Release wird vorab nur zu Prüfzwecken veröffentlicht.

Die Implementierung und Aktivierung sind in
[completed](../archive/toolpath-refactoring-completed.md#ci1) dokumentiert.
Versionsregeln, Paketprüfungen, Aufbewahrung und Betrieb stehen in der
[Release-Pipeline](../release-pipeline.md).

PR-Paketablauf und Sieben-Tage-Aufbewahrung sind mit
[PR #5 abgenommen](../archive/toolpath-refactoring-completed.md#pr5-installation);
der PR hat kein Release veröffentlicht.
- [ ] Den ersten bewusst freigegebenen stabilen Tag `v2.0.0` einschließlich
  dauerhaftem Download und „Latest“ real abnehmen. Dies ist noch keine
  Freigabe, einen stabilen Tag nur für einen Test zu erzeugen.
- [ ] Windows-Codesignierung nach Bereitstellung eines Zertifikats gesondert
  umsetzen. Der freigegebene Erststand ist ausdrücklich unsigniert.

Die Bereinigungslogik wurde mit kontrollierten Daten geprüft (13 eigene
Develop-Releases, zehn bleiben; Stable, Drafts und fremde Previews bleiben
unangetastet). Ein realer Löschlauf wird erst bei mehr als zehn eigenen
veröffentlichten Develop-Ständen notwendig. M1 bleibt eine eigene Abnahme.

<a id="m1"></a>

### M1 – macOS separat und endgültige Release-Artefakte

Windows-ZIP/MSI, frische Ubuntu-Wheels mit Qt5/Qt6 und das exakte Kandidaten-
Wheel auf Debian sind im ausdrücklich beauftragten Schritt 3
[abgenommen](../archive/toolpath-refactoring-completed.md#pr5-installation).
Dies ersetzt den früheren Quellstand-Nachweis nicht rückwirkend, sondern prüft
neu die tatsächlich installierten Kandidatenartefakte und deren Herkunft.

- macOS bleibt ohne konkrete Zielumgebung separat; vor Ausführung beauftragen.
- Im anschließenden Release-Schritt endgültige Artefakte gegen Manifest/Hashes
  abgleichen und ihren Start bestätigen. Ein neuer Build ist nicht allein durch
  den geprüften Kandidaten abgenommen.
- Keine physische Maschinen- oder reale GPU-Abnahme aus CLI/Xvfb ableiten.


## Bedienmodell: gemeinsame Planung von R3 und R1b

Der gemeinsame Plan für R3 und R1b ist vom Nutzer bestätigt. Commit, Push
und Develop-Release vor der Softwareimplementierung sind abgeschlossen;
[Nachweis](../archive/toolpath-refactoring-completed.md#develop-r3-checkpoint).
Als nächstes folgt die beauftragte Auswahl der ersten Implementierungsscheibe P1. Der
[Detailplan mit Nutzerentscheidungen](r3-r1b-implementation-plan.md) verbindet
Bedienmodell, Vererbung, Persistenz, Stegregionen und prüfbare Etappen.
Die Teilkontur-Erweiterung wird dabei berücksichtigt, aber noch nicht umgesetzt.

<a id="r3"></a>

### R3 – Geometrie und Bearbeitung im Bedienmodell trennen

**Umfang der beauftragten Planung:** Den zurückgestellten Layerwechsel R1b
gemeinsam mit diesem Bedienkonzept behandeln; aktuell keine separate
Implementierung im bestehenden Layerbaum vornehmen.

**Vorschlag zur Diskussion, noch keine Architekturentscheidung:** Importierte
DXF-Layer beschreiben die Zeichnung; die gewünschte CNC-Bearbeitung beschreibt
eine davon unabhängige Reihenfolge von Arbeitsgängen. Diese Aufgaben sollten
langfristig getrennt sichtbar sein, statt weitere Bedeutung in denselben
Layerbegriff zu packen.

```text
Geometrie                         Bearbeitung (Export von oben nach unten)
  DXF-Layer / Entities             1. Taschen – Werkzeug 2
    Originalkonturen                  Operation → referenzierte Kontur(en)
                                   2. Innenkonturen – Werkzeug 1
                                      Operation → referenzierte Kontur(en)
                                   3. Außenkonturen – Werkzeug 1
                                      Operation → referenzierte Kontur(en)
```

- [ ] **Bestätigter Entwurf vom 06.11.2026:** Die bestehenden Tabs Entities
  und Layers erhalten; Bearbeitung als dritten Tab für geordnete Gruppen und
  Arbeitsgänge ergänzen. Die Auswahl in Baum und Vorschau bleibt gekoppelt.
  Die ursprüngliche DXF-Zuordnung bleibt als Herkunft erhalten. Die genaue
  Rolle ist präzisiert: Entities und Layers dienen der Auswahl der
  Originalkonturen; der anfängliche Bearbeitungsbaum wird aus Layers
  aufgebaut. Verschieben ist nur zwischen Bearbeitungsschritten vorgesehen.
- [ ] Bearbeitungsgruppen anlegen/benennen, Werkzeug und Vorgaben zuweisen,
  Operationen per Drag-and-drop umsortieren oder in andere Gruppen verschieben.
  Zusätzliche Aktionen „Nach oben/unten“ und „In Gruppe verschieben …“ machen
  die Planung auch ohne präzises Ziehen bedienbar.
- [ ] Dieselbe Originalkontur über explizit angelegte Referenzen später in
  mehreren Arbeitsgängen nutzen können, etwa Tasche und anschließendes
  Schlichten. B1 gilt je Operation; zwei getrennte Operationen dürfen dieselbe
  Geometrie unterschiedlich bearbeiten. Verschieben und bewusstes Erzeugen
  einer weiteren Operation müssen in der Bedienung unterscheidbar sein.
  **Präzisierung vom Nutzer:** Eine Kontur kann mit Schruppen, Schlichten
  und weiteren Schritten verknüpft werden; Kopieren bedeutet zusätzliche
  Zuordnung derselben Originalgeometrie. Verschieben und Kopieren gehören
  gemäß aktualisierter Entscheidung beide zur ersten nutzbaren Version.
- [ ] Jede Operation besitzt eine stabile Identität und klare effektive
  Werkzeug-/Bearbeitungswerte. Entstehende Teilkonturen können später eigene
  Startpunkte und Leads erhalten, wie in der Teilkontur-Erweiterung beschrieben;
  Tiefenpässe sind keine separat zu sortierenden Geometrieobjekte.
- [ ] Reihenfolge und Optimierungsfreigabe im Bearbeitungsbaum sichtbar halten.
  Optimierung erfolgt innerhalb ausdrücklich freigegebener Grenzen und
  verändert niemals die fachlich geplante Gruppenreihenfolge.
- [ ] Projektpersistenz und Übernahme bestehender Layerprojekte gesondert
  planen. **Bestätigt:** Anfangsstruktur aus dem Layerbaum übernehmen;
  neue `.d2g`-Version und Leser für 1.1–1.5. Genau ein Werkzeug je Schritt;
  alte Tool-Overrides erfordern getrennte Schritte. Ebenso ist je Schritt
  genau eine Bearbeitungsart festgelegt. Bei Aufteilung gemischter alter Layer
  die ursprüngliche Ausgabereihenfolge erhalten; konkrete Migration abstimmen.

**Weiteres Vorgehen:** R1a sichert den bestehenden Baum ab. R2 hat den
Reihenfolgevertrag unabhängig vom Layerwechsel abgesichert. Der gemeinsame
R3-/R1b-Plan ist abgestimmt; nach Commit, Push und Develop-Release folgt
die Umsetzung in den geplanten kleinen Etappen. Die Teilkontur-Erweiterung
bleibt weiterhin ein gesonderter Folgeumfang.

#### Ergänzung: Break-/Haltestegregionen im Bearbeitungsmodell anlegen

**Nutzerwunsch vom 04.11.2026:** Break-Regionen sollen künftig auch ohne eine
vorher im CAD angelegte `BREAKS:`-Ebene erzeugt werden können. Gemeinsam mit
R3 planen, nicht als isolierte Erweiterung des bestehenden Layerbaums.

- [ ] Eine manuelle Aktion zum Anlegen einer Break-/Haltestegregion vorsehen;
  Erzeugen, Auswählen, Ändern und Löschen im Bedienentwurf berücksichtigen.
  Ob sie als eigener Bearbeitungsobjekttyp oder über eine Kompatibilitäts-
  Darstellung als Break-Layer gespeichert wird, ist noch zu entscheiden.
- [ ] Platzierung durch Zeichnen von Rechtecken im Canvas untersuchen,
  einschließlich späterem Verschieben und Ändern der Abmessungen. Zusammenhang
  zwischen gezeichneter Region, betroffenem Konturabschnitt und wirksamer
  Stegbreite bei Kompensation erklären.
- [ ] Optionalen Fang an bestehender Geometrie prüfen. Fangkandidaten,
  Toleranz, Ausrichtung und Verhalten bei mehreren nahen Konturen vor
  Implementierung abstimmen; Fang und frei gesetzte Position unterscheidbar halten.
- [ ] Unterstützte/automatische Platzierung prüfen, etwa nach Anzahl,
  Abstand und gewünschter Breite. Regeln für Ecken, ungeeignete Abschnitte
  und erforderliche manuelle Korrekturen gemeinsam festlegen; keine
  automatische material-/spanntechnische Eignung zusagen.
- [ ] Beziehung zu referenzierten Konturen und einzelnen Arbeitsgängen
  definieren, damit dieselbe Zeichnung unterschiedlich bearbeitet werden kann.
  Ursprüngliche DXF-Geometrie/-Layer als Herkunft erhalten; neue Regionen
  benötigen stabile Identitäten und Projektpersistenz einschließlich
  Weiterladen geänderter Zeichnungen.
- [ ] Bestehende `BREAKS:`-Projekte, absolute Steg-Z-Werte und
  „Process breaks from“ berücksichtigen. Neue Bedienung muss denselben
  Bearbeitungszustand in Vorschau und Export erzeugen; Rechteck-/Fang-/Auto-
  Erzeugung, Änderung/Löschung und Projekt-Roundtrip später gezielt absichern.

**Nutzerentscheidung vom 06.11.2026:** Zunächst Gruppen, Verschieben und Kopieren;
+manuelle Stegregionen folgen später. Rechteckzeichnen, automatische
+Platzierung und Fang bleiben Teil einer gesonderten Folgeplanung. Bestehende
+BREAKS:-Funktionen bleiben beim Grundumbau erhalten.

<a id="r1b"></a>

### R1b – Layerwechsel gemeinsam mit R3

**Planung jetzt gemeinsam mit R3 beauftragt:** Noch keine Shapes im bestehenden
Modell umhängen. Ziel sind unabhängige Bearbeitungsgruppen; Verschieben soll
die DXF-Herkunft nicht verändern. [Entwurf](r3-r1b-implementation-plan.md).

**Bestandsbefund:** Heute hängen Mitgliedschaft, `parentLayer` und
Exportreihenfolge eng zusammen. Im neuen Modell müssen Mitgliedschaft und
Exportreihenfolge der Bearbeitungseinträge zusammenpassen, während die
Layerzuordnung der Originalgeometrie unverändert bleibt.

- [ ] Konturzuordnungen zwischen Bearbeitungsschritten verschieben;
  die Original-Layer und ihre Geometrien unverändert lassen. Sortieren
  der Bearbeitung und bewusstes Erzeugen weiterer Zuordnungen trennen.
  Auswahl mehrerer Bearbeitungen und eindeutige Drop-Markierung
  beim Umhängen beziehungsweise Einfügen berücksichtigen.
- [ ] Einen Anwendungsfall für die atomare Änderung von Quell-/Ziellisten,
  Arbeitsgangmitgliedschaft, Reihenfolge und Planinvalidierung verwenden.
  `parentLayer` der Originalgeometrie nicht zum Umhängen von Bearbeitungen
  nutzen. Baum, Modell,
  Vorschau und Export anschließend aus demselben Zustand aktualisieren;
  Identität und Gesamtzahl der Shapes erhalten.
- [ ] **Bestätigte Semantik vom 06.11.2026:** Beim Verschieben explizite
  Tiefen, Vorschübe und Leads behalten und geerbte Werte aus dem Ziel
  übernehmen. Das Werkzeug stammt verbindlich aus dem Zielschritt.
  **Ebenfalls bestätigt:** Beim Kopieren eigene Werte übernehmen und
  Zielvorgaben erben; die neue Zuordnung ist unabhängig bearbeitbar.
  Unklare bisher gespeicherte Zahlen bei Migration als eigene Werte erhalten,
  ihre Herkunft nicht erraten. Wirksame Änderungen müssen erkennbar sein.
  **Weitere bestätigte Regeln:** Unpassende Zielart lehnt die gesamte Aktion
  vor Änderungen ab; neue Konturen nach Neuimport erst bewusst zuordnen;
  Rückgängig/Wiederholen für die neuen Bearbeitungsaktionen sofort vorsehen.
  Werkzeugdaten/Vorgaben im Projekt bis zur bewussten Aktualisierung erhalten.
  Gültige Aktionen direkt ausführen, Änderungen anzeigen und Undo anbieten;
  kein zusätzlicher Bestätigungsdialog beim Verschieben/Kopieren.
  Sonderlayer, Breaks und benutzerdefinierter G-Code benötigen klare Regeln.
- [ ] Speichern/Laden nach dem Verschieben prüfen. Ein notwendiger Ausbau
  der Projektzuordnung ist als eigener Kompatibilitätsschritt zu planen;
  bestehende `.d2g`-Versionen 1.1–1.5 bleiben lesbar. Keine unbemerkte
  Formatänderung als Nebenwirkung des GUI-Fixes.

**Abnahme bei späterer Umsetzung:** Quell-/Zielschritt, Hin-/Zurückverschieben,
Mehrfachauswahl, Reihenfolge, unveränderte Identitäten und Overrides sowie
Projekt-Roundtrip und tatsächlichen Export der neuen Zuordnung prüfen.
Die Absturzabsicherung R1a ist bereits abgeschlossen und dokumentiert im
[Erledigt-Dokument](../archive/toolpath-refactoring-completed.md#r1a).


<a id="teilkonturen"></a>

### Teilkontur-Erweiterung – mehrere Konturen einer Operation

**Priorität:** zurückgestellt. Auf dem abgeschlossenen Refactoring
aufbauen und das Datenmodell mit R3/R1b abstimmen; noch keine Funktion implementieren.

Wenn eine Pocket- oder Shape-Operation zwei oder mehr getrennte Inseln bzw.
Bearbeitungskonturen erzeugt, sollen diese einzeln behandelt werden können:

- [ ] Lead-in, Lead-out und Overcut je entstandener Teilkontur unabhängig
  planen und einstellen können.
- [ ] Die Startpunkte dieser Teilkonturen in der GUI einzeln auswählen und
  festlegen können, auch wenn sie zur selben ursprünglichen Shape bzw.
  Operation gehören.
- [ ] Die Zuordnung der Startpunkte und Einstellungen zu den Teilkonturen bei
  Neuberechnung sowie Speichern/Laden eines Projekts nachvollziehbar erhalten;
  das genaue Zuordnungs- und Speicherverfahren später ausarbeiten.
- [ ] Vorschau und Export verwenden dieselben Teilkonturen samt ihren
  Startpunkten, Leads und Overcuts. Mehrere Tiefenpässe und Verbindungsbewegungen
  dürfen diese Zuordnung nicht vermischen.

**Architekturleitlinie:** Ursprungs-Shape, Operation, resultierende Teilkontur
und Tiefenpass müssen unterscheidbar bleiben. Datenmodell und Schnittstellen
dürfen nicht dauerhaft genau einen Startpunkt oder genau ein Lead-/Overcut-Paar
pro Shape voraussetzen. Identifizierbare Teilkonturen müssen später als
Untergliederung eines Werkzeugwegplans ergänzt werden können. Die konkrete
Modellierung und GUI-Bedienung werden erst beim Aufgreifen dieser Erweiterung
entschieden; sie ist kein Abnahmetor für das aktuelle Refactoring.

## Optionale Qt-Bindung

<a id="q1"></a>

### Q1 – PySide6 als zusätzliche Qt-Bindung

**Optional und zurückgestellt (31.10.2026):** Aktuell werden PyQt5 und PyQt6
unterstützt; PySide6-Kompatibilität ist nicht zugesichert. Vorhandene
PySide6-Dateien aus Designer-/Ressourcenwerkzeugen sind kein Nachweis einer
funktionsfähigen PySide6-Anwendung. Kein aktueller Umsetzungsauftrag.

- [ ] Eine ausdrückliche Bindungsauswahl für PySide6 ergänzen; den bisherigen
  Standard und die PyQt5-/PyQt6-Unterstützung beibehalten. Qt-Version und
  Python-Bindung in `qt_compat` getrennt behandeln.
- [ ] Unterschiede bei Signalen, Slots, Properties, Versionsinformationen und
  den QVariant-/Shape-Referenzen im Baum zentral kapseln beziehungsweise
  prüfen. Innerhalb eines Prozesses nur eine Qt-Bindung verwenden.
- [ ] UI-/Ressourcenerzeugung, Übersetzungswerkzeuge und optionale
  Paketabhängigkeiten für PySide6 ergänzen; passende generierte Module laden.
- [ ] Bei Umsetzung zunächst gezielt Hauptfenster, Baum/Drag-and-drop,
  Auswahl und Werkzeugwegvorschau, Übersetzungen und Export prüfen.
  3D/OpenGL gesondert absichern; größere Test-/Paketläufe erst nach der
  bestehenden Freigaberegel einplanen.

Die Erweiterung bei konkretem Nutzungsbedarf als eigenen Schritt umsetzen;
der zusätzliche dauerhafte Prüfaufwand für eine weitere Bindung ist bei
der Priorisierung zu berücksichtigen.

