# Werkzeugweg- und G-Code-Refactoring

## Ziel

Die erzeugte Geometrie, der geplante Werkzeugweg (bisher vor allem `StMove`)
und die G-Code-Ausgabe sollen klar getrennte Aufgaben haben. Darstellung und
Export sollen aus demselben geplanten Werkzeugweg abgeleitet werden. Das
Refactoring soll schrittweise und mit unverändertem Verhalten für bestehende
Projekte erfolgen.

### Vorgemerkte spätere Erweiterung

Pocket- oder Shape-Operationen können mehrere getrennte Bearbeitungskonturen
erzeugen. Für diese sollen später eigene Startpunkte in der GUI sowie
unabhängige Lead-in-, Lead-out- und Overcut-Einstellungen möglich sein.
Architekturentscheidungen müssen daher Ursprungs-Shape, Operation,
resultierende Teilkonturen und Tiefenpässe auseinanderhalten und eine spätere
Zuordnung von Startpunkten und Einstellungen je Teilkontur ermöglichen.

Diese Funktion ist zurückgestellt und wird im aktuellen Refactoring noch
nicht umgesetzt. Die offenen Punkte stehen im Abschnitt
[„Zurückgestellte Erweiterung“ der TODO-Liste](toolpath-refactoring-todo.md#zurückgestellte-erweiterung-mehrere-konturen-einer-operation).

## Ausgangslage

- `core/stmove.py` erzeugt Anfahr- und Offsetgeometrie, baut Pocketmilling in
  dieselbe veränderliche Geometriesammlung ein und enthält außerdem
  Vorschau-Zeichenlogik.
- `core/shape.py` enthält mit `Write_GCode()` die Auswahl und Ausgabe von
  Software- oder Maschinenkompensation, Tiefenpässen, Richtungsumkehr,
  Breaks/Tabs, Lead-in/Lead-out und Rückzügen. Das Schleppmesser hat einen
  separaten Exportpfad.
- `core/linegeo.py` und `core/arcgeo.py` formatieren ihre Bewegungen selbst,
  indem sie direkt Methoden des Postprocessors aufrufen.
- `core/pocketmill.py` baut Pocket-Bahnen, liest dabei Zustand aus `StMove`
  und hängt Geometrien an dessen Liste an.
- `postpro/postprocessor.py` steuert den Export über Layer und Shapes und
  formatiert zugleich Steuerungsbefehle.
- Maschinenart und Kompensationsverantwortung sind getrennte Einstellungen,
  wirken aber über mehrere Module hinweg: Maschinenart (`milling`, `lathe`,
  `drag_knife`), Software- oder Maschinenkompensation und die Richtung `G40`,
  `G41` oder `G42`.

Die Vorschau zeigt bereits Teile des geplanten Weges. Sie ist aber keine
vollständige Quelle der Exportbewegungen: der Export expandiert die
Tiefenpässe, kehrt offene Konturen um, behandelt Tabs je nach Pass und erzeugt
Rückzüge und Zustellungen separat. Die 2D- und 3D-Ansicht sind außerdem
unterschiedliche Projektionen des Weges. Die 2D-Ansicht soll wiederholte
XY-Bahnen nicht mehrfach übereinander zeichnen. Die 3D-Ansicht soll ihre
Tiefeninformation behalten; die bisherige Darstellung zwischen Start- und
Endtiefe soll zunächst erhalten bleiben.

## Zielarchitektur

```text
Shape + aufgelöste Einstellungen + Maschinenfähigkeiten
                         |
                         v
       Werkzeugwegplanung / StMove-Übergangsschicht
         | Offset, Lead, Passfolge, Tabs, Pocket
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

### Geometrie

- Geometrie- und Offsetalgorithmen nehmen explizite Eingaben entgegen und
  liefern Geometrie zurück.
- Geometrieklassen kennen weder den Postprocessor noch G-Code-Befehle.
- Die Algorithmen hängen nicht von globalem GUI- oder Konfigurationszustand
  ab. Die benötigten Werte werden als Einstellungen übergeben.

### Werkzeugwegplanung und `StMove`

- `StMove` beziehungsweise eine schrittweise eingeführte
  `ToolpathPlan`-Schnittstelle ist die mittlere Ebene zwischen Geometrie und
  Ausgabe.
- Sie legt die vollständige Reihenfolge pro Tiefenpass fest: Positionierung,
  Zustellung, Schnittgeometrie, Pocket-Bahnen, Tabs, Richtungswechsel und
  Rückzug.
- Sie beschreibt Kompensationszustände und Übergänge semantisch. Sie erzeugt
  keine G-Code-Strings und zeichnet nicht selbst.
- Für Maschinenkompensation enthält der Plan die programmierte Kontur und die
  G41/G42-Übergänge. Für Softwarekompensation enthält er bereits den
  berechneten Werkzeugmittelpunktweg und verwendet G40.
- Falls beide Darstellungen gebraucht werden, hält der Plan programmierte
  Bahn und erwarteten Werkzeugmittelpunktweg auseinander.

#### Vertrag für Planaktionen und Diagnosen

Der kanonische Plan ist geordnet und unveränderlich. Er beschreibt die
Bearbeitung unabhängig von G-Code-Text und Qt. Die semantischen Aktionen
decken die folgenden Fälle ab. Bewegungsart und fachliche Rolle sind getrennt;
beispielsweise ist eine Zustellung eine Z-Bewegung mit der Rolle `plunge`.

| Aktion | Inhalt des Plans |
| --- | --- |
| `rapid_xy`, `rapid_z` | Zielposition für eine Eilfahrt |
| `linear_z` mit Rolle `plunge`/`retract`, `feed` | Z-Ziel, Vorschub und Bezug zu Werkstückoberfläche bzw. Sicherheitsabstand |
| `linear_xy`, `arc` | Start, Ende und bei Bögen Mittelpunkt sowie Drehrichtung/Öffnungswinkel |
| `compensation_on`/`compensation_off` | G40/G41/G42-Zustand und nötiger Wechselpunkt |
| XY-/Z-Bewegungen mit Rolle `tab` | Konturabschnitt und Z-Höhe, an denen der Tab aktiv ist |
| `drill`, `drill_retract` | Bohrposition und geordnete Zustell-/Rückzugstiefen |
| Bewegungen mit Rolle `drag_swivel`/`ramp` | Schwenk-/Drag-Aktion und zugehörige Tipweg-Geometrie |
| `pre_cut`, `post_cut` | Semantische Schnittstellen für die bestehenden Profilaktionen vor/nach der Kontur |
| `literal` | expliziter benutzerdefinierter G-Code; nur für CustomGCode, nicht für Geometrieplanung |

Ein Planlauf liefert einen ToolpathPlanningResult: entweder einen
vollständigen Plan oder Diagnosen ohne exportierbaren Plan. Diagnosen
(ToolpathDiagnostic) tragen einen stabilen Code, Schweregrad,
menschenlesbare Meldung und optional Shape-/Geometriebezug. Warnungen dürfen
einen gültigen Plan begleiten. Planung zeigt keine Dialoge und serialisiert
keine Diagnose in G-Code; GUI und CLI präsentieren sie selbst. Der Vertrag ist
in domain/toolpath/plan.py definiert. Die reinen Strategien geben ihre Fehler
und Warnungen darüber zurück; der Exportadapter übernimmt erst anschließend
deren Übersetzung, Anzeige und Logging. Extraktionsmarker halten die
Übersetzungsquellen für Qt Linguist auffindbar, ohne Qt im Fachkern zu laden.

### Maschinenart und Kompensation

Diese Aspekte bleiben voneinander getrennt:

1. **Maschinenart** beschreibt die Bearbeitungslogik: Fräse, Drehmaschine oder
   Schleppmesser.
2. **Kompensationsverantwortung** beschreibt, ob dxf2gcode den Offset
   geometrisch berechnet oder die Maschinensteuerung G41/G42 ausführt.
3. **Steuerungsdialekt und Fähigkeiten** beschreiben, welche Befehle und
   Übergänge ein Postprocessor unterstützt, etwa Bogenbefehle oder
   Kompensationswechsel zwischen Pässen.

Die Planungslogik wählt für unterstützte Maschinenarten passende Strategien.
Gemeinsame Bewegungsarten können gemeinsam ausgegeben werden. Spezifische
Bewegungen, zum Beispiel Schleppmesser-Schwenken oder Bohren, bleiben als
eigene semantische Aktionen darstellbar. Ungültige Kombinationen werden beim
Planen geprüft und mit einer verständlichen Fehlermeldung abgelehnt.

### Tiefenpässe und offene Konturen

- Der Planer berechnet die Tiefen und erzeugt eine geordnete Passliste.
- Bei offenen Konturen bestimmt der Planer die Richtung jedes Passes und kehrt
  die Geometrieelemente bei Bedarf um.
- Wird Maschinenkompensation genutzt, berücksichtigt der Plan den Wechsel der
  Kompensationsseite bei umgekehrter Laufrichtung (`G41`/`G42`). Ob die
  Steuerung die Kompensation zwischen Pässen zurücksetzen muss, kommt als
  Postprocessor-Fähigkeit beziehungsweise -Regel in die Planung.
- Breaks/Tabs werden für die tatsächlich betroffenen Pässe in denselben Plan
  aufgenommen. Vorschau und Export dürfen diese Auswahl nicht unabhängig
  voneinander erneut berechnen.

### Pocketmilling

- Pocketmilling bleibt ein Geometrie-/Planungsschritt und erzeugt
  Pocket-Bahnen als Ergebnis, statt `StMove.geos` direkt zu verändern.
- Der Planer übergibt Kontur, Werkzeug, Offsetstrategie, Richtung,
  Wandreferenz und Freiraum explizit.
- `always_inward` und `selected_direction` bleiben fachliche Optionen der
  Pocket-Planung.
- Zunächst bleibt die bestehende Einschränkung erhalten, dass die GUI
  Pocketmilling bei Maschinenkompensation nicht anbietet. Die Gültigkeit wird
  zusätzlich im Planer geprüft und nicht allein der GUI überlassen.

### G-Code-Ausgabe

- Ein gemeinsamer Exporter durchläuft den fertigen Plan und serialisiert
  Bewegungs- und Zustandsaktionen.
- Der Exporter berechnet keine Offsets, Passreihenfolgen oder Taschenbahnen.
- Der Postprocessor formatiert die Aktionen für eine konkrete Steuerung und
  verwaltet notwendige Ausgabezustände wie Zahlenformat, Vorschub und
  Koordinatenmodus.
- Steuerungsspezifische Varianten werden über Fähigkeiten oder eng begrenzte
  Dialektmethoden behandelt, nicht durch Maschinenart-Abfragen in
  Geometrieklassen.

## Vorschau aus demselben Plan

Der Plan ist die Quelle sowohl für Export als auch Darstellung. Die Ansichten
projizieren ihn passend zu ihrem Zweck:

- **2D:** zeigt jede unterschiedliche XY-Bahn einmal. Wiederholte
  Tiefenpässe und deren Richtungsumkehr erzeugen keine deckungsgleichen
  Mehrfachlinien. Tabs, Eilwege, Lead-in, Lead-out und Pocket-Bahnen bleiben
  entsprechend ihrer Bedeutung unterscheidbar.
- **3D:** übernimmt XY und Z aus dem Plan. Die bestehende Darstellung über
  Start- und Endtiefe bleibt zunächst erhalten. Falls einzelne Tiefenpässe
  sichtbar gemacht werden, stammen deren Ebenen ebenfalls direkt aus dem
  Plan.
- **Kompensation:** die Vorschau kennzeichnet eindeutig, ob sie die
  programmierte Bahn oder den erwarteten Werkzeugmittelpunktweg zeigt.
- **Dynamische Daten:** Änderungen an Tiefe, Werkzeug, Offset, Tabs oder
  Kompensation invalidieren und erneuern den Plan sowie beide Ansichten
  gemeinsam.

## Umsetzung in Etappen

### 0. Verhaltensmatrix festhalten

Vor Änderungen werden die gültigen Kombinationen und erwarteten Ergebnisse
als Tests beziehungsweise Testmatrix festgehalten:

- Maschinenarten: Fräse, Drehmaschine, Schleppmesser;
- Kompensation: Software und Maschine;
- Richtung: G40, G41 und G42, soweit für die Kombination gültig;
- offene und geschlossene Konturen;
- einzelne und mehrere Tiefenpässe;
- Tabs/Breaks, Lead-in/Lead-out und Overcut;
- Pocketmilling mit beiden Richtungsoptionen;
- Postprocessor-Regeln für Bogenexport und Kompensationswechsel.

Vorhandene Golden-G-Code-Tests und die vollständige Suite bilden die
Verhaltensbasis. Der zuletzt gemessene Stand war 644 Tests und 73 %
Gesamtabdeckung; die Abdeckung ist kein Ersatz für gezielte Verhaltenstests.

### 1. Plan-Datenmodell einführen

Ein kleines, GUI- und Postprocessor-freies Modell für Pässe und semantische
Bewegungen einführen. Den ersten Plan noch aus den bestehenden
`StMove`-Geometrien zusammensetzen. Damit kann die neue Schnittstelle
eingeführt werden, ohne die Geometriealgorithmen gleichzeitig umzuschreiben.

### 2. Ausgabe vom Shape entkoppeln

Die G-Code-Orchestrierung aus `Shape.Write_GCode()` schrittweise in einen
Exporter verschieben. Zuerst einen bestehenden Fräsfall abbilden, dann
Maschinen-/Softwarekompensation, Mehrfachpässe und offene Konturen ergänzen.
Golden-Ausgaben und Exportbewegungen müssen dabei erhalten bleiben.

### 3. Vorschau an den Plan anschließen

2D und 3D lesen dieselben Pass- und Bewegungsdaten wie der Exporter. 2D
projiziert gleiche XY-Bahnen einmal; 3D behält die Tiefendarstellung. Tabs und
Lead-out werden nicht erneut separat durch Vorschau-Code geplant.

### 4. Geometrieerzeugung aus `StMove` herauslösen

Offset, Lead-Geometrie, Pocket-Bahnen und Schleppmesser-Tipweg in
Geometriefunktionen oder spezialisierte Planer verschieben. `StMove` wird
während der Migration Adapter für bestehende GUI-Aufrufer und wird erst
entfernt oder umbenannt, wenn keine Aufrufer mehr davon abhängen.

### 5. Maschinenstrategien und Randfälle vervollständigen

Drehmaschine und Schleppmesser sowie Postprocessor-Fähigkeiten schrittweise
auf das Planmodell umstellen. Danach Pocketmilling und alle bisher gültigen
Kombinationen absichern. Unterstützungsgrenzen werden zentral validiert.

### 6. Alte Kopplungen entfernen

Direkte `Write_GCode()`-Methoden aus Geometrieklassen, doppelte
Pass-/Tab-/Lead-Berechnungen und globale Zustandszugriffe entfernen, sobald
alle Aufrufer umgestellt und die Regressionstests grün sind.

## Abnahmekriterien

- Planer, Geometrieberechnung, Vorschau und G-Code-Formatierung sind getrennt
  testbar.
- Vorschau und Export greifen auf denselben Plan zu; keine zweite Berechnung
  von Passreihenfolge, Tabs oder Lead-out findet im jeweiligen Ausgabeweg
  statt.
- 2D zeigt keine deckungsgleichen Linien für wiederholte Tiefenpässe.
- 3D behält die Tiefenausdehnung bei und kann Tiefenpass-Ebenen aus dem Plan
  darstellen.
- Softwareoffsets sind geometrisch im Plan enthalten; Maschinenoffsets
  erscheinen als explizite Kompensationszustände zur programmierten Bahn.
- Bestehende Golden-G-Code-Ausgaben und vollständige Regressionstests bleiben
  grün oder jede absichtliche Änderung ist dokumentiert und fachlich geprüft.
- Unterstützte und nicht unterstützte Maschinen-/Kompensationskombinationen
  sind explizit getestet.

## Arbeitsregeln

- Kleine vertikale Scheiben umbauen und nach jeder Etappe fokussierte Tests
  sowie die Gesamtsuite ausführen.
- Geometrieausgabe nicht gleichzeitig mit Geometriealgorithmen ändern, wenn
  sich der Effekt nicht getrennt validieren lässt.
- Die bestehende G-Code-Ausgabe als Verhaltensvertrag behandeln, bis eine
  fachliche Änderung ausdrücklich beschlossen ist.
- Keine großflächige Umbenennung oder Verzeichnisverschiebung als ersten
  Schritt durchführen.
