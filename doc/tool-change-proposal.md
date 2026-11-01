# P1: Werkzeugwechsel über das bestehende Postprozessor-Makro

Stand: **01.11.2026**. Ursprünglicher Strukturvorschlag; die erste optionale
Profilerweiterung ist inzwischen implementiert. Maßgeblich für die verfügbaren
Felder, Grenzen und Einrichtung ist die [Makro-Anleitung](tool-change-macros.md).

## Empfehlung

`Program.tool_change` bleibt das frei definierbare Wechselmakro. Dasselbe Feld
kann einen manuellen Wechsel, einen automatischen Werkzeugwechsler oder einen
Aufruf eines steuerungsseitigen Makros ausgeben. Kein zweites konkurrierendes
Werkzeugwechsel-Template einführen und keine universelle M6-/G43-Sequenz
hartcodieren.

Die Erweiterung benötigt zwei Dinge: eindeutige Wechselparameter und einen
erklärten Rückkehrzustand des Makros. Diese Metadaten beschreiben das Makro;
sie ersetzen es nicht durch einen fest eingebauten Wechselablauf.

## Vorhandener Stand und gemeldeter Vorschlag

Das bestehende Template lautet:

```ini
[Program]
tool_change = T%tool_nr M6%nlS%speed%nl
```

`ProfileDialect.chg_tool` setzt Werkzeugnummer und Drehzahl und expandiert das
Template. Es kann bereits mehrzeiligen G-Code und vorhandene Custom-GCode-
Platzhalter verwenden. Es führt dabei jedoch keine Bewegungen oder Moduswechsel
aus dem Text in seinem internen Positionsmodell nach.

Der Kommentar im Konfigurationsschema nennt noch den Layerwechsel. Tatsächlich
prüft `MyPostProcessor.exportShapes` die effektive Werkzeugnummer je Eintrag:
auch beim ersten Eintrag und bei Werkzeugwechseln innerhalb eines Layers.
Gleiche aufeinanderfolgende Werkzeugnummern lösen keinen neuen Wechsel aus.

Die [Originalmeldung im Forum vom 02.02.2025](https://www.ltspiceusers.ch/threads/some-suggest-about-tool-change.3777/)
zeigt Rückfahrt über `G91 G28 Z0`, `M06 T04`, danach `G90`, XY-Positionierung
und `G43 Z1. H04`. Sie schlägt vor, die bisher einmalige Z-Positionierung
hinter dem Wechsel zu verschieben oder dort zu wiederholen. Sie erwähnt selbst,
dass die initiale Rückzugshöhe auch ohne Werkzeugwechsel erforderlich bleibt.

**Bewertung:** Die erforderliche Positionierung nach dem Wechsel ist plausibel.
Ein bloßes Verschieben der Zeile reicht als allgemeine Lösung nicht: Makro und
Steuerung bestimmen die Wechselposition, Werkzeuglängenkorrektur und Reihenfolge
der anschließenden Bewegungen. Die Höhe `Z1.` ist eine Beispielgröße, keine
allgemeine Vorgabe; Einheit und Werkstückbezug müssen dazu passen.

## Was die Steuerungen unterscheiden

| Steuerung | Dokumentierter Unterschied | Konsequenz für das Profil |
| --- | --- | --- |
| LinuxCNC | M6 kann abhängig von der INI Achsen bewegen; M6 aktiviert nicht die neue Werkzeuglängenkorrektur. | Wechselverfahren und anschließendes G43 ausdrücklich passend konfigurieren. |
| Haas Fräsen | M06 übernimmt Spindel-/Kühlmittelstopp, Z-Wechselposition und Spindelorientierung. Neuere NGC-Versionen haben zusätzlich geändertes automatisches Werkzeuglängenverhalten. | Keine zusätzlichen Maschinenbewegungen aus einer pauschalen M6-Annahme ableiten; Steuerungsversion berücksichtigen. |
| Mach3 / Mach4 | Mach3 kann M6 ignorieren, einen manuellen Halt oder Wechselmakros verwenden. Mach4 unterstützt profilbezogene M6-Makros; G43 mit Achswerten kann zugleich positionieren. | Maschinenmakro und Wiederaufnahme müssen ausdrücklich aufeinander abgestimmt sein. |
| Klassisches GRBL 1.1 | Die offizielle Befehlsliste enthält G43.1/G49, aber kein M6 und kein tabellenbasiertes G43 H. | Kein gewöhnliches M6/G43-H-Profil zusichern; Aufteilung in Dateien oder ein separat definierter Senderablauf ist eine eigene Integration. |

Quellen: [LinuxCNC M6](https://linuxcnc.org/docs/stable/html/gcode/m-code.html#mcode:m6),
[Haas M06](https://www.haascnc.com/service/codes-settings.type%3Dmcode.machine%3Dmill.value%3DM06.html),
[Haas G43 / NGC-Versionen](https://legacy-aem.haascnc.com/content/haascnc/en/service/codes-settings.type%3Dgcode.machine%3Dmill.value%3DG43.html),
[Mach3 Konfiguration, Abschnitt 5.5.1](https://www.machsupport.com/wp-content/uploads/2013/02/Mach3Mill_Install_Config.pdf),
[Mach4 Fräsen, G43 und M06](https://www.machsupport.com/wp-content/uploads/2014/05/Mach4%20Mill%20GCode%20Manual.pdf),
[GRBL 1.1 Befehlsliste](https://github.com/gnea/grbl/blob/master/README.md).

Diese Auswahl begründet die Struktur; sie ist keine Zusage fertiger Profile
für sämtliche Steuerungen oder Maschinen. GRBL-Derivate benötigen eine eigene
Betrachtung.

## Parameter des Wechselmakros

Bestehende Platzhalter behalten ihre Bedeutung. Neue Namen sind zunächst ein
Vorschlag und dürfen keine vorhandenen Platzhalter als Präfix enthalten:
Die heutige Expansion verwendet einfache Textersetzung.

| Parameter | Vorgeschlagene Bedeutung |
| --- | --- |
| `%tool_nr`, `%speed`, `%nl` | Bestehende neue Werkzeugnummer, Drehzahl und Zeilenumbruch. |
| `%previous_tool_nr` | Vorheriges tatsächlich ausgewähltes Werkzeug; beim ersten Wechsel nicht bekannt. Kein stillschweigendes Werkzeug 0 erfinden. |
| `%retract_z` | Rückzugshöhe des nächsten Bearbeitungsplans im Werkstückkoordinatensystem. |
| `%initial_retract_z` | Bisherige globale initiale Rückzugshöhe als gesonderter Wert. |
| `%next_start_x`, `%next_start_y` | Tatsächlicher erster Anfahrpunkt des nächsten Plans, einschließlich Lead-in oder Pocket-Einstieg. Nicht ungeprüft den Startpunkt der Originalkontur verwenden. |
| `%length_offset_nr` | Optional ausdrücklich konfigurierte Zuordnung zur Werkzeuglängentabelle; H = T nur bei gewählter Zuordnungsregel. |
| `%units_code` | Zum Export passende Einheit, G20 oder G21, für Profile, die diese Befehle unterstützen. |
| `%distance_mode` | Zum Export passender Modus, G90 oder G91, für entsprechende Profile. |

Maschinenbezogene Einstellungen wie Wechselposition und Makronummer gehören ins
Postprozessorprofil. Sie sind keine Geometrie- oder Shape-Parameter. Als spätere
Ergänzung kann ein eigener, validierter Platzhalter-Namensraum skalare Profilwerte
zugänglich machen. Keine beliebigen Python-Ausdrücke aus Profiltext auswerten.
Unbekannte Platzhalter und fehlende benötigte Zuordnungen sollen vor dem Schreiben
der Ausgabedatei eine verständliche Diagnose liefern.

Die bestehenden Bewegungswerte `%ZE` und `%XE` sind dafür ungeeignete neue
Schnittstellen: Ihre Bedeutung hängt vom letzten Formatierungsaufruf und vom
Absolut-/Inkrementalmodus ab. Wechselparameter sind dagegen ausdrücklich benannte
absolute Zielwerte in der aktuellen Exporteinheit.

## Rückkehrvertrag und Wiederaufnahme

Ein freier G-Code-Text lässt sich nicht zuverlässig allgemein interpretieren.
Deshalb muss ein erweitertes Profil erklären, welchen Zustand das Makro am Ende
herstellt. Vorschlag für eine erste überschaubare Erweiterung:

- Alte Profile bleiben im bisherigen Verhalten. Das vorhandene Template und die
  initiale Z-Ausgabe ändern sich dort nicht.
- Ein Profil kann ausdrücklich einen verwalteten Wechsel aktivieren und den
  Vertrag `next_start_at_retract` wählen: Nach dem Makro steht die neue
  Werkzeugspitze bei `%next_start_x`, `%next_start_y`, `%retract_z` im vereinbarten
  Werkstückbezug. Die benötigte Werkzeuglängenkorrektur ist wirksam.
- Das Profil beschreibt den ausgegebenen Endmodus und den unveränderten oder
  ausdrücklich festgelegten Werkstückbezug. Der Adapter übernimmt die erklärte
  Position und stellt vor normalen Planaktionen den Exportmodus wieder her.
  Bei G91 werden die nächsten Differenzen erst aus dieser Position berechnet.
- Spindel, Kühlmittel und Vorschub werden nach einem Wechsel als neu zu
  initialisieren behandelt. Bereits vorhandene `pre_shape_cut`-Befehle bleiben
  dafür nutzbar; kein Vorschubwert vor dem Wechsel darf nötige neue Ausgabe
  unterdrücken.
- Unbekannte Positionen dürfen nicht als bekannte Koordinaten in G91 weiterleben.
  Weitere Rückkehrverträge, etwa unveränderte XY-Position oder eine feste
  Wechselstation, erst ergänzen, wenn die anschließende Positionierung ebenso
  eindeutig beschrieben ist.

Die wirkliche Maschinenposition ist offline nicht messbar. Die Software prüft
Vollständigkeit und Konsistenz der Profildeklaration; sie kann nicht beweisen,
dass ein beliebiges Maschinenmakro die Deklaration tatsächlich einhält.

Das Makro bestimmt die Reihenfolge: etwa zunächst Z-Freifahrt, dann XY, dann
Z-Ziel mit Längenkorrektur, oder zunächst ein anderes erklärtes Vorgehen.
Ein fest eingebautes `G0 Z...` unmittelbar nach jedem M6 würde diese Freiheit
einschränken und könnte eine falsche Reihenfolge erzwingen.

`G28` und `G53` sind keine gleichbedeutenden Höhenangaben. LinuxCNC dokumentiert
G28 als Fahrt über eine gegebenenfalls programmierte Zwischenposition zu einer
gespeicherten Maschinenposition; G53 betrifft Maschinenkoordinaten.
Wechselhöhe in Maschinenkoordinaten und Rückzugshöhe über dem Werkstück bleiben
getrennte Größen. Siehe [LinuxCNC G-Codes](https://linuxcnc.org/docs/stable/html/gcode/g-code.html).

## Manueller und automatischer Wechsel

Bei einem manuellen Wechsel kann das Profil ein eingerichtetes M6-Verfahren
oder einen steuerungsspezifischen Halt samt anschließendem Vermessen aufrufen.
Ein universelles M0 allein stellt weder Vermessung noch einen aktualisierten
Werkzeuglängenwert sicher. Die Wiederaufnahme muss den gewählten Vertrag erfüllen.

Bei einem automatischen Wechsel kann dasselbe Feld T/M6 oder ein Maschinenmakro
aufrufen. Magazinsteuerung, Sensorabfragen und Vermessungszyklen bleiben auf der
Steuerung. DXF2GCODE liefert die Parameter und die erforderliche Fortsetzung.

Beide Verfahren brauchen dieselbe eindeutige Werkzeug- und Positionsübergabe.
Ein einzelner Schalter „manuell/automatisch“ beschreibt dafür zu wenig; die
Makrodefinition und ihr Rückkehrvertrag sind maßgeblich.

## Verantwortlichkeiten und Umsetzung in kleinen Schritten

1. Bestehenden Wechselablauf mit vollständigen Exportsequenzen charakterisieren:
   erstes Werkzeug, ein Werkzeug, A–B–A innerhalb eines Layers und über Layer,
   leere Layer, leeres Wechseltemplate, benutzerdefinierter G-Code, G90 und G91.
2. Einen ausdrücklichen Wechselkontext an der Exportgrenze bilden. Den nächsten
   Shape-Plan einmal mit Diagnosen erzeugen und anschließend denselben Plan
   verwenden; seine erste Bewegung und Rückzugshöhe liefern die Zielwerte.
3. Das bestehende Template um Wechselparameter und die optionale Deklaration
   erweitern. Formatierung bleibt im Profiladapter. Der normale Konturplaner
   enthält weiterhin keine Maschinenmakros.
4. Den verwalteten Ablauf ergänzen: Makro expandieren, erklärten Zustand
   übernehmen, Modalwerte wiederherstellen und denselben Plan serialisieren.
   Für den ersten Werkzeugaufruf ersetzt dieser Ablauf die bisher davorliegende
   globale Z-Bewegung nur im ausdrücklich aktivierten Profil. Das Makro muss
   deshalb auch den Programmstart abdecken. Ein leeres Makro mit erklärtem
   Rückkehrzustand gilt nicht als erfüllter Wechselvertrag.
5. Zuerst ein dokumentiertes Testprofil für manuelle Wechsel und eines für
   ATC mit dem Ticketablauf aufbauen. Ganze G-Code-Sequenzen vergleichen und
   gezielt den ersten Z-/XY-Befehl sowie G91-Differenzen nach dem Makro prüfen.
   Bestehende Profile und Golden-Ausgaben unverändert absichern.

Der nächste konkrete Umsetzungsschritt ist **1**, gefolgt vom Wechselkontext.
Für den Strukturentwurf muss der Anwender keine Steuerung auswählen. Für ein
tatsächlich einzusetzendes Maschinenprofil bleiben dessen Wechselmakro,
Koordinatenbezug, Werkzeuglängenverfahren und Steuerungsversion erforderlich.
