# Schleppmesser: Einstellungen und neuer Schnittablauf

Stand: **02.11.2026**, lokal implementierter und gezielt geprüfter D1/D2-Ablauf;
siehe [Plan und Prüfnachweise](drag-knife-plan.md). Eine praktische
Materialabnahme ist nicht erfolgt.

## Aktivierung und Tiefen

Der Maschinentyp **Schleppmesser** verwendet einen einheitlichen Schnittablauf.
Lead-in, Lead-out und Überfahrt sind unabhängig wählbar; ein zusätzlicher
Freischalter ist nicht erforderlich. „Keine“ bei beiden Leads und ausgeschaltete
Überfahrt lassen die zusätzlichen Anfahr-, Ausfahr- und Überfahrwege weg.

Im neuen Ablauf bleiben Werkstückoberfläche, Endtiefe und Slice-Tiefe die
vorhandenen Bearbeitungsparameter. Die Slice-Tiefe ist die maximale Zustellung
pro Schnitt. Beispiel: Oberfläche 0, Slice-Tiefe −0,1 mm und Endtiefe −0,3 mm
ergeben Schnitte auf −0,1, −0,2 und −0,3 mm.

Die separate **Schwenk-Kontakthöhe Z** ist eine absolute Z-Koordinate im
Werkstücksystem. Beim Schwenken wird nie tiefer als der aktuelle Schnitt
eingetaucht. Der Winkelgrenzwert entscheidet wie bisher, wann das Messer zum
Schwenken entlastet wird. Die anfängliche Messerstellung wird in Grad angegeben;
0° bedeutet positive X-Richtung.

**Schwenk-Kontakthöhe Z** ist auch in den Konturparametern bearbeitbar. Ohne
eigenen Wert gilt die globale Vorgabe aus **Konfiguration → Ausgabeeinstellungen
→ Ziehmesser-Optionen**. Zum Zurücksetzen auf diese Vorgabe das Konturfeld leeren.
Bei Mehrfachauswahl können unterschiedliche Werte gemeinsam ersetzt werden.

## Messerstellung vor und nach einer Kontur

Die Eingangsstellung ist ausdrücklich auswählbar:

- **Eingestellten Startwinkel annehmen:** Der konfigurierte Winkel wird für
  jeden erneuten Einstieg angenommen. Er ist ein Bedienerwert, keine Messung.
- **Letzten Winkel beibehalten:** Die erreichte Stellung wird zwischen Konturen
  desselben Werkzeugs übernommen. Beim ersten Schnitt oder nach einem
  Werkzeugwechsel beziehungsweise freiem G-Code gilt wieder der konfigurierte
  Startwinkel. Diese Auswahl setzt voraus, dass die Klinge beim Abheben ihre
  Stellung beibehält. Vorschau und Export berücksichtigen dieselbe Reihenfolge.
- **Unbekannt: externe Ausrichtstrecke:** Für Messer, die sich beim Abheben
  verdrehen können. Nach jedem erneuten Abheben führt der nächste Einstieg
  zuerst eine gerade Strecke mit Materialkontakt vor dem eigentlichen Lead-in
  aus. Die bisherige Winkelannahme wird dafür nicht verwendet. Geschlossene
  Tiefenumläufe ohne Zwischenrückzug benötigen diese Strecke nur beim ersten
  Einstieg; offene Schnitte mit Rückzug dagegen bei jedem neuen Einstieg.

Bei unbekannter Stellung sind ein externer Lead-in und eine Ausrichtstrecke
von mindestens dem doppelten Offset erforderlich. Das ist eine geometrische
Untergrenze, kein Nachweis ausreichender Ausrichtung: die tatsächlich benötigte
Strecke muss mit dem konkreten Messer und Material geprüft und eingestellt
werden. Die Software misst keinen Winkel und kann bei völlig unbekannter
Klingenstellung keinen exakten Spitzenweg während dieser Ausrichtstrecke
garantieren. Der Anfahrbereich muss dafür freigegeben sein.

Unabhängig davon lässt sich **im Auslauf vor dem Abheben auf den Startwinkel
ausrichten** einschalten. Dafür muss ein Lead-out gewählt sein. Diese Bewegung
erfolgt genau einmal am Konturende auf entlasteter Kontakthöhe; sie wird nicht
zwischen geschlossenen Tiefenumläufen wiederholt. Eine Rückausrichtung vor dem
Abheben garantiert keine unveränderte Stellung nach dem Abheben. Bei instabiler
Klingenstellung bleibt daher der Einstieg „Unbekannt“ die passende Auswahl.

## Offset und Leads

In der Werkzeugtabelle wird im Schleppmessermodus **Messer-Offset** angezeigt:
der Abstand zwischen Drehachse und Spitze. Die Speicherung verwendet weiterhin
den vorhandenen Durchmesserwert, ohne einen zweiten unabhängigen Offsetwert.
0,25 mm angezeigter Offset entsprechen intern 0,50 mm Durchmesser.

Lead-in und Lead-out wie beim Fräsen in der bestehenden Auswahl der Ebene oder
Kontur wählen. Die Werkzeug-Lead-Länge bestimmt den geraden Teil des Lead-ins;
die Schleppmesser-Auslauflänge ist separat einstellbar. Radius und kombinierte
Gerade/Kreis-Geometrien verwenden den vorhandenen Lead-Radius als Radius der
Messerspitzenbahn. Die Halterbahn wird daraus mit dem Spitzenversatz berechnet.

Beim ersten Einstieg erfolgt die Ausrichtung mit Materialkontakt im
Anfahrbereich. Die gewählte Geometrie muss dort zusätzliche Bewegungen erlauben.
Eine zu kurze Anfahrt wird gemeldet. Die Planung ist keine automatische
Kollisions- oder Verschachtelungsprüfung gegenüber benachbarten Konturen.

**Rampenlänge 0** bedeutet senkrechtes Zustellen bei stehendem XY. Ein positiver
Wert erzeugt gleichzeitige XYZ-Bewegungen über diese Weglänge. Bei vorhandenem
Lead-in ist die erste Schnitttiefe am Sollkonturanfang erreicht. Lead-in „Keine“
ist die bewusst gewählte Alternative für Einstieg und Rampe auf der Kontur.

Gerade Rampen werden als koordinierte XYZ-Geraden ausgegeben. Bogenrampen
werden innerhalb der eingestellten Anpassungstoleranz in XYZ-Geraden zerlegt.
Der resultierende Vorschub wird so begrenzt, dass die XY- und Z-Komponenten
ihre jeweiligen Vorschubvorgaben einhalten. Das neue Postprozessorfeld
`Program.lin_mov_xyz` beschreibt die Ausgabe, standardmäßig
`G1 X%XE Y%YE Z%ZE%nl`. Der neue Ablauf verwendet G-Code-Ausgabe.

## Geschlossene Konturen

Nur der erste Einstieg verwendet die externe Ausrichtung und den Lead-in.
Weitere Schnitte schließen ohne Zwischenrückzug an. Die nächste Zustellung
erfolgt am Konturanfang senkrecht oder über die eingestellte Rampenstrecke auf
der Kontur; die Entlastungsbewegungen an Ecken bleiben erhalten.

Am Ende wird ein noch nicht auf Endtiefe geschnittener Rampenbereich automatisch
nachgeschnitten. **Ein zusätzlicher vollständiger Schnitt auf Endtiefe** ist
eine unabhängige Ein-/Aus-Option, standardmäßig aus. Sie ersetzt diesen
Rampenausgleich nicht. Danach folgt die aktivierte Nahtüberlappung entlang der
Kontur und der Lead-out. Ohne zusätzlichen Vollumlauf ergeben beispielsweise
2 mm Rampenausgleich plus 0,5 mm Überfahrt eine Fortsetzung um 2,5 mm.

## Offene Konturen

Ohne Richtungswechsel erfolgt zwischen den Schnitten ein Rückzug und eine
erneute Anfahrt am Anfang. Bei **abwechselnden Schnitten** sind gerade Leads
an beiden Enden erforderlich. Das Messer fährt aus der Sollkontur heraus,
schwenkt am externen Ende um und stellt auf dem Rückweg zur nächsten Tiefe zu.
Zu kurze oder ungeeignete Leads blockieren den Plan, statt den Ablauf zu ändern.

Bei einer Rampe innerhalb der offenen Kontur wird nach dem letzten Tiefenschnitt
automatisch ein vollständiger Durchgang auf Endtiefe eingefügt. Ein ausdrücklich
gewählter zusätzlicher Endtiefen-Durchgang kommt unabhängig davon hinzu.

## Speichern, Vorschau und Prüfung

Neue Projektdateien im Format 1.5 speichern die Schleppmesser-Einstellungen,
deren Einheit und die relevanten globalen Lead-Vorgaben. Werkzeug- und
Konturwerte werden weiterhin über die vorhandenen Projektfelder gespeichert.
Anwendungskonfiguration 9.18 und Postprozessorkonfiguration 8.3 lesen die bisher
unterstützten Vorgängerversionen weiterhin.

Beim Laden alter Schleppmesser-Profile wird die bisherige Slice-Tiefe einmalig
zur Schwenk-Kontakthöhe. Als Zustellung wird der Abstand von Oberfläche zu
Endtiefe gesetzt, sodass zunächst ein Tiefenschnitt entsteht. Beide Leads
werden auf „Keine“ gesetzt; die Überfahrt bleibt erhalten. Die Konfiguration
wird mit der neuen Versionsnummer gespeichert. Fräs- und Drehprofile behalten
ihre Tiefen- und Lead-Werte. Bereits aktiv verwendete D1/D2-Einstellungen aus
Version 9.17 beziehungsweise Projektversion 1.4 behalten ihre neue Bedeutung.

Alte Schleppmesser-Projekte werden entsprechend übernommen, wobei die
bisherigen Schwenktiefen je Kontur erhalten bleiben. Beim nächsten Speichern
enthält das Projekt die getrennten Werte und Version 1.5. Die Migration erhält
die Bedeutung der Einstellungen; sie garantiert keine identische Folge aller
Bewegungen des früheren Planers. Insbesondere erfolgt keine automatische
Rückausrichtung ohne ausdrücklich gewählten Lead-out.

Vorschau und Export verwenden denselben semantischen Plan einschließlich
XYZ-Rampen. Regressionen kontrollieren die tatsächliche Endtiefen-Abdeckung,
Umkehr und Spitzenversatz, die historische `dxf/drag_knive_test.dxf`,
Projekt-/Einheiten-Roundtrips, Übersetzungen und G90/G91-Ausgabe. Material,
Messereinstellung und freier Anfahrbereich bleiben am konkreten Aufbau zu prüfen.
