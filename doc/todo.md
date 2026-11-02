# DXF2GCODE: offene Aufgaben und Umsetzungsreihenfolge

Stand: **02.11.2026**.

Diese Todo enthält die verbleibenden Aufgaben. Abgeschlossene Arbeiten,
historische Prüfergebnisse und verworfene Wünsche stehen im neuen Dokument
[Abgeschlossene Arbeiten und Prüfergebnisse](archive/toolpath-refactoring-completed.md).
Die [Architekturverträge](architecture.md#weitergeltende-architekturverträge)
gelten weiter. Die früheren Werkzeugweg-Etappen 1–6 und 5a sowie K3 und
[B1/B2](archive/toolpath-refactoring-completed.md#b1-b2) sind abgeschlossen.

Die Reihenfolge unten ist ein Prioritätsvorschlag, kein Auftrag zur Umsetzung
aller Punkte. Die bestehenden Kennungen bleiben erhalten. Codebefunde und
Prüfvorschläge stammen aus der Untersuchung vom 30./31.10.2026; diese
Dokumentbereinigung ist keine neue Codeprüfung. Offene fachliche Entscheidungen
werden vor der jeweiligen Implementierung geklärt.

## Überblick und empfohlene Reihenfolge

| Reihenfolge | Abschnitt / Aufgaben | Grund und Voraussetzungen |
| --- | --- | --- |
| Abgeschlossen | [Exportablauf und Werkzeugwechsel](#1-exportablauf-und-werkzeugwechsel): P1 und R2 | P1 für den vereinbarten manuellen LinuxCNC-Ablauf softwareseitig geprüft; Praxisprüfung bleibt beim Anwender |
| Abgeschlossen | [Schleppmesser](#2-schleppmesser): D1 und D2 | Lokal softwareseitig umgesetzt und gezielt unter Qt5/Qt6 geprüft; praktische Materialprüfung bleibt beim Anwender |
| 1 | [Konfiguration und Bedienung](#3-konfiguration-und-bedienung): V1, U3, U5 (K1/K2 abgeschlossen) | Übersetzungen, Profilvorgaben und Hilfetexte sind abgesichert; offene Bedienentscheidungen vor Umsetzung abstimmen |
| 2 | [Paketabnahme und Abnahmegrenzen](#4-paketabnahme-und-abnahmegrenzen): CI1, M1, A1 | Automatische Build-/Download-Pipeline und Aufbewahrung einrichten; Paketabnahme und verbleibende Abnahmegrenzen berücksichtigen |
| Zurückgestellt | [Bedienmodell und Teilkonturen](#5-zurückgestelltes-bedienmodell-und-teilkonturen): R3 mit R1b, anschließend Teilkontur-Erweiterung abstimmen | Kein Layerwechsel vor dem gemeinsamen Bedien-/Modell-/Persistenzentwurf |
| Optional | [Zusätzliche Qt-Bindung](#6-optionale-zusätzliche-qt-bindung): Q1 | PySide6 nur bei konkretem Bedarf als eigener Schritt |

**Abgrenzungen:** R1a, U1, U2, U4 und I2 sind erledigt. I1 (kurze Segmente
markieren) und R4 (alphanumerische Layersortierung) wurden ausdrücklich
abgewählt. Diese Punkte werden nicht erneut als offene Aufgaben geführt.
M1 ist trotz bestandener Debian-Quelltests weiterhin eine offene Paketabnahme.

**Aktueller Abschluss, 02.11.2026:** K1-Konfigurationsübersetzungen und der
vereinbarte P1-LinuxCNC-Softwareumfang sind abgeschlossen. Zusätzlich sind
skalierungsabhängige Windows-Symbolgrößen, eine stabile Taskleistenkennung,
die kompakte Infofenster-Wortmarke und der Link zur
[Dokumentation im Aufbau](https://dxf2gcode.github.io/dxf2gcode/) umgesetzt.
Details und Prüfgrenzen stehen im
[Erledigt-Dokument](archive/toolpath-refactoring-completed.md#gui-branding).

**D1/D2 softwareseitig abgeschlossen, 02.11.2026:** Rampen und Konturschluss,
Tiefenzustellungen, zusätzliche Endtiefenfahrt, offene Umkehr und auswählbare
Messerstellung sind implementiert. [Plan und Prüfnachweise](drag-knife-plan.md)
sowie [Bedienung](drag-knife-usage.md) beschreiben Umfang und Materialprüfgrenze.
Der Schleppmesser verwendet inzwischen einen gemeinsamen Ablauf ohne
Freischalter. Konfiguration 9.18 und Projektformat 1.5 migrieren alte
Schwenktiefen; unterschiedliche Konturwerte bleiben bearbeitbar erhalten.
Lead-/Überfahrtdetails werden über den 2D-Konturbahnen gezeichnet. Für
Start-Einstellungen meldet die Konfiguration den erforderlichen Neustart und
führt ihn nach dem Schließen mit leerem Fenster aus; siehe
[Abschluss und Prüfgrenzen](archive/toolpath-refactoring-completed.md#configuration-restart).
Maschinentyp und Importtoleranzen wirken durch Neuladen unmittelbar; nur
2D/3D-Modus und Protokollierung benötigen diesen Konfigurationsneustart.
**K2 abgeschlossen, 02.11.2026:** Geladene Profilwerte und Werkseinstellungen
sind klar unterschieden; Hilfetexte verweisen auf die GitHub-Dokumentation.
[Umfang und Prüfungen](archive/toolpath-refactoring-completed.md#k2).
**Nächster Umsetzungsvorschlag: V1**, den Werkzeugkreis am Start unabhängig
vom Lead-in anzeigen; offene Bedienentscheidungen vorher abstimmen.

## 1. Exportablauf und Werkzeugwechsel

R2 betrifft das Umordnen innerhalb der bestehenden Ebenen und den Export
ohne/mit bewusst gewählter Optimierung. Dafür keinen Layerwechsel R1b
implementieren. P1 baut auf einem klaren Reihenfolge-/Werkzeugwechselvertrag
auf; der Nutzer hat LinuxCNC ohne automatischen Werkzeugwechsler als Ziel
festgelegt und die Prüfung auf der Maschine den Anwendern überlassen.

### R2 – Sichtbare Reihenfolge als Exportvertrag (abgeschlossen)

Abgeschlossen am **01.11.2026**; Umsetzung und lokale Prüfergebnisse stehen
im [Erledigt-Dokument](archive/toolpath-refactoring-completed.md#r2).

Manuelles Umordnen von Shapes im Treeview (Drag-and-drop oder Auf/Ab) legt
innerhalb desselben Layers die neue Bearbeitungsreihenfolge fest. Modell und
Exportlisten übernehmen sie auch ohne Routen-Live-Update; mit Live-Update zeigt
die Routenanzeige die neuen Verbindungen. Startpunkte, Geometrie, Werkzeuge und
Optimierungsfreigaben bleiben beim manuellen Umordnen erhalten. Speichern/Laden
und Export ohne Optimierung erhalten die sichtbare Reihenfolge einschließlich
benutzerdefiniertem G-Code.

**Nutzerentscheidung:** Bisherige Optimierungsmodi behalten; relative Reihenfolge
nicht freigegebener Shapes genügt. GUI und CLI wenden denselben Modus an.
P1 ist für den vereinbarten manuellen LinuxCNC-Ablauf softwareseitig geprüft.

### P1 – Z-Positionierung beim Werkzeugwechsel (softwareseitig abgeschlossen)

**Abgeschlossen für den vereinbarten Umfang, 02.11.2026:** Der Nutzer verwendet
LinuxCNC ohne ATC und hat den Abgleich mit Standard-G-Code sowie Softwaretests
beauftragt; die Maschinenprüfung übernehmen die Anwender. Der
[LinuxCNC-Abgleich samt ladbarem manuellem Profil](linuxcnc-manual-tool-change.md)
und zwei vollständige G90-/G91-Referenzausgaben sichern M6, G43, Rückzugshöhen,
Z vor XY und die inkrementelle Wiederaufnahme ab. Der bisherige Standard bleibt
bewusst ohne automatisch aktivierte Werkzeuglängenkorrektur. Siehe auch
[Erledigt-Dokument](archive/toolpath-refactoring-completed.md#p1-linuxcnc).

**Optionale Profilerweiterung implementiert, 01.11.2026:** Manueller Wechsel und
ATC verwenden weiterhin `Program.tool_change`. Neue Wechselparameter, ein
erklärter Rückkehrzustand, H-Zuordnungen und G91-Wiederaufnahme sind verfügbar;
alte Profile bleiben im Legacy-Verhalten. Einrichtung und Grenzen stehen in
der [Makro-Anleitung](tool-change-macros.md), die Herleitung im
[Werkzeugwechsel-Vorschlag](tool-change-proposal.md). 16 gezielte neue Tests
prüfen unter anderem zwei vollständige Ausgabesequenzen, A–B–A, tatsächlichen
Lead-Einstieg, Profilparameter, Fehlerbehandlung und geladene Übersetzungen.
Postprozessorversionen 8/8.1 bleiben lesbar; neues Schema ist 8.2.

**Abnahmegrenze:** Konkrete Controller-Version, HAL-/INI-Konfiguration,
Werkzeuglängen und freie Wechselwege prüft der jeweilige Anwender. Weder der
Standard-Abgleich noch die manuellen/ATC-Testprofile sind Maschinenfreigaben.
Verwalteter Export ist zunächst auf Fräsen ohne freie Custom-G-Code-Baumzeilen
begrenzt; die Legacy-Funktionen bleiben für diese Fälle erhalten. Die folgenden
Codebefunde beschreiben die Ausgangslage des Legacy-Exports.

**Meldung:** Ein ATC-Profil kann zunächst Z zur Werkzeugwechselposition
fahren, das Werkzeug wechseln und erst danach mit aktiver
Werkzeuglängenkorrektur die Arbeitshöhe anfahren. Das gemeldete Beispiel
verwendet `G91 G28 Z0`, `M06 T04`, die Rückkehr zu `G90` und später
`G43 Z1. H04`. Vorgeschlagen wurde, die einmalige Z-Rückzugsbewegung hinter
den Werkzeugwechsel zu verschieben oder dort zusätzlich auszugeben.

**Codebefund:** In
`adapters/postprocessor/postprocessor.py:exportShapes` wird
`rap_pos_z(Depth_Coordinates['axis3_retract'])` einmal vor der Layer-/Shape-
Schleife ausgegeben. Innerhalb der Schleife wird bei neuer effektiver
Werkzeugnummer `chg_tool` aufgerufen. Diese Methode expandiert nur das
Profiltemplate `Program.tool_change`; eine zusätzliche Z-Positionierung
direkt nach dem Wechsel gibt es dort nicht. Der erste exportierte
Shape-Eintrag löst aktuell ebenfalls `chg_tool` aus, weil `previous_tool`
anfangs `None` ist. Die Annahme „gleiche Werkzeugnummer, deshalb beim ersten
Shape kein Wechselaufruf“ trifft im aktuellen Code somit nicht zu.

Das Standardtemplate in `postprocessorconfig.py` enthält `T%tool_nr M6`
und die Drehzahl, aber keine allgemeine ATC-/Werkzeuglängensequenz.
Beliebige Profiltemplates können zudem Position und Modalzustand verändern,
ohne dass `chg_tool` die intern geführten Z-/G90-/G91-Werte nachführt.
Das ist bei einer Lösung insbesondere für inkrementellen Export zu beachten.

- [x] Reproduzierbare LinuxCNC-Exporte mit mindestens zwei Werkzeugen für
  G90/G91 erstellen und die vollständige Reihenfolge prüfen. Der vereinbarte
  Softwareumfang verwendet manuelles M6, G43 ohne H-Wort, vorbereitete
  Werkzeugtabellen und einen ausdrücklich konfigurierten Werkstückbezug.
  Konkrete Controller-Version und Maschinenparameter bleiben gemäß
  Nutzerentscheidung Teil der Anwenderprüfung.
- [x] Programmstart, Freifahren vor einem Werkzeugwechsel und Positionieren
  nach einem Werkzeugwechsel als getrennte Anforderungen beschreiben.
  Initiale Positionierung bleibt auch ohne weiteren Werkzeugwechsel oder
  bei leerem/manuellem Wechseltemplate sichergestellt; eine Zeile nicht
  ersatzlos in den Zweig „Werkzeugnummer geändert“ verschieben.
- [x] Eine profilabhängige ATC-Sequenz vorsehen: Wechselposition anfahren,
  Werkzeugwechsel, benötigten Modalzustand wiederherstellen und
  Werkzeuglängenkorrektur/Positionierung passend zum Controller ausgeben.
  `G28`, `G43` und eine Zuordnung `H = T` nicht ungeprüft für alle Maschinen
  fest einbauen. Die Lage der XY-Positionierung innerhalb dieser Sequenz
  ist Teil des zu vereinbarenden Maschinenprofilvertrags.
- [x] Festlegen, welche Höhe nach dem Wechsel gilt: globale initiale
  Rückzugshöhe, nächste Layer-/Shape-Rückzugshöhe oder eine besondere
  Profilvorgabe. Diese Höhen nicht mit Maschinen-Z-Home gleichsetzen.
- [x] Internen Positions-/Modalzustand nach Wechselmakros eindeutig neu
  herstellen oder über einen definierten Profilvertrag aktualisieren;
  keine falschen inkrementellen Z-Differenzen aus Werten vor dem Wechsel
  berechnen. Nicht versuchen, beliebigen Makro-G-Code allgemein zu parsen.
- [x] Werkzeugwechsel innerhalb eines Layers wegen Shape-Overrides ebenso
  behandeln wie Wechsel zwischen Layern. Wiederholte Shapes mit demselben
  Werkzeug dürfen keinen unbeabsichtigten erneuten ATC-Zyklus auslösen.
- [x] Exportorchestrierung und Profiladapter übernehmen diese Verantwortung;
  Geometrie-/Konturplaner erhalten keine hartcodierten ATC-Befehle.
  Vorhandene Profile bleiben kompatibel. Absichtliche neue ATC-Ausgaben
  gesondert freigeben; vorhandene Golden-Ausgaben nicht pauschal ändern.

**Abnahme und Tests:** Vollständige Exportsequenzen statt nur Aufrufanzahlen
prüfen: ein Werkzeug, mehrere Shapes mit gleichem Werkzeug, Wechsel A→B→A
innerhalb eines Layers und zwischen Layern, leere/deaktivierte Layer sowie
manuelles/leeres Wechseltemplate. Ein eigenes ATC-Testprofil und Golden
decken Wechselposition, Modalzustand, H-Zuordnung und erste Bewegung nach
dem Wechsel ab; absolute und inkrementelle Ausgabe berücksichtigen.
`dxf2gcode_shape_tool_test.py` prüft Werkzeugwechsel bereits auf Aufrufebene
und kann um die ausgegebene Reihenfolge ergänzt werden. Diese Prüfungen
bewerten erzeugten Code, nicht die Freigabe für eine reale Maschine.
Die optionale Makro-Erweiterung ist implementiert; alte Profile behalten ihre
Ausgabe. Ein direkter Vergleich mit dem vorherigen Stand bestätigt dies für
G90/G91 und normales/leeres Wechseltemplate in vier vollständigen Exporten.

## 2. Schleppmesser

D1 und D2 bilden den gemeinsam abgestimmten
[Schleppmesser-Ablauf](drag-knife-plan.md). Zunächst Rampen und Konturschluss
absichern, darauf Tiefenzustellungen und Wiederholung aufbauen. Dieser Umfang
ist lokal softwareseitig umgesetzt und gezielt geprüft. Bestätigt sind eine Option für genau einen zusätzlichen
Endtiefen-Durchgang und kontinuierliche Zustellungen geschlossener Konturen
ohne Zwischenrückzug; externe Ausrichtung und Lead-in erfolgen dort nur beim
ersten Einstieg. Bedienung und Kompatibilität stehen in der
[Schleppmesser-Anleitung](drag-knife-usage.md). Messerstellung und optionale
Rückausrichtung sind auswählbar, einschließlich unbekannter Stellung nach
dem Abheben mit einer am Material zu prüfenden externen Ausrichtstrecke.

### D1 – Rampen und Konturschluss (softwareseitig abgeschlossen)

**Forumsbericht:** Im gezeigten Thread
[Overcut with drag knife / vinyl cutter](https://www.ltspiceusers.ch/threads/overcut-with-drag-knife-vinyl-cutter.2247/)
beschreibt Randy am 16. und 27. Juni 2026 kleine ungeschnittene Stellen beim
Konturschluss. Besonders bei Schrift lassen sich dadurch Abfallbereiche nur
schwer entfernen, ohne Buchstaben abzulösen. Als Ursache vermutet er den
Versatz der Messerspitze; genannt werden etwa 0,25 mm. Das ist eine
Nutzervermutung, noch kein nachgewiesener Fehler im aktuellen Stand.

**Legacy-Ausgangslage:** Eine Überfahrt für geschlossene Schleppmesserkonturen ist
bereits vorhanden: `domain/toolpath/stmove.py` hängt `build_overcut`-Geometrie
an die Originalkontur an, bevor der Spitzenversatz verarbeitet wird.
`dxf2gcode_leadmove_golden_test.py` enthält `drag_knife_overcut`, ein
Funktionstest prüft zusätzlich den erfolgreichen Export. Diese Tests belegen
noch nicht, dass die physische Messerspitze am Konturschluss die gemeldete
Lücke in allen Fällen überfährt. Der ältere Forumsbericht ist mit dem
aktuellen Code und den wirksamen Einstellungen abzugleichen.

- [x] Reproduktion mit einer kleinen geschlossenen Schrift-/Testkontur,
  Werkzeugversatz, Startausrichtung, Überfahrt und Schneidtiefe festhalten.
  Werkzeughalterbahn und tatsächliche Messerspitzenbahn unterscheiden.
- [x] Vorhandene `dxf/drag_knive_test.dxf` aus dem
  [Forumsfall von 2022](https://www.ltspiceusers.ch/threads/dragknife-issue.1126/)
  als Regression für den abschließenden Messerschwenk und dessen
  Z-/Vorschubreihenfolge einbeziehen. Zuordnung über Commit `0178408` und
  Prüfziele stehen im [gemeinsamen Plan](drag-knife-plan.md#vorhandene-forums-testdatei-abschließender-messerschwenk).
- [x] Konturschluss mit aktivierter und deaktivierter Überfahrt prüfen;
  Startorientierung, Richtung, erste kurze Linie beziehungsweise Bogen und
  Übergang vom letzten zum ersten Segment einbeziehen. Eine Mindestlänge
  größer als der Spitzenversatz nicht ungeprüft als allgemeine Lösung setzen.
- [x] Bestehende Überfahrt bei Bedarf gezielt korrigieren. Ein neues
  Wiederholungsmerkmal aus D2 darf einen Fehler des Konturschlusses nicht
  lediglich verdecken. Keine pauschale Änderung anderer Maschinenmodi.

**Abnahme und Tests:** Spitzenbahn am Anfang und Ende sowie tatsächlich
abgedeckte Schnittstrecke geometrisch prüfen, nicht nur nicht leeren G-Code.
Geschlossene Linien-/Bogenkonturen, kurze Anfangssegmente und beide
Umlaufrichtungen testen; bestehende Schleppmesser-Goldens vergleichen.
Praktische Schnittqualität erfordert danach einen gesonderten Materialtest;
ein solcher ist mit diesem TODO nicht durchgeführt oder freigegeben.

### D2 – Mehrere Schnitttiefen und Endtiefen-Durchgang (softwareseitig abgeschlossen)

**Abgestimmter Umfang, 02.11.2026:** Offene und geschlossene Konturen über
mehrere Schnitte auf Endtiefe bringen. Vorhandene Endtiefe und Slice depth
als Endtiefe und maximale Zustellung wiederverwenden; Schwenktiefe davon
trennen. Eine Ein-/Aus-Option erlaubt genau einen zusätzlichen vollständigen
Durchgang auf Endtiefe. Die vorhandenen Eckenschleifen und
Spitzenversatzkorrekturen bleiben erhalten. Einzelheiten einschließlich
Einstieg, Lead-Auswahl, Ausrichtung und offener Umkehr stehen im
[gemeinsamen Plan](drag-knife-plan.md).

**Legacy-Ausgangslage:** `DragKnifeStrategy` in
`domain/toolpath/strategies/drag_knife.py` verarbeitet die vorbereitete Bahn
einmal und hängt danach den Rückzug an. Eine eigene Einstellung für mehrere
zusammenhängende Umläufe ist dort nicht vorhanden. `slice_depth` dient im
Schleppmessermodus bereits als Schwenktiefe an Ecken. Im neuen Ablauf wird er
zur Zustellung; bestehende Profile benötigen eine ausdrückliche Übernahme
des bisherigen Verhaltens statt einer stillen Bedeutungsänderung.

- [x] Modus festgelegt: Tiefenzustellungen über Slice depth und optional genau
  ein zusätzlicher vollständiger Endtiefen-Durchgang; keine freie Umlaufanzahl.
- [x] Den Übergang zwischen den Umläufen kontinuierlich planen, einschließlich
  Messerorientierung und Eckenkorrektur an der Schließstelle. Anfahrt,
  anfängliche Rampe und abschließenden Rückzug nicht einfach mitduplizieren.
- [x] Geschlossene Übergänge festgelegt: weitere Zustellungen auf der Kontur,
  ohne Zwischenrückzug. Eckenschwenks mit Entlastung bleiben davon getrennt;
  externe Ausrichtung und Lead-in nur beim ersten Einstieg.
- [x] Den abgestimmten Rampenausgleich und die abschließende Nahtüberlappung
  aus D1 mit den Tiefenfolgen und dem zusätzlichen Durchgang verbinden.
  Offene Konturen mit gleicher/wechselnder Richtung und Umkehr/Zustellung
  im externen Lead-Bereich berücksichtigen. Jeder Sollkonturabschnitt wird
  mindestens einmal auf Endtiefe bearbeitet.
- [x] Einstellung, Projektpersistenz und GUI-Anzeige gemeinsam planen;
  neue Texte in Deutsch, Französisch und Russisch pflegen. Wiederholungen
  als semantischen Ablauf planen, damit Vorschau und Export denselben Plan
  verwenden. Keine bloße Verdoppelung des fertigen G-Code-Texts.

**Abnahme und Tests:** Anzahl und Tiefe der Umläufe, korrekten Nahtübergang,
fehlenden Zwischenrückzug bei geschlossenen Umläufen, erhaltene Eckenschleifen
und geplante Rückkehr-/Umkehrabläufe offener Konturen prüfen. G-Code und 3D-Projektion verwenden
dieselben Z-Bewegungen; 2D darf deckungsgleiche XY-Bahnen weiterhin einmal
darstellen. Unveränderten Ein-Umlauf-Modus sowie Roundtrip der neuen Option
absichern. D1/D2 sind lokal implementiert: je 44 fokussierte Tests unter Qt5
und Qt6 bestanden. Die praktische Schnittqualität bleibt am Material zu prüfen.

## 3. Konfiguration und Bedienung

K1 und K2 sind abgeschlossen. V1, U3 und U5 sind anschließend
unabhängig auswählbare Erweiterungen; ihre offenen Bedienentscheidungen
bleiben jeweils vor der Umsetzung zu klären.

### K1 – Übersetzung des Konfigurationsfensters (abgeschlossen)

Abgeschlossen am **02.11.2026**: extrahierbare MyConfig-/MyPostProConfig-Texte,
80 extrahierbare Hilfetexte im Kontext ConfigurationHelp, übersetzte
Auswahlanzeigen bei unveränderten Speicherwerten, korrigierte Maschinenmenüs
und neu kompilierte DE-/FR-/RU-Kataloge. Qt5 und Qt6 prüfen echte Dialoge,
Menüaktionen und einen erneuten Extraktionslauf einschließlich UI-Datei.
Einrichtung und Abnahme stehen im
[Erledigt-Dokument](archive/toolpath-refactoring-completed.md#k1).
Die folgenden Codebefunde beschreiben die behobene Ausgangslage.

**Behobene Ausgangslage:** `presentation/qt/configuration_widgets.py` verwendet
`config.tr`; `adapters/config/runtime_config.py:MyConfig.tr` fragt den
Qt-Kontext `MyConfig` ab. Die untersuchten Beschriftungen standen in allen
drei TS-Katalogen unter `@default` als `unfinished`; ihre alten Einträge unter
`MyConfig` waren `obsolete`. Dieser Kontextbruch verursachte den englischen
Rückfall. Die korrigierten Dialoge sind mit geladenen QM-Dateien geprüft.

**Ebenfalls behoben:** Im Menü „Maschinen Typ“ war
`&Lathe` im deutschen `MainWindow`-Katalog fälschlich als `&Hilfe` übersetzt.
Gemeint ist „Drehmaschine“. Die Aktion ist in `application.py` korrekt mit
`setMachineTypeToLathe` verbunden und setzt `machine_type='lathe'`; der
Menütext war falsch, nicht die Zuordnung der Aktion. Der Eintrag ist
korrigiert; die Maschinenbezeichnungen und Aktionen aller drei Sprachen sind
geprüft.

- [x] Einen eindeutigen Übersetzungskontext für die ausgelagerten
  Widget-Definitionen festlegen und die Extraktion darauf abstimmen, damit
  spätere Übersetzungsläufe den Fehler nicht erneut erzeugen.
- [x] Anwendungs- und Postprozessorkonfiguration einschließlich Überschriften,
  Hilfetexten und Auswahleinträgen prüfen. Technische Profil-/Dateischlüssel
  bleiben unabhängig von übersetzten Anzeigenamen stabil.
- [x] Deutsch, Französisch und Russisch gemeinsam aktualisieren, QM-Dateien
  neu erzeugen und den geöffneten Dialog mit diesen Dateien prüfen.

**Abnahme und Tests:** Kontext-/Katalogprüfung und fokussierter Qt-Test, der
einen echten Translator lädt und repräsentative Labels im aufgebauten Dialog
prüft. Auch nach erneutem Extrahieren/Kompilieren müssen diese Labels
übersetzt bleiben. Bestehende Nutzereinstellungen werden dabei nicht verändert.
Zusätzlich die drei Maschinentypen im übersetzten Menü prüfen: „Fräsen“,
„Drehmaschine“ und „Schleppmesser/Drag Knife“ müssen auf die zugehörigen
internen Werte zeigen; der Hilfemenütext darf nicht als Maschinentyp erscheinen.

### K2 – „default“ gegenüber tatsächlichen Vorgabewerten klären (abgeschlossen)

Abgeschlossen am **02.11.2026**; [Prüfnachweis](archive/toolpath-refactoring-completed.md#k2).
Der pauschale Zusatz „(default)“ ist entfernt. Tooltips nennen die tatsächliche
Werkseinstellung aus `CONFIG_SPEC`, während die Felder den geladenen Profilwert
anzeigen. Die fachlichen Vorgaben bleiben unverändert:

| Einstellung | Derzeitige Vorgabe für ein neues Profil |
| --- | --- |
| Deaktivierte Pfade anzeigen | `True` |
| Exportroute live aktualisieren | `False` |
| Liniensegmente teilen | `False` |
| Automatische Fräsradienkompensation | `False` |
| Maschinentyp | `milling` |

`MainWindow.initializeConfigProfile` erzeugt ein neues Profil über die
Konfigurationsklassen mit deren Vorgaben; es kopiert absichtlich nicht das
aktuelle Profil. Die Prüfung isolierter Profile bestätigt dieses Verhalten;
ein zusätzlicher Fehler beim Anlegen oder Laden wurde nicht festgestellt.

- [x] Schema, frisch erzeugte Datei, geladene Werte, Checkboxanzeige und
  Wirkung beim Programmstart je betroffener Option vergleichen.
- [x] Den Unterschied zwischen Werkseinstellung, gespeichertem Profilwert
  und Vorgabe für neue/importierte Shapes verständlich benennen.
  Der pauschale Zusatz ist entfernt; Tooltips nennen „Vorgabe für neue Profile“.
- [x] Fachliche Standardwerte und bestehende Profile unverändert lassen.
  Künftige Änderungen der Vorgaben weiterhin einzeln abstimmen.

**Abnahme und Tests:** Je 13 fokussierte Tests unter Qt5 und Qt6 bestanden:
neue Profile, Speichern/Laden, Startaktionen, Dialogwerte und Vorgaben für neue
Konturen. Individuelle Werte bleiben erhalten. DE/FR/RU sind gepflegt,
kompiliert und mit echten Translatoren geprüft.

### V1 – Werkzeugkreis am Start unabhängig vom Lead-in anzeigen

**Codebefund:** `StMoveGUI` in `canvas2d.py` zeichnet den Kreis nur innerhalb
der Prüfung auf einen nicht leeren Lead-in-Pfad.
`_lead_in_dive_point` und `boundingRect` haben ebenfalls diese Bindung.
Eine eigene Konfigurationsoption für die Sichtbarkeit fehlt.

- [ ] Den Werkzeugdurchmesser auch ohne Lead-in am zugehörigen Startpunkt
  darstellen; Zeichnen und Bounding-Box gemeinsam von der Lead-Auswahl lösen.
- [ ] Eine persistierte Anzeigeoption mit verständlichem Text in allen drei
  Sprachen ergänzen. **Vorschlag zur Freigabe:** standardmäßig eingeschaltet;
  Ausschalten verbirgt nur den Werkzeugkreis, nicht Leads oder Werkzeugbahnen.
- [ ] Vor Umsetzung den Bezugspunkt eindeutig vereinbaren. **Vorschlag:**
  tatsächlicher Werkzeugmittelpunkt am Einstieg des geplanten Schnitts;
  mit Lead-in dessen vorhandener Eintauchpunkt, ohne Lead-in der entsprechende
  Bahnanfang. Bei Softwarekompensation den kompensierten Punkt verwenden;
  bei Maschinenkompensation eine nur angenäherte Darstellung gegebenenfalls
  kenntlich machen. Kein zweiter Offset-/Lead-Algorithmus in der Ansicht.
- [ ] Effektive Shape-Werkzeuge, Transformationen, Zoom und mehrere
  Teilkonturen aus der zurückgestellten Erweiterung berücksichtigen.
  Zunächst betrifft der Befund 2D; den gewünschten Umfang in 3D vor Umsetzung
  festlegen und mit dem [abgeschlossenen Vorschauvertrag](archive/toolpath-refactoring-completed.md#5-vorschau-und-gemeinsame-planquelle-abschließen) abstimmen.

**Abnahme und Tests:** Anzeige an/aus mit Lead-in an/aus, G40/G41/G42,
Shape-Werkzeugoverride und transformierter Geometrie prüfen. Mittelpunkt,
Radius und Bounding-Box gezielt testen; die Anzeigeoption darf den Plan oder
G-Code nicht verändern. Bestehende Startpunkt-/Lead- und Vorschautests ergänzen.

### U3 – Nullpunkt über einen Punkt im Kontextmenü festlegen

**Gewünschter Ablauf:** An der gewünschten Position in der Zeichnungsansicht
das Kontextmenü öffnen und „Nullpunkt hierher verschieben …“ wählen.
Anschließend öffnet sich der bestehende Eingabedialog aus dem Menü mit den
aus diesem Punkt berechneten Verschiebungswerten. Diese lassen sich vor dem
Übernehmen bearbeiten oder unverändert bestätigen.

**Codebefund:** `MainWindow.moveWorkpieceZero` in
`presentation/qt/application.py` öffnet bereits den Dialog für die beiden
Achsenwerte (`cont_dx`, `cont_dy`) und übernimmt die Verschiebung nach
Bestätigung. `MyDropDownMenu` in `canvas.py` erhält die angeklickte Position
bereits als `clicked`. Diese Eingänge sollten denselben Anwendungsablauf
verwenden, statt eine zweite Nullpunktberechnung in der GUI einzuführen.

- [ ] Den Kontextmenüeintrag ergänzen und den beim Öffnen gewählten Punkt
  als Ausgangspunkt verwenden. Die berechneten Werte im bestehenden Dialog
  vorbelegen; sie bleiben editierbar. Der normale Menüaufruf für die rein
  numerische Eingabe bleibt erhalten.
- [ ] Erst beim Bestätigen die Verschiebung anwenden. Abbrechen verändert
  weder Nullpunkt noch Geometrie, Projektzustand oder Werkzeugweg.
- [ ] Klickkoordinaten korrekt in die vorhandene Nullpunktverschiebung
  umrechnen: aktuelle Verschiebung, Transformationen, Bildschirm-Y-Richtung
  und aktive Einheit berücksichtigen. Bei unveränderter Bestätigung soll der
  gewählte Zeichnungspunkt im resultierenden System bei X=0/Y=0 liegen.
- [ ] Vorschau, Plan und Export gemeinsam aktualisieren; die bestätigten
  Werte müssen beim erneuten Öffnen des numerischen Dialogs erscheinen und
  über die bestehende Projektpersistenz erhalten bleiben.
- [ ] **Begriff vor Umsetzung abstimmen:** Die vorhandene Funktion verschiebt
  den Werkstück-/Zeichnungsnullpunkt. Der vom Nutzer genannte
  „Maschinennullpunkt“ darf nicht versehentlich als Änderung des physischen
  Maschinenreferenzpunkts oder als neuer Steuerungsbefehl umgesetzt werden.
  Ein optionales Fangen auf Geometriepunkte ist gesondert festzulegen; eine
  zusätzliche Fangfunktion ist mit diesem TODO noch nicht beschlossen.
- [ ] Neue Menü-/Hilfetexte gemeinsam in Deutsch, Französisch und Russisch
  pflegen.

**Abnahme und Tests:** Klickpunkt → vorbelegter Dialog → Bestätigen sowie
Bearbeiten und Abbrechen gezielt testen. Bestehenden numerischen Menüweg,
wiederholtes Setzen ohne Verschiebungsdrift, bereits verschobene/transformierte
Zeichnungen, mm/in und Projekt-Roundtrip einbeziehen. Vorschau und exportierte
Koordinaten müssen dieselbe bestätigte Verschiebung verwenden. Die Umsetzung
bleibt bis zur Auswahl dieses Punkts zurückgestellt.

### U5 – Ticket #157: Tastenkürzel zum Ein-/Ausklappen

- [ ] Tastenkürzel für die Layer-Klappaktionen vorsehen. Vor Umsetzung
  festlegen, ob der gesamte Baum oder die ausgewählte Gruppe gemeint ist
  und ob dieselbe Bedienung auch für Entities gelten soll.
- [ ] Mit vorhandenen Baum-/Canvas-Tasten und deren Fokusregeln abstimmen;
  dieselben Aktionen und Verfügbarkeitsregeln wie die U2-Buttons verwenden.

**Abnahme und Tests:** Echte Tastenevents im aktiven Baum prüfen, einschließlich
leerem, vollständig ein-/ausgeklapptem und gemischtem Baum. Keine Auslösung
bei Texteingabe oder unbeabsichtigte Änderung des Canvas-Zooms.

## 4. Paketabnahme und Abnahmegrenzen

### CI1 – Automatische Builds und Downloads auf GitHub

**Vereinbarter Zielablauf, 01.11.2026:** Fertige Downloads als GitHub-Release-
Assets ablegen, nicht in der Git-Historie. Temporäre Testpakete gehören zu
Actions-Artefakten. Als offene Umsetzung vorgemerkt; diese Todo-Ergänzung
startet keine Builds, Veröffentlichungen oder Löschungen.

| Anlass | Prüfungen und Builds | Bereitstellung |
| --- | --- | --- |
| Lokaler Commit | Fast-Suite über den Pre-Commit-Hook | Keine Veröffentlichung |
| Pull Request nach `develop` | Vollsuite und Paketprüfungen; Wheel und Windows-Pakete bauen | Temporäre Actions-Artefakte für 7 Tage; kein öffentliches Release aus dem PR |
| Push auf `develop` | Vollsuite und Paketprüfungen desselben Commits | Bei Erfolg automatisch ein ausdrücklich gekennzeichnetes Develop-Prerelease |
| Bewusst gesetzter Release-Tag | Vollsuite und Paketprüfungen | Reguläres Release mit dauerhaft aufbewahrten Downloads |

- [ ] Als erste Downloadformate ein entpackbares Windows-x64-ZIP mit EXE und
  allen benötigten Laufzeitdateien, einen MSI-Installer sowie ein Wheel
  vorsehen. Windows-Pakete zunächst mit einer festgelegten Python-/Qt-
  Kombination bauen; die breitere Testmatrix beibehalten. Ein zusätzlicher
  EXE-Installer oder eine einzelne eigenständige EXE bleibt optional.
- [ ] Builds und Tests eindeutig demselben Commit zuordnen. Öffentliche
  Develop-Downloads erst nach erfolgreichen Tests und Paketprüfungen
  aktualisieren. Bei Fehlern bleibt der letzte erfolgreich geprüfte Download
  verfügbar. Veröffentlichungsrechte auf den dafür vorgesehenen Ablauf für
  übernommene Develop-Stände beziehungsweise Release-Tags begrenzen.
- [ ] Eindeutige Entwicklungsversionsnummern und Dateinamen mit Datum und
  Commitkennung verwenden. Paketversion, eingebettete Herkunft, Infofenster
  und Downloadbezeichnung müssen zusammenpassen. MSI-konforme Versionierung
  einschließlich Unterscheidung mehrerer Builds am selben Tag festlegen;
  die bisherige Ableitung `2026.10.30` ist wegen des zu großen ersten
  MSI-Versionsfelds anzupassen.
- [ ] Die fertigen Artefakte prüfen: Wheel in einer frischen Umgebung
  installieren und mit `tests/verify_wheel.py` kontrollieren; Windows-Paket
  auf Vollständigkeit, Programmstart und einen kleinen DXF-Export prüfen.
  Generierte Qt-Dateien und alle gepflegten Übersetzungen mitliefern.
- [ ] Unter GitHub Releases klar unterscheidbare Develop-Prereleases und
  stabile Releases anbieten. Das stabile Release nicht durch einen
  Entwicklungsstand als reguläres „Latest“-Release ersetzen. Downloads im
  README verlinken und SHA-256-Prüfsummen mitliefern.
- [ ] Aufbewahrung automatisieren: PR-/Actions-Testpakete nach **7 Tagen**
  entfernen und nur die letzten **10 erfolgreich veröffentlichten Develop-
  Stände** behalten. Alte Develop-Prereleases samt zugehörigen Assets gezielt
  bereinigen; stabile Releases und deren Downloads dauerhaft erhalten.
  Tag-Bereinigung gesondert auf die eigenen Develop-Tags begrenzen.
- [ ] Speicherbelegung und tatsächlichen GitHub-Tarif vor Aktivierung prüfen.
  Release-Assets, temporäre Actions-Artefakte und Caches getrennt behandeln;
  kurzlebige CI-Kopien nicht unnötig zusätzlich zu den Releases aufbewahren.
  Eine Codesignierung für öffentlich verteilte Windows-Pakete einplanen.

**Abnahme:** Den Ablauf mit einem PR-Testpaket, einem erfolgreichen und einem
fehlgeschlagenen Develop-Build sowie einem regulären Release nachvollziehen.
Dateinamen, Commitbezug, Installierbarkeit und Downloads prüfen. Die
Aufbewahrungslogik zunächst mit kontrollierten Testdaten beziehungsweise
Vorschau der Löschkandidaten prüfen: Die letzten zehn Develop-Stände und alle
stabilen Releases müssen erhalten bleiben. M1 bleibt die gesonderte
Paket-/Debian-Abnahme; die Existenz eines erfolgreichen CI-Builds ersetzt sie
nicht automatisch.

<a id="m1"></a>

### M1 – Noch offene Paket-/Debian-Abnahme

- [ ] Nach gesonderter Freigabe ein aktuelles Wheel/Quellarchiv und die
  Windows-Artefakte bauen und ihre mitgelieferten Metadaten prüfen.
- [ ] Wheel aus dem Quellarchiv ohne Git bauen; Herkunft und Zeitstempel
  müssen aus dem Archiv stammen. Installierte Anwendung ohne Git starten.
- [ ] Das freigegebene Wheel im isolierten Debian-Testworkflow prüfen:
  Infofenster zeigt die Paketversion und Build-Herkunft des tatsächlich
  installierten Artefakts, nicht einen vorherigen Quellstand oder den
  lokalen Branch der VM. Ergebnisse einschließlich Paketidentität festhalten.
- [ ] Paket-/Quellstart und G-Code-Kopf gegen dieselbe Herkunft abgleichen;
  Bewegungsausgabe bleibt gegenüber den bestehenden Golden-Fällen erhalten.

**Freigabegrenze:** M1 ist vorgemerkt, nicht mit der Dokumentbereinigung
beauftragt. Vollständige Release-/MSI-Builds, Debian-/SSH-Läufe und Änderungen
an installierten Testumgebungen erfolgen erst auf ausdrücklichen Auftrag
oder nach angenommenem konkretem Vorschlag.

Der dokumentierte Debian-Lauf mit 775 Tests prüfte einen Quell-/Testsnapshot
in einer isolierten Umgebung, kein neu gebautes und installiertes Release-
Artefakt. Er schließt M1 deshalb nicht ab. Die spätere Darstellungskorrektur
wurde gezielt mit je 21 Tests unter Qt5/Qt6 geprüft. Keine erneuten langen
Läufe allein wegen dieser Dokumentbereinigung starten.

### A1 – Verbleibende Grenzen der Architekturabnahme klären

Die früheren allgemeinen Abnahmetore sind im
[Erledigt-Dokument eingeordnet](archive/toolpath-refactoring-completed.md#einordnung-der-früheren-abnahmetore).
Bereits nachgewiesene Kriterien sind keine neue Implementierungsserie.

- [ ] Über die gezielten B1/B2-Nachweise hinaus weitere relevante Maschinen-,
  Kompensations- und Profilfälle nur bei einer benannten Abdeckungslücke
  festlegen; aus der früher pauschalen Matrix keine neue Vollprüfung ableiten.
- [ ] Die Reichweite des früher pauschal auf „Domain und Application“
  bezogenen Import-Abnahmetors klären. Importfreiheit ist für alle Module
  unter `domain/geometry` und `domain/toolpath` nachgewiesen, nicht für alle
  übrigen Projektmodelle oder die GUI-/Datei-Exportfassade. Eine darüber
  hinausgehende Entkopplung wäre gesondert zu beschließen und zu planen.

## 5. Zurückgestelltes Bedienmodell und Teilkonturen

Diese Themen bleiben zurückgestellt. Weder die abgeschlossenen
Refactoring-Etappen noch die Neuordnung dieser Liste geben ihre Umsetzung
frei. Zuerst R3 und R1b gemeinsam entwerfen; das Datenmodell der
Teilkontur-Erweiterung dabei berücksichtigen und anschließend abstimmen.

<a id="r3"></a>

### R3 – Geometrie und Bearbeitung im Bedienmodell trennen

**Umfang für die spätere Planung:** Den zurückgestellten Layerwechsel R1b
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

- [ ] Einen Tab „Geometrie“ für Herkunft, Sichtbarkeit und Auswahl sowie einen
  Tab „Bearbeitung“ für geordnete Gruppen/Operationen entwerfen. Die Auswahl
  in Baum und Vorschau bleibt gekoppelt. Die ursprüngliche DXF-Zuordnung
  bleibt als Herkunft erhalten, auch wenn Arbeitsgänge umsortiert werden.
- [ ] Bearbeitungsgruppen anlegen/benennen, Werkzeug und Vorgaben zuweisen,
  Operationen per Drag-and-drop umsortieren oder in andere Gruppen verschieben.
  Zusätzliche Aktionen „Nach oben/unten“ und „In Gruppe verschieben …“ machen
  die Planung auch ohne präzises Ziehen bedienbar.
- [ ] Dieselbe Originalkontur über explizit angelegte Referenzen später in
  mehreren Arbeitsgängen nutzen können, etwa Tasche und anschließendes
  Schlichten. B1 gilt je Operation; zwei getrennte Operationen dürfen dieselbe
  Geometrie unterschiedlich bearbeiten. Verschieben und bewusstes Erzeugen
  einer weiteren Operation müssen in der Bedienung unterscheidbar sein.
- [ ] Jede Operation besitzt eine stabile Identität und klare effektive
  Werkzeug-/Bearbeitungswerte. Entstehende Teilkonturen können später eigene
  Startpunkte und Leads erhalten, wie in der Teilkontur-Erweiterung beschrieben;
  Tiefenpässe sind keine separat zu sortierenden Geometrieobjekte.
- [ ] Reihenfolge und Optimierungsfreigabe im Bearbeitungsbaum sichtbar halten.
  Optimierung erfolgt innerhalb ausdrücklich freigegebener Grenzen und
  verändert niemals die fachlich geplante Gruppenreihenfolge.
- [ ] Projektpersistenz und Übernahme bestehender Layerprojekte gesondert
  planen. **Offene Entscheidung:** zunächst eine Bearbeitungsgruppe je
  bestehendem Layer als verlustfreie Ausgangssicht? Speicherformat und
  Kompatibilitätsweg vor Implementierung klären.

**Weiteres Vorgehen:** R1a sichert den bestehenden Baum ab. R2 hat den
Reihenfolgevertrag unabhängig vom Layerwechsel abgesichert. R1b wird erst
gemeinsam mit R3 anhand von Bedienabläufen und einem Modell-/Speicherentwurf
geplant und zur Freigabe vorgelegt. R1b und R3 bleiben ebenso wie die
Teilkontur-Erweiterung zunächst zurückgestellt.

<a id="r1b"></a>

### R1b – Layerwechsel gemeinsam mit R3

**Zurückgestellt durch Nutzerfestlegung:** Aktuell keine Shapes in einen
anderen Layer verschieben. Diese Erweiterung später gemeinsam mit dem
Bedienkonzept R3 planen; sie ist keine Voraussetzung für R2.

Ein rein optisches Umhängen im Baum reicht nicht: Mitgliedschaft in
`real_layer.shapes`, `parentLayer`, Exportreihenfolge und die beim
Projekt-Neuimport wiederhergestellte Zuordnung müssen zusammenpassen.

- [ ] Gültige Shapes in einen anderen Bearbeitungslayer verschieben;
  das bestehende Umordnen von Layern und Shapes innerhalb ihrer Ebene
  erhalten. Auswahl mehrerer Shapes und eindeutige Drop-Markierung
  beim Umhängen beziehungsweise Einfügen berücksichtigen.
- [ ] Einen Anwendungsfall für die atomare Änderung von Quell-/Ziellisten,
  `parentLayer`, Reihenfolge und Planinvalidierung verwenden. Baum, Modell,
  Vorschau und Export anschließend aus demselben Zustand aktualisieren;
  Identität und Gesamtzahl der Shapes erhalten.
- [ ] **Vor R1b abstimmen:** Beim Verschieben explizite Shape-Werte behalten
  und geerbte Werte aus dem Ziel übernehmen? Das ist der Vorschlag für
  Werkzeug, Tiefe und Leads; die wirksamen Änderungen müssen erkennbar sein.
  Sonderlayer, Breaks und benutzerdefinierter G-Code benötigen klare Regeln.
- [ ] Speichern/Laden nach dem Verschieben prüfen. Ein notwendiger Ausbau
  der Projektzuordnung ist als eigener Kompatibilitätsschritt zu planen;
  bestehende `.d2g`-Versionen 1.1–1.3 bleiben lesbar. Keine unbemerkte
  Formatänderung als Nebenwirkung des GUI-Fixes.

**Abnahme bei späterer Umsetzung:** Quell-/Ziellayer, Hin-/Zurückverschieben,
Mehrfachauswahl, Reihenfolge, unveränderte Identitäten und Overrides sowie
Projekt-Roundtrip und tatsächlichen Export der neuen Zuordnung prüfen.
Die Absturzabsicherung R1a ist bereits abgeschlossen und dokumentiert im
[Erledigt-Dokument](archive/toolpath-refactoring-completed.md#r1a).


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

## 6. Optionale zusätzliche Qt-Bindung

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

## Arbeits- und Prüfregeln

Arbeiten in kleinen, reviewbaren Scheiben ausführen. Für jede Scheibe zuerst
die bisherigen Ergebnisse durch Tests festhalten, dann Planung und Ausgabe
umstellen und erst nach bestandenem Abnahmetor mit der nächsten Scheibe
beginnen. Absichtliche Änderungen am G-Code-Verhalten benötigen eine eigene
fachliche Begründung und dürfen nicht als Nebeneffekt der Strukturmigration
einfließen.

Geometrieausgabe und Geometriealgorithmen nicht gleichzeitig ändern, wenn
sich ihre Effekte nicht getrennt validieren lassen. Bestehende G-Code-Ausgabe
bleibt Verhaltensvertrag, bis eine Änderung ausdrücklich beschlossen ist.
Keine großflächigen Umbenennungen/Verzeichnisverschiebungen als ersten Schritt
einer fachlichen Scheibe; entfernte alte Importpfade nicht wieder einführen.
Die lokalen Prüfungen ersetzen nicht die abschließende Gesamtprüfung. Lange
Prüfungen werden nach der Freigaberegel der Teststrategie eingeplant.

### Prüfstrategie

Die Beschränkung umfangreicher Prüfläufe betrifft die lokale Arbeit von Codex.
Auf GitHub läuft die Vollsuite automatisch bei Push auf `develop` und Pull
Requests nach `develop`; ein manueller Start bleibt möglich. Vor jedem lokalen
Commit führt der Pre-Commit-Hook die Fast-Suite aus. Dieser verpflichtende Lauf
ersetzt keine gezielten Tests während der Bearbeitung und muss nach bestandenem
Hook nicht zusätzlich manuell wiederholt werden.

Bei der jeweils beauftragten Umsetzung nur die passenden Prüfungen
festlegen. Die oben genannten Fälle sind Anforderungen an diese spätere
Umsetzung und kein Auftrag, jetzt Tests auszuführen.

- Reproduzierbare Abstürze, ungültige Bearbeitungszustände, falsche
  Zuordnungen und Export-/Speicherfehler erhalten automatische Regressionen.
  Der Test soll das beobachtbare Verhalten prüfen und vor dem Fix den Fehler
  nachweisen. Fachregeln möglichst ohne Qt testen; Signal-/Modellzusammenspiel
  zusätzlich mit wenigen fokussierten Qt-Workflows absichern.
- Vorhandene Tests erweitern, wenn sie denselben Vertrag abdecken. Ein neuer
  Test ist sinnvoll, wenn eine bislang ungesicherte Regel oder Fehlerursache
  geprüft wird; reine Wiederholungen der Implementierung vermeiden.
- Neue Konfigurationsoptionen über Vorgaben, Persistenz und Wirkung testen;
  Übersetzungen mit tatsächlichem Kontext und geladenem Katalog prüfen.
- Kleine Layoutänderungen primär gezielt visuell prüfen. Keine fragilen
  Pixeltests nur für Abstände; Zustandslogik wie bei den Baum-Buttons ist
  dagegen sinnvoll automatisch prüfbar.
- Bei Exportänderungen Planinhalt, Reihenfolge und relevante Golden-Ausgaben
  vergleichen. Tests verringern das Wiederholungsrisiko; sie garantieren nicht
  die Abwesenheit aller denkbaren Fehler oder Plattformunterschiede.
- Zunächst schnelle lokale Prüfungen des freigegebenen Teilbereichs.
  Vollständige Suite, Debian-/SSH-Läufe und Release-/MSI-Builds nur auf
  ausdrücklichen Auftrag oder nach angenommenem konkretem Vorschlag.

### Vor jeder Umsetzung

Nur den gewählten, überschaubaren Teilbereich bearbeiten. Offene fachliche
Entscheidungen vorher klären. Vorhandene Tests verwenden und nur echte
Verhaltenslücken ergänzen. Nach bestandenen passenden Prüfungen keine
weiteren Abschlussrunden ohne konkreten Anlass anhängen. Frühere Freigaben
für Vollsuite, Debian oder Builds gelten nicht als dauerhafte Freigabe.
Bei GUI-Textänderungen alle gepflegten TS-Kataloge (Deutsch, Französisch,
Russisch) im selben Schritt aktualisieren, die zugehörigen QM-Dateien
erzeugen und die geänderten Übersetzungen prüfen. Kein Commit ohne Auftrag.

## DOC1 – Zensical-Dokumentation und GitHub Development Preview

**Aktualisiert am 02.11.2026.** Historischer Übergabebericht mit lokalen und GitHub-
Prüfergebnissen, Commitbezügen und Wiederaufnahmebefehlen:
[Phase-1-Abnahme und Wiederaufnahme](migration/zensical-prototype.md).
Die vier englischen Seiten bleiben ein technischer Prototyp.

### Phase 1 – tatsächlicher Status

- [x] Technische Abnahme: Strict-Build, 167 lokale Verweise ohne Fehler,
  vier Sitemap-Adressen unter `/dxf2gcode/`, 18 Suchindexeinträge.
- [x] Visuelle Inhaltsabnahme der vier Seiten durch den Nutzer abgeschlossen.
- [ ] Optionale zusätzliche visuelle Kontrolle des veröffentlichten Symbols/
  Headers im Browser; technische Live-Prüfung und Publikationsfreigabe liegen vor.
- [x] 15 Wiki-Seiten gesichert, 23 von 24 Medien/Anhängen vorhanden;
  Herkunftsverzeichnis und Rechteprüfung dokumentiert. Rohsicherung ignoriert.
- [x] Neue versionsfreie Wortmarken-/Symbolquellen und abgeleitete
  Windows-/Linux-/ICNS-Symbole lokal eingebunden und unter Qt5/Qt6 geprüft.
- [x] Programm-/Test-/CI-/Infofensteränderungen auf `origin/develop` veröffentlicht;
  ursprüngliche Commits `5017e16` und `a982969` unverändert erhalten.
- [x] Werkzeugwechsel-Testisolation und zusätzliche Qt-/CI-Testfixturefehler
  korrigiert; keine dafür notwendige Änderung des produktiven Exportcodes.
- [x] GitHub-Volltestmatrix für `e2ceed4` bestanden: Python 3.11/3.12/3.13
  mit PyQt5 und Python 3.11 mit PyQt6; siehe Lauf 41327575137 im Übergabebericht.
- [x] Dokumentation (`e2ba4b5`), Branding (`bbc8354`) und Dokumentationsworkflows
  (`6831a0b`) getrennt committed und nach erfolgreicher Develop-CI auf
  `origin/docs/zensical-prototype` veröffentlicht. Dokumentationscheck
  [41328175268](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41328175268)
  bestanden; Status-/Wiederaufnahmebericht als eigener Abschluss aktualisiert.
- [x] Dokumentationsbranch einschließlich Branding/Ressourcen/Workflows ohne
  History-Rewrite nach `develop` integriert; README-/Publishing-Anpassung
  [e4beb1e](https://github.com/dxf2gcode/dxf2gcode/commit/e4beb1e).
- [x] Erneute Integrations-Volltestmatrix
  [41329328147](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41329328147)
  und Dokumentationscheck
  [41329328253](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41329328253)
  bestanden.
- [x] GitHub Pages mit Actions aktiviert und
  [Deployment 41329699445](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41329699445)
  erfolgreich: <https://dxf2gcode.github.io/dxf2gcode/>. Vier Seiten, 159 Live-
  Verweise, Bilder/Favicon, Sitemap und echte Suche geprüft. Veröffentlichung
  war zunächst manuell; inzwischen veröffentlicht der Workflow Änderungen an
  Website-Dateien auf `develop` nach erfolgreichem Strict-Build automatisch.
  Freigabevariable und Environment bleiben erhalten (`b0e5127`).
- [x] Leeres GitHub-Wiki vor und nach Veröffentlichung geprüft, anschließend
  deaktiviert; keine eigenen Seiten zu sichern. Repository-Website und README
  verlinken die neue Dokumentation; SourceForge bleibt unverändert.

### Phase 2 – geplanter Umfang

- [x] [Migrationsmatrix für alle 15 Wiki-Seiten, Zielnavigation und priorisierte
  Arbeitspakete](migration/wiki-migration-plan.md) vorhanden.
- [ ] Jetzt von integriertem `develop` den neuen Branch `docs/wiki-migration`
  für WP1 erstellen; in diesem Veröffentlichungsauftrag noch nicht angelegt.
- [ ] Zuerst WP1: First DXF to G-code mit eigenem kleinen Beispiel und
  ausdrücklich benannten Profilannahmen; anschließend User Guide (WP2–WP7).
- [ ] Für WP6 / Schleppmesser das Tutorial von Erich Styger berücksichtigen:
  [Optimized Vinyl Cutting G-Code Tool Path with DXF2GCODE](https://mcuoneclipse.com/2021/07/06/optimized-g-code-tool-path-for-vinyl-cutting-with-dxf2gcode/)
  (MCU on Eclipse, 06.07.2021). Als weiterführenden Link und fachliche Quelle
  einplanen; Bedienung, Spitzenversatz und maschinenspezifische Einstellungen
  mit dem dann aktuellen Stand abgleichen. Details stehen im
  [WP6-Migrationsplan](migration/wiki-migration-plan.md#wp6-tabs-and-machine-modes).
- [ ] Danach Configuration und Postprozessoren (WP8–WP10), dann Developer Guide
  (WP11–WP12) und historische/Projekt-Dokumentation (WP13).

### Offene Punkte und Wiederaufnahme

- [ ] Rechteklärung für Wiki-Texte, Screenshots, fremde DXFs und Git-Flow-Grafik.
  Ungeklärte Inhalte bleiben außerhalb von Git und Website.
- [x] Neue Logos laut Nutzer selbst gestaltet, GPT-unterstützt, ohne fremde
  Gestaltungsbestandteile; öffentliche Projektverwendung beauftragt. Erklärung
  und Hashes in RIGHTS.md dokumentiert; keine pauschale Rechtegarantie oder
  neue allgemeine Asset-Lizenz daraus ableiten.
- [ ] Fehlendes `Spant.png` (404) bei späterer Migration klären/autorisiert ersetzen.
- [ ] Externe Wiki-/Forum-Verweise bei der jeweiligen Inhaltsmigration prüfen;
  GitHub-Zugriff und öffentliche Zielbranches sind geprüft.
- [ ] Frische Windows-/Ubuntu-/PyQt6-Installationen bleiben getrennte Aufgaben;
  ebenso CNC-/ATC-/manuelle Maschinenabnahme und macOS-Paketabnahme.
- [x] Pages-Ziel, Environment und ausdrückliche Deployment-Freigabe geklärt;
  `DOCS_PREVIEW_PUBLISH_APPROVED=true`. Änderungen an den Website-Dateien auf
  `develop` werden automatisch nach erfolgreichem Strict-Build veröffentlicht;
  der manuelle Workflow bleibt zusätzlich verfügbar.
- [x] Infofenster verlinkt die GitHub-Pages-Dokumentation ausdrücklich als
  Dokumentation im Aufbau; Deutsch, Französisch und Russisch sind gepflegt.

Zur Wiederaufnahme auf `develop` den aktuellen Übergabebericht,
Status und jüngsten CI-Lauf lesen. Lokale Vorschau:
`.\.tox\docs\Scripts\python.exe -m zensical serve`; technische Docs-Prüfung:
mit demselben Interpreter `-m zensical build --strict`. Nächstes Inhaltspaket ist
WP1 vom aktuellen Develop; keine Vollsuite/Installer-Builds zum bloßen Wiederaufnehmen.
