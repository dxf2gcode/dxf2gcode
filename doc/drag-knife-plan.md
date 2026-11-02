# Schleppmesser: gemeinsamer Ablauf für D1 und D2

Stand: **02.11.2026**, mit dem Nutzer abgestimmter Zielablauf.
Der Plan ist lokal softwareseitig umgesetzt und gezielt geprüft. Die praktische
Materialabnahme bleibt beim Anwender. Bedienung und Kompatibilität stehen in der
[begleitenden Anleitung](drag-knife-usage.md).
Der gemeinsame Umfang ist im lokalen Commit `fa8335b` abgeschlossen;
[completed](archive/toolpath-refactoring-completed.md#d1-d2) enthält den
abschließenden Prüfnachweis. Die einzelnen Prüfstände unten bleiben historisch
erhalten. Material für die spätere Anleitung steht in den
[Dokumentationsnotizen](documentation-notes/drag-knife.md).
D1 untersucht und korrigiert Rampen und Konturschluss; D2 ergänzt darauf
aufbauend Tiefenzustellungen und einen optionalen zusätzlichen Durchgang.

**Abschlussentscheidung umgesetzt:** Rückausrichtung im Lead-out ist unabhängig
anwählbar. Der Einstieg verwendet wahlweise den angenommenen Startwinkel,
den übernommenen letzten Winkel oder eine externe Ausrichtstrecke bei
unbekannter Stellung. Rückausrichtung vor dem Abheben garantiert keine
Winkelerhaltung danach. Die externe Strecke benötigt eine am Material geprüfte
Länge und wird bei jedem neuen Einstieg nach einem Rückzug wiederholt.
Innerhalb geschlossener Tiefenumläufe gibt es keine erneute Rückausrichtung.

## Lokaler Implementierungs- und Prüfstand

Implementiert sind der einheitliche Schleppmesser-Ablauf, Slice-Zustellungen mit separater
Schwenkhöhe, koordinierte XYZ-Rampen, kontinuierliche geschlossene Umläufe,
automatischer Rampenausgleich und ein unabhängiger zusätzlicher Vollschnitt.
Offene Konturen unterstützen Rückkehr und externe Umkehr mit neu berechneter
Halterbahn. Lead-Geometrien, Offseteditor, Einheiten und Projektsnapshot sind
angebunden; DE/FR/RU-Kataloge einschließlich QM-Dateien sind aktualisiert.

Vor Vereinheitlichung bestanden je **44 fokussierte Tests unter Qt5 und Qt6**: 22 neue D1/D2-Prüfungen,
vier bestehende Schleppmesser-Goldens, ein Plan-/Export-Schnittstellentest,
drei Konfigurations-/Extraktionsprüfungen, sechs Projektadapter- und acht
Postprozessorprofiltests. Die Rampen-Golden wurde für die echte XYZ-Rampe und
die zuvor ausgelassene Restgerade gezielt aktualisiert. Weitere lokale
Grenzprüfungen für bestehende Vorschau, Einheiten, Werkzeugwechsel und
MainWindow-Workflow bestanden. Dialoge wurden bei 125 % gerendert und geprüft.

Geprüft sind auch Winkelübernahme, Werkzeugwechsel-/Custom-G-Code-Grenzen,
unbekannte Stellung, optionale Rückausrichtung und scrollbar erreichbare Felder.
Keine Vollsuite, Debian-/SSH-Prüfung, Paket-/MSI-Erstellung oder Maschinenprüfung
wurde zu diesem früheren Prüfstand gestartet; der spätere Commitabschluss ist
oben verlinkt.

## Bestehende Einstellungen wiederverwenden

- Werkstückoberfläche/Starttiefe bleibt der Bezug für die Bearbeitung.
- Schnitttiefe/Endtiefe bleibt die insgesamt zu erreichende Tiefe.
- Slice depth wird im neuen Ablauf als maximale Zustellung pro Schnitt
  verwendet. Bei Oberfläche 0, Endtiefe −0,3 mm und Slice depth −0,1 mm
  entstehen Schnitte auf −0,1, −0,2 und −0,3 mm. Ein eigener Wert für die
  erste Schnitttiefe ist für diesen Ablauf nicht erforderlich.
- Die bisherige Schleppmesser-Verwendung von Slice depth als absolute
  Schwenktiefe muss davon getrennt werden. Schwenken entlastet das Messer
  und darf es nie tiefer als die gerade ausgeführte Schnitttiefe bewegen.
- Lead-in-/Lead-out-Geometrien werden nach demselben Bedienprinzip wie beim
  Fräsen gewählt. Vorhandene Geometrien nach Eignung wiederverwenden;
  zusätzliche Varianten nur bei fachlichem Bedarf ergänzen.
- Messer-Offset gehört zur Werkzeugtabelle. Der aktuelle Algorithmus nutzt
  den Werkzeugradius: 0,25 mm Offset entsprechen derzeit 0,50 mm Durchmesser.
  Eine ausdrückliche Offsetanzeige soll diese Umrechnung übernehmen; keine
  zwei unabhängig pflegbaren Werte für denselben Abstand einführen.
- Die anfängliche tatsächliche Messerstellung bleibt als Winkel in der
  Schleppmesser-Konfiguration (`drag_start_angle`). Die gewünschte Richtung
  am Kontureinstieg ergibt sich aus Lead-in und Kontur.

Bestehende Profile dürfen durch die neue Bedeutung von Slice depth nicht
unbemerkt andere Tiefenfolgen oder Bewegungen erzeugen. Speicherung und
Übernahme des bisherigen Ein-Schnitt-Verhaltens sind Teil der Umsetzung.

## Erster Einstieg und Ausrichtung

Auch geschlossene Konturen erhalten ihre anfängliche Messerausrichtung im
freigegebenen Anfahr-/Abfallbereich außerhalb der Sollkontur. Bei Innenkonturen
kann dieser Bereich innerhalb der geometrisch eingeschlossenen Fläche liegen.
Materialkontakt zum Ausrichten und ausreichend Platz sind erforderlich;
eine Halterbewegung in der Luft stellt die passive Klinge nicht zuverlässig.

1. Beginn des Lead-ins auf sicherer Höhe anfahren.
2. Auf geeignete Kontakttiefe absenken und das Messer im Anfahrbereich ausrichten.
3. Erste Schnitttiefe über eine der beiden wählbaren Varianten erreichen:
   senkrechtes Eintauchen bei stehendem XY oder gleichzeitige XYZ-Zustellung
   entlang der vorgesehenen Rampenstrecke des Lead-ins.
4. Ausgerichtet auf die Kontur übergehen.

Ausrichtung und Rampe benötigen eigene verfügbare Wegstrecken. Ungeeignete
oder zu kurze Leads nicht stillschweigend durch einen anderen Ablauf ersetzen.
Ein Einstieg beziehungsweise eine Rampe auf der Kontur bleibt eine bewusst
gewählte Alternative; die dabei nötige Nachbearbeitung gehört zum Plan.

## Geschlossene Konturen

**Bestätigt:** Externe Ausrichtung und Lead-in nur beim ersten Einstieg.
Weitere Zustellungen erfolgen kontinuierlich am Konturanfang auf der Kontur,
ohne Zwischenrückzug oder erneuten externen Lead-in. Dabei ist senkrechte
Zustellung oder eine Zustellrampe entsprechend der gewählten Variante möglich.
Eckenschwenks mit ihren Entlastungsbewegungen bleiben erhalten; sie sind von
einem Rückzug zwischen vollständigen Umläufen zu unterscheiden.

Nach dem letzten Tiefenumlauf wird der anfangs noch nicht auf Endtiefe
geschnittene Rampenbereich auf Endtiefe nachbearbeitet. Eine zusätzliche
Nahtüberlappung schließt daran an. Beispiel ohne zusätzlichen Vollumlauf:
5 mm Rampenbereich plus 0,5 mm Nahtüberlappung ergeben 5,5 mm abschließende
Fortsetzung über den nominalen Konturschluss hinaus. Die Abdeckung ist anhand
der Messerspitze zu prüfen, nicht nur anhand der Halterbahn.

## Offene Konturen

- Gleiche Schnittrichtung: am Ende zurückziehen, zum Anfang zurückkehren und
  über den geplanten Einstieg den nächsten Schnitt beginnen.
- Wechselnde Schnittrichtung: hinter dem Konturende ausfahren, das Messer im
  freigegebenen Bereich umkehren, zur nächsten Tiefe zustellen und rückwärts
  schneiden. Gerade Lead-out-/Lead-in-Strecken sind hierfür ein Ausgangspunkt;
  die Bereiche an beiden Enden müssen getrennt einstellbar sein.
- Die Umkehr benötigt eine neu berechnete Halterbahn für den Spitzenversatz;
  die bisherige Halterbahn nicht einfach rückwärts abfahren. Der freigegebene
  Bereich kann zusätzliche Schnitte im Material enthalten.
- Erfolgt die Zustellung vollständig auf dem externen Lead-in, beginnt die
  Sollkontur bereits auf der jeweiligen Schnitttiefe.
- Eine Rampe innerhalb der Sollkontur erfordert nach dem letzten Tiefenschnitt
  einen vollständigen Durchgang auf Endtiefe, damit auch ihr Rampenbereich
  fertig geschnitten ist.

## Optionaler zusätzlicher Durchgang auf Endtiefe

**Bestätigt:** Genau eine Ein-/Aus-Option für einen zusätzlichen vollständigen
Durchgang auf Endtiefe, standardmäßig aus. Keine frei wählbare Umlaufanzahl.
Damit ist auch zweimaliges Schneiden auf derselben Tiefe möglich.

Dieser bewusst zusätzliche Durchgang ist vom automatisch erforderlichen
Rampenausgleich zu unterscheiden und darf nicht stillschweigend durch diesen
ersetzt werden. Die Ausführung muss Kontinuität und Messerorientierung wahren;
am Ende folgen die abschließende Nahtüberlappung bei geschlossenen Konturen
beziehungsweise der Lead-out bei offenen Konturen und der Rückzug.

## Umsetzung und Abnahme

1. Die vorhandenen Rampenfehler reproduzieren und korrigieren: Restgeometrie
   nach Rampenende erhalten, Z-Fortschritt über Segmentgrenzen fortschreiben
   und echte gleichzeitige XYZ-Bewegungen planen.
2. Messerspitzenbahn, ersten Einstieg und Konturschluss für D1 absichern.
3. Tiefenfolgen und kontinuierliche geschlossene Umläufe ergänzen; danach
   offene Konturen einschließlich Rückkehr und externer Umkehr behandeln.
4. Automatischen Rampenausgleich, zusätzlichen Vollumlauf und Nahtüberlappung
   als unterscheidbare Anforderungen mit vollständiger Endtiefenabdeckung prüfen.
5. Werkzeug-/Lead-Bedienung, Konfiguration und Projektroundtrip ergänzen;
   geänderte GUI-Texte in Deutsch, Französisch und Russisch pflegen.

Ein gemeinsamer semantischer Plan enthält sämtliche Bewegungen für Vorschau
und Export. Keine Verdoppelung fertiger G-Code-Texte und keine pauschale
Änderung anderer Maschinenmodi. Fokussierte geometrische Prüfungen umfassen
beide Richtungen, Linien/Bögen, kurze Anfangssegmente, Rampen über mehrere
Segmente, Messerorientierung, Eckenschwenks, Tiefenfolgen, Endtiefenabdeckung
und G90/G91. Praktische Schnittqualität bleibt anschließend am Material zu prüfen.

Weitere Quelle für die spätere Anleitung: [MCU-on-Eclipse-Tutorial von 2021](https://mcuoneclipse.com/2021/07/06/optimized-g-code-tool-path-for-vinyl-cutting-with-dxf2gcode/),
mit den Abgleichhinweisen im [WP6-Migrationsplan](migration/wiki-migration-plan.md#wp6-tabs-and-machine-modes).

## Vorhandene Forums-Testdatei: abschließender Messerschwenk

Der Thread [Dragknife issue](https://www.ltspiceusers.ch/threads/dragknife-issue.1126/)
von Tjmarch/Tim March (17.–20.05.2022) beschreibt einen abschließenden
Messerschwenk auf Schnitttiefe statt auf entlasteter Schwenktiefe. Der Bericht
enthält vier kleine Quadrate als DXF-Beispiel und historische G-Code-Anhänge.
Die damalige Korrektur wurde im Thread nach Wahl des richtigen Develop-Stands
bestätigt; der Bericht belegt keinen noch vorhandenen Fehler im aktuellen Code.

Die lokale [dxf/drag_knive_test.dxf](../dxf/drag_knive_test.dxf) ist als
Testreferenz zugeordnet: Der im Thread verlinkte Commit
`0178408a60a8f65907461bba05e18e564448d65d` vom 18.05.2022 fügte genau diese
Datei hinzu und setzte für den abschließenden Schwenkbogen das `drag`-Merkmal.
Die lokale Datei enthält 4.826 DXF-Zeilenpaare wie im Forums-Debugprotokoll;
auch die protokollierten Startkoordinaten sind enthalten. Der damalige
Attachmentname `test.dxf` ist nicht mit der heutigen `dxf/test.dxf` gleichzusetzen.

Geplante Regressionen mit dieser vorhandenen Fixture:

- Vor einem als entlastungspflichtig markierten Endschwenk zuerst Z-Vorschub
  wählen, auf die zulässige Schwenktiefe bewegen und danach den XY-Vorschub
  für den Schwenkbogen setzen. Erst anschließend endgültig zurückziehen.
- Fälle mit und ohne erforderlichen Endschwenk unterscheiden; keinen
  unnötigen Schwenk allein wegen des Konturendes erzwingen.
- Den letzten Schnitt, Konturschluss und Endschwenk separat prüfen, auch mit
  unterschiedlichen Startausrichtungen, Überfahrt und mehreren Schnitten.
- Die historische Rückausrichtung auf den Startwinkel nicht ungeprüft an
  jedem neuen Tiefenumlauf wiederholen: Kontinuität gemäß D2 erhalten.

Die Fixture wurde über Git-Historie und DXF-Inhalt zugeordnet. Neue fokussierte
Regressionen importieren die fünf Konturen, prüfen Schwenktiefe und Vorschub
und exportieren den gemeinsamen Ablauf mit und ohne Lead-in. Maschinenläufe
wurden nicht ausgeführt.

## Vereinheitlichung und Migration (02.11.2026)

Der Schalter „Geplante Messerschnitte“ entfällt. Lead-in, Lead-out und Überfahrt
sind im Schleppmessermodus direkt wirksam; die Slice-Tiefe bestimmt die Anzahl
der Tiefenschnitte. Konfiguration 9.18 und Projektformat 1.5 unterscheiden die
neue Bedeutung von den alten Schwenktiefen. Alte Profile und Projekte erhalten
einen Tiefenschnitt und deaktivierte Leads bei unveränderter Überfahrt.
Bereits aktivierte D1/D2-Einstellungen bleiben erhalten. Unterschiedliche alte
Schwenktiefen werden als bearbeitbare Konturwerte gespeichert; ohne eigenen
Wert folgt eine Kontur weiterhin der Konfigurationsvorgabe.

Die vier Schleppmesser-G-Code-Referenzen zeigen jetzt die wirksamen Lead-Vorgaben,
Slice-Zustellungen und separate Schwenkhöhe. Die zusätzlichen Regressionen
prüfen einmalige Migration, erneutes Laden, Konturwerte, Einheiten, Mischselektion,
Bearbeitung und Rückkehr zur globalen Vorgabe sowie unterschiedliche Vorschau
für alle Lead-Modi. Bedienung und Grenzen stehen in der begleitenden Anleitung.

Je **130 fokussierte Tests unter Qt5 und Qt6 bestanden**, einschließlich
Profilmigration, Projekt-/Einheiten-Roundtrips, realer Konturfeld-Bearbeitung,
vier aktualisierten G-Code-Referenzen, Vorschau-/Export-Verträgen und
Hauptfenster-Startaktionen. Das Konturfeld wurde zusätzlich im deutschen
Hauptfenster bei 125 % unter Qt6 gerendert und geprüft. Keine Maschinen- oder
Paketabnahme.

Nachbesserung der Werkzeugtabellenprüfung: Die Prüfung erhält den tatsächlichen
positiven Werkzeugwert und berücksichtigt die Messerspitzenbahn separat mit
einer Fräserhülle von null. Zuvor wurde fälschlich ein Durchmesser von null
übergeben und jeder Messer-Offset abgewiesen. Auch bei einer verborgenen
Werkzeugseite folgt die Prüfung dem aktiven Maschinentyp. Wiederholte Wechsel
erhalten die gespeicherten Durchmesser und die passende Offsetanzeige.
Beschädigtes „größer“ und fehlende Zeilenumbrüche der Werkzeugmeldungen sind
korrigiert; DE/FR/RU sind neu kompiliert. Je **38 fokussierte Tests unter Qt5
und Qt6 bestanden**, einschließlich gültiger Offsets, echter Nullwerte,
Fräserradiusgrenzen, Maschinenwechsel und geladener Übersetzungen.
