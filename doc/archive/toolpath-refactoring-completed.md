# DXF2GCODE: abgeschlossene Arbeiten und Prüfergebnisse

Stand: **15.11.2026** (ältere Prüfergebnisse behalten ihren jeweiligen Stand).

## Drei Startoptionen beim Öffnen einer DXF (22.11.2026)

Die Fräseinstellungen bieten das automatische Anlegen mit oder ohne
Fräserradiuskorrektur sowie den reinen Geometrieimport. Im dritten Modus
bleiben die Konturen sichtbar und können später zugeordnet werden. Importierte
Stegregionen bleiben erhalten. Alte Profile übernehmen ihre bisherige Wahl
für den GUI-Import. Gespeicherte Projekte und direkter CLI-Export verwenden
weiterhin ihre jeweiligen Einstellungen.

Geprüft mit Qt5 und Qt6 für DXF-Import, manuelle Zuordnung, Projektladen,
Stegregionen und direkten CLI-Export. Die Profilübernahme und die kompilierten
deutschen, französischen und russischen Menütexte wurden ebenfalls geprüft.

## Canvas-Kontextmenü in der räumlichen VisPy-Ansicht (22.11.2026)

Ein Rechtsklick öffnet das gemeinsame Canvas-Menü. Befehle mit
Klickkoordinaten und das Zeichnen von Stegen sind in der räumlichen
Ansicht mit Hinweis auf die Draufsicht deaktiviert. Rechtsziehen zoomt
weiterhin. Native Qt6-Mausereignisse prüften beide Ansichten, die
Verfügbarkeit der Befehle und den Zoom.

## Gemeinsamer Schalter für die Exportreihenfolge (22.11.2026)

„Exportreihenfolge anzeigen“ in der Gruppe „Ausgabe“ zeichnet die
Exportverbindungen, hält sie bei Änderungen aktuell und blendet sie
beim Ausschalten sofort aus. Die Exportreihenfolge im Baum und die
Pfadrichtungen behalten ihre eigene Funktion.

Geprüft wurden die Anzeige im nativen PyQt6-VisPy-Fenster, das Verhalten
bei Startpunktänderungen und die Exportreihenfolge unter PyQt5 sowie
die kompilierten deutschen, französischen und russischen Texte.

## Strg-Mehrfachauswahl der Stegregionen im Canvas (22.11.2026)

Strg-Klick fügt sichtbare Stegregionen zur Auswahl hinzu oder entfernt sie.
Der linke Editor übernimmt dieselbe Mehrfachauswahl. Der Stegmodus
unterscheidet Klick und Ziehen, sodass Strg-Ziehen weiter am Original
ausrichtet. Native Mausereignisse prüften beide VisPy-Kameramodi und den
Fang. Die fokussierten Qt5-Ansichtstests bestanden ebenfalls.

## Stegregionen links einzeln und gemeinsam bearbeiten (22.11.2026)

Der linke Stegeditor bietet Name, Platzierung, Stegoberkante, Vorschübe,
Aktivierung und Zuordnung auch bei ausgeschaltetem Stegmodus. Strg-Auswahl
im Baum bearbeitet mehrere Regionen gemeinsam, unterschiedliche Werte
erscheinen als Platzhalter. Eine Feldänderung oder Zuordnung ist jeweils ein
Undo-Schritt. Die Zielauswahl für mehrere Regionen zeigt die Schnittmenge
der zulässigen Ziele.

PyQt5 und natives PyQt6 prüften Strg-Auswahl, gemeinsame Höhe, Name,
Aktivierung, Zuordnung und Undo. Die drei Sprachkataloge sind kompiliert und
die neuen Texte verifiziert.

## Werkzeugweg nach Stegoberkante je Zustellung (22.11.2026)

Die Stegoberkante ist die absolute Z-Höhe des Stegs. Der gemeinsame
Werkzeugwegplan hebt bei jeder Zustellung an, die tiefer liegt. Direkt
benachbarte Stege können unterschiedliche Höhen haben. Das Durchgangsfeld
und seine Menütexte wurden entfernt. Alte Projektwerte bleiben lesbar und
steuern die Planung nicht mehr.

Der native Windows-Lauf mit `1997.d2g` prüfte Werkzeugwegvorschau und
G-Code bei Stegoberkante Z −2 mm (Anheben nur aus Z −3 mm) und Z 0
(Anheben aus Z −1,5 und −3 mm). Die Projektdatei blieb unverändert.
Fokussierte Prüfungen deckten benachbarte Stege, exakte Höhenübereinstimmung,
Kompensation, Altprojekt-Lesen und den 2D-Rückfall ab.

## Export- und Optimierungshäkchen im Bearbeitungsbaum (22.11.2026)

Ein Checkbox-Klick ändert den Wert bei unveränderter Konturauswahl und
unverändertem aktivem Baumeintrag. Das Kontextmenü in der Spalte und im
Spaltenkopf bietet Sammelaktionen je Checkbox-Typ. Jede Sammelaktion ist
ein Undo-Schritt. Mausereignisse, beide Spaltenmenüs und Undo wurden mit
PyQt5 und nativem PyQt6/VisPy geprüft. Die Menütexte wurden in Deutsch,
Französisch und Russisch in den kompilierten Katalogen verifiziert.

## Werkzeugdurchmesser im Auswahl-Tooltip (22.11.2026)

Der Tooltip im Werkzeug-Dropdown zeigt den vollständigen Durchmesser in
Projekteinheiten. Eng benachbarte Durchmesser bleiben bei gleicher gerundeter
Anzeige unterscheidbar. Mit Tabellen- und Projektwerkzeugen für mm und Zoll
geprüft.

## GUI1 – Windows-Fokusübergabe nach dem Start (22.11.2026)

Nach dem normalen Qt-Aktivierungsversuch fordert DXF2GCODE einmalig die
Windows-Aktivierung an, wenn das bei Programmstart aktive Fenster noch
im Vordergrund ist. Bei Bedarf werden die Eingabewarteschlangen für den
kurzen Fokuswechsel verbunden und sofort wieder getrennt. Der fokussierte
Test prüfte den Wechsel und das Überspringen bei einem inzwischen anderen
Vordergrundfenster. Der native Qt6-/VisPy-Start und die Qt6-Startfehlertests
bestanden. Der Start über den Debugger in der Nutzersitzung bleibt zu prüfen.

## GUI1 – Zoombasierte Beschriftung verknüpfter Bearbeitungen (22.11.2026)

VisPy fasst die ausgewählten Bearbeitungen derselben Kontur bei kleiner
Darstellung mit ihrer Anzahl zusammen. Beim Heranzoomen erscheinen die
Namen einzeln und werden bei Kollision mit bereits platzierten Texten
versetzt. Der native Lauf mit `1997.d2g` prüfte Zusammenfassung und
Einzelbeschriftung bei identischem Textanker sowie beide Kameramodi.

## GUI1 – Räumlicher Maßstab (22.11.2026)

Die räumliche VisPy-Ansicht zeigt unten rechts gleich lange Maßlinien für
X, Y und Z in den Farben des Nullpunktsymbols, ohne Rahmen oder Hintergrund.
Die Kamera bestimmt ihre
projizierte Richtung und Länge. Der gemeinsame Maßwert folgt dem Zoom.
Das Linealsymbol schaltet den Maßstab in allen Ansichten. Der native
Windows-Test prüfte Rotation, Zoom, Ansichtswechsel und Schalter.
44 Qt5-Maßstabstests bestanden.

## GUI1 – Fensterstart ohne sichtbaren OpenGL-Wechsel (22.11.2026)

Die VisPy-Ansicht wird vor dem ersten Anzeigen in das Fenster eingehängt.
Die 3D-Schalter stehen damit schon beim ersten Anzeigen im Ribbon. Nach
dem Anzeigen prüft ein kleiner OpenGL-Renderdurchlauf die Grafikfähigkeit.
Der 2D-Rückfall bleibt verfügbar.

Der native Windows-Lauf mit `1997.DXF` protokollierte zuvor ein
`Show → Hide → WinIdChange → Show`; die 3D-Schalter erschienen rund
540 ms nach dem ersten Anzeigen. Nach der Änderung erschienen Fenster
und fertiges Ribbon gemeinsam. Nach dem Anzeigen wurde das Fenster
einmal aktiviert und blieb bis zum Testende sichtbar. Die Konstruktion
des Ribbons selbst dauerte im Vergleichslauf 21 ms. Die nativen
Ansichtstests, die Qt5-Rückfalltests und die Qt6-Startfehlertests bestanden.

## GUI1 – Auswahlfilter für Stegregionen (22.11.2026)

Der Werkzeugwegfilter begrenzt die sichtbaren Stegregionen und die
Stegvorschau in der Bearbeitung auf die Auswahl. Die Zuordnung verwendet
die Stegwirkung je Bearbeitung. Der native VisPy-Test prüfte den Wechsel
zwischen verknüpfter und unverknüpfter Bearbeitung im Stegmodus und in der
räumlichen Ansicht. Die fokussierten Qt5-Ansichtstests bestanden ebenfalls.

## GUI1 – XYZ-Achsen am Werkstücknullpunkt (22.11.2026)

Die räumliche VisPy-Ansicht zeigt am Werkstücknullpunkt die positiven
Weltachsen X (rot), Y (grün) und Z (blau). Das Symbol folgt der Kamera und
hat eine zoomunabhängige Maximalgröße. Sein Schalter im Ansichtsband wird
mit den Fensteroptionen gespeichert. Die Draufsicht zeigt das runde
Nullpunktsymbol. Der native Windows-Test prüfte Position, Schalter und
Ansichtswechsel. Die Qt5-Ansichtstests prüften den 2D-Rückfall und die
Übersetzungen.

## GUI1 – Flüssigeres Ziehen von Stegen und Auswahlrahmen (22.11.2026)

Der Auswahlrahmen in der VisPy-Draufsicht nutzt eine feste transparente
Zeichenfläche und fasst Mausbewegungen für die Darstellung zusammen. Beim
Loslassen werden Originalkonturen geprüft und bereits vorhandene Baumzeilen
aktualisiert. Beim Stegziehen werden die Originalkonturen für den Strg-Fang
zwischengespeichert und über ihre Begrenzungsrahmen vorgefiltert. Nach 120 ms
Ziehpause plant die Vorschau die zugeordneten, vom Steg geschnittenen
Bearbeitungen. Das Loslassen übernimmt die Region über den normalen
Bearbeitungsbefehl.

Lokale Windows-Messung mit PyQt6, VisPy und `AFluegel Rippen b2 0201.dxf`
(63 Originalkonturen): bei 20 eingespeisten Mausbewegungen sank die mediane
Verarbeitungszeit für den Rahmen von 38,3 auf 0,31 ms, die höchste Stichprobe
von 109 auf 37 ms. Der Wechsel der Auswahl beim Loslassen dauerte 42 ms
gegenüber 118 ms im vorigen Lauf. Der zwischengespeicherte Strg-Fang dauerte
im Median 0,91 ms, die Stegvorschau für eine Bearbeitung 1,55 ms.
Die nativen Ansichts- und Stegtests sowie 42 fokussierte Projekt- und
Stegregionstests bestanden.

## GUI1 – Fensterstart, Stegwahl und Orientierung in VisPy (22.11.2026)

Das Hauptfenster wird nach dem Einlesen einer Startdatei angezeigt und nach
Initialisierung der Ansicht aktiviert. Die Stegplatzierung bleibt im
Bearbeitungsband als Symbol-Dropdown verfügbar. Seine Mindestbreite lässt
unter Windows Platz für das vollständige Symbol und den Pfeil. Beim Öffnen
passt sich nur die Liste an die Breite der übersetzten Texte an. Die
Listenbreite wurde mit Qt6 für Deutsch, Französisch und Russisch geprüft.
Beide VisPy-Kameramodi zeigen
das 2D-Nullpunktsymbol am Weltursprung und den Maßstab für den aktuellen Zoom.
Das Linealsymbol im Ansichtsband schaltet den Maßstab in beiden Renderern.
Neue Profile aktivieren ihn, bestehende übernehmen ihre Konfiguration.

Der native Windows-Test mit PyQt6 und VisPy prüfte das aktive Fenster, beide
Overlays und die Stegbearbeitung. Die fokussierten Qt5-Ansichts- und
Maßstabstests bestanden. Der breitere Qt5-Offscreen-Test scheiterte beim
Tooltip über überlappenden Konturbeschriftungen.

## GUI1 – Werkzeugwegfilter und gespeicherte Darstellung (22.11.2026)

Das Ansichtsband bietet einen Filter für Werkzeugwege ausgewählter Konturen
und einen Schalter für aufwärts gerichtete Z-Eilgangbewegungen. Die Filter
greifen in der Vorschau und bei der Pfadauswahl. Qt speichert die Schalter
gemeinsam mit dem Fensterzustand in den Benutzereinstellungen.
Der lokale Windows-Test mit PyQt6 und VisPy prüft die sichtbaren Pfade,
die Z-Rückzüge und unveränderte Projektdaten. Acht fokussierte PyQt5-Tests
decken den 2D-Rückfall, das Laden der Einstellungen und die übersetzten
Schaltflächen ab.

## Eigener Zweig für Ribbon und integrierte Ansichten vorbereitet (15.11.2026)

Die vorherigen Dokumentations-/Planbereinigungen einschließlich der identischen
Vergleichs-DXF im gewünschten `dxf`-Ordner sind mit `3da5a15` auf `develop`
gesichert und gepusht. Darauf den neuen Arbeitszweig `ribbon-2d-3d` angelegt.
Das Nutzerziel ist unter GUI1 in beiden offenen Listen festgehalten: 2D primär
zur Bearbeitung, 3D primär zur Darstellung, gemeinsame Bedienung über Ribbon.
Umsetzung und Abnahme erfolgen zunächst auf diesem Zweig. Noch keine GUI-
Änderung, Bibliotheksfestlegung oder Funktionsabnahme durch das Anlegen des Zweigs.

## Nutzerentscheidung zu DOC1, M1, LC1 und CAMotics (15.11.2026)

<a id="doc1-accepted"></a>

**DOC1 abgeschlossen:** Der Nutzer bestätigt die Dokumentations-Sichtprüfung.
Der Punkt ist vollständig aus Kurz- und Detailliste entfernt; keine erneute
Abnahme aufgrund bereits erledigter Dokumentationsarbeiten einfordern.

<a id="m1-macos-dropped"></a>

**M1/macOS nicht weiterverfolgt:** Der Nutzer will und kann die verbleibende
macOS-Abnahme nicht durchführen. Sie entfällt als offene Aufgabe. Das ist
keine macOS-Freigabe; die zuvor belegten Windows-/Ubuntu-/Debian-Nachweise bleiben.

<a id="lc1-auto-dropped"></a>

**LC1-Zusatzmodus verworfen:** Ein zusätzlicher automatischer LinuxCNC-CLI-
stdout-Filter ist nicht gewünscht und entfällt aus beiden Listen. Dies betrifft
die optionale Erweiterung, nicht die bestehende interaktive AXIS-Integration.

**Spätere Simulation:** Beim verbleibenden optionalen Simulations-/Maschinenpunkt
CAMotics als möglichen ersten Schritt für Fräs-G-Code vorgemerkt. Die
[Projektseite](https://camotics.org/) nennt 3-Achs-Simulation und schließt
Drehmaschinen-Simulation aus. Deshalb keine pauschale Abdeckung der Laser-/
Heißdraht-/Drehbeispiele oder physische Freigabe daraus ableiten. Noch keine
Installation oder Simulation gestartet. In beiden aktiven Listen verbleiben
dieselben sechs Themen: CI1, Teilkonturen, PP1, Q1, GUI1 und optionale Simulation/
Maschinenprüfung. Bisherige Links auf entfernte aktive Punkte führen hierher.

## Planung auf zwei offene Listen reduziert (15.11.2026)

Sämtliche fünf Dateien aus `doc/planning` gegen Todo und Abschlussnachweise
geprüft. A1-Abschlussplan, Architektur-Bestandsaufnahme, R3/R1b-Umsetzungsplan
und maschining-project-Releaseplan sind abgeschlossen und ins
[Planungsarchiv](planning/README.md) verschoben. Der letzte Releaseplan ist
vollständig abgearbeitet; die separat beim Nutzer verbleibende Sichtprüfung
DOC1 wird nicht als unerledigter Integrations-/Releaseplan weitergeführt.

Aus beiden aktiven Listen entfernt: umgesetzte Geometrie-/Bearbeitungstrennung,
Verschieben/Kopieren, Migration/Undo/Exportreihenfolge, manuelle Stegregionen,
Fang/Größenautomatik sowie Kandidaten- und endgültige Windows-/Ubuntu-/Debian-
Paketabnahme. Die darüber hinaus vorgeschlagene selbsttätige Stegverteilung
wurde vom Nutzer verworfen und ist keine offene Erweiterung.

Nur `doc/todo.md` (Kurzcheckliste) und `doc/planning/open-task-details.md`
(gleiche neun Themen mit Umfang/Abnahme) bleiben aktiv. CI1 enthält nur den
ersten freigegebenen stabilen Release und Codesignierung, M1 nur macOS.
DOC1, Teilkonturen, automatischer LC1-Filter, PP1, PySide6, Ribbon und optionale
physische Maschinenabnahmen bleiben bewusst offen. Fehlenden LC1-Detailanker
wiederhergestellt; historische R3-/R1b-Verweise führen ins Archiv.

IDs, Entscheidungen D1–D48 und historische Quellen sind erhalten. Verschobene
Dokumente sind ausdrücklich als Historie gekennzeichnet; alte Aussagen über
offene Zwischenstände gelten nicht als neuer Auftrag. Fachmaterial bleibt über
die Dokumentationsnotizen nutzbar. Reine Dokumentbereinigung, keine neuen
Software-, Paket-, SSH- oder Maschinenläufe.

Dokumentprüfung: Die beiden aktiven Listen haben dieselben neun Kennungen;
die Kurzliste wird als neun offene Checkboxen dargestellt. Relative Datei- und
Ankerverweise einschließlich aller verschobenen Pläne geprüft, ursprüngliche
Entscheidungskennungen erhalten und Diff-Prüfung bestanden.

## Dokumentation nach Arbeitsablauf gegliedert (15.11.2026)

Die vom Nutzer bestätigte Struktur ist umgesetzt: User guide mit Einstieg,
Zeichnung/Projekt, Werkzeugen, Bearbeitungsvorbereitung, Werkzeugwegen/Ausgabe
und Spezialanwendungen. Settings, Postprocessors sowie Help and troubleshooting
stehen daneben auf oberster Ebene. Entwickler- und Projektinformationen bleiben
separat; Postprozessor-Beispiele sind unter Postprocessors zusammengeführt.

Kurze Bereichsübersichten öffnen über die Gruppenüberschriften; Breadcrumbs
zeigen die Einordnung. Andere Gruppen bleiben standardmäßig zusammengeklappt.
Die Startseite bietet Bereichseinstiege statt einer langen flachen Kapitelliste.
Werkzeugtabelle, Zuordnung und Projektabweichungen sind als zusammenhängender
Werkzeugbereich ausgearbeitet; vorhandene ausführliche Absätze aus dem
Bearbeitungskapitel dorthin verlagert und in den Einstellungen verlinkt.
Bestehende Seitenpfade und relevante Anker bleiben erhalten, einschließlich
Installation, Diagnosen, Support und den bisherigen Werkzeug-Verweiszielen.

Nachweis: strenger Zensical-Build und Diff-Prüfung bestanden. 56 eindeutige
Navigationsseiten, sämtliche bisherigen Navigationspfade enthalten, keine
doppelte Kapitelzuordnung. Erzeugtes HTML auf sieben Hauptbereiche, sechs
User-guide-Gruppen, passende Unterordnung, anklickbare Übersichten, Breadcrumbs
und aktive/inaktive Aufklappzustände geprüft. Reine Dokumentänderung; keine
Quellcode-, Vollsuite-, Paket- oder Maschinenprüfung dafür gestartet. Die
abschließende generelle Dokumentations-Sichtprüfung bleibt wie vereinbart beim
Nutzer; Struktur-/Publikationsnachweis ist davon getrennt.

## Repository-Startseite auf Bearbeitungsprojekte aktualisiert (15.11.2026)

Auf Nutzerrückmeldung die tatsächlich verwendete Root-README per GitHub-API
bestätigt und um den seit dev13 integrierten Stand ergänzt: Geometrie/Bearbeitung,
benannte Schritte und Mehrfachbearbeitung, Undo/Redo, Werkzeugauflösung,
Stegregionen, unzugeordnete IGNORE-Konturen und D2G 2.1 mit alten Lesern.
Aktuellen eigenen Screenshot und direkte Links zu den passenden Anleitungen
eingebunden. Develop bleibt Vorschau; keine stabile oder physische Freigabe
behauptet. Das separate Organisationsprofil wird durch diese Änderung nicht
stillschweigend mitgeändert.

Nachweis: 12 lokale README-/Bildverweise, Markdown-Diff und GitHub-Markdown-
Rendering erfolgreich geprüft. Reine Dokumentänderung, keine Quellcode- oder
Pakettests erforderlich. Veröffentlichung auf develop und Abgleich der
öffentlichen README gehören zu diesem Auftrag.

<a id="develop-machining-release"></a>

## Schritt 4: maschining-project auf develop / dev13 veröffentlicht

Übernahme und Veröffentlichung am **14.11.2026**, abschließender Download-/Start-
und Website-Abgleich am **15.11.2026**. Der im Gespräch verlinkte Fehlerlauf
`43605863555` gehörte zum ersten Kandidaten; er ist durch den grünen Lauf
`43606276059` mit Testkorrektur `a4849c8` abgelöst, nicht als bestanden gewertet.

`develop` wurde unter Erhalt sämtlicher Historie per Fast-forward auf `65da25e`
übernommen. Gegenüber dem geprüften Kandidaten kam nur der Abschlussnachweis
hinzu; Quell-/Test-/Buildstand sind identisch. GitHub markierte
[PR #5](https://github.com/dxf2gcode/dxf2gcode/pull/5) als merged. Der ältere
GitHub-Develop-Stand `4346709` wurde nicht über die lokale Integrationsbasis
geschrieben; insbesondere bleibt der Qt-Fehlerdialog-Fix `8aeef7f` erhalten.

[Develop-Prüflauf](https://github.com/dxf2gcode/dxf2gcode/actions/runs/43608027083)
und [Release-Lauf](https://github.com/dxf2gcode/dxf2gcode/actions/runs/43608298632)
sind vollständig erfolgreich. Der Release-Lauf prüfte erneut vier Vollsuiten
mit je 1040 Tests, frische Ubuntu-Wheels Qt5/Qt6 sowie Windows-ZIP und tatsächliche
MSI-Installation/GUI/Export/Deinstallation auf dem wegwerfbaren Runner.
Veröffentlicht ist [Develop 2.0.0.dev13](https://github.com/dxf2gcode/dxf2gcode/releases/tag/develop-ci-43608298632),
kein stabiler 2.0.0-Tag. Die Pipeline hat die Nummer aus den veröffentlichten
Develop-Versionen bestimmt; die frühere Kandidatenversion dev22 war kein Release.

Alle sechs öffentlichen Dateien heruntergeladen: Wheel, Quellarchiv, ZIP, MSI,
Manifest und SHA256SUMS. Prüfsummen, veröffentlichte Assetliste und eingebettete
Version/Revision in Quelle, Wheel und ZIP stimmen überein. Windows-Startprüfung
bezieht sich auf dieselben endgültig veröffentlichten Dateien, keine lokale
MSI-Installation über die Arbeitsumgebung. Das endgültige Wheel wurde zusätzlich
in einer neuen Debian-venv installiert und unter X11/Xvfb mit Bearbeitung, Steg,
Projekt-Roundtrip und Export geprüft; Herkunft `65da25e`, `dirty=false`, `origin=build`.
[Maschinenlesbarer Nachweis](develop-machining-release-acceptance.json).

[Pages-Deployment](https://github.com/dxf2gcode/dxf2gcode/actions/runs/43608027016)
erfolgreich. Installation/MSI, Bearbeitungs- und Stegkapitel HTTP 200; sämtliche
16 aktuellen GUI-Bilder stimmen online bytegenau mit dem Repository überein.
Die IGNORE-Beispiel-DXF stimmt nach Git-üblicher CRLF/LF-Normalisierung überein.
Dies ist keine vorweggenommene Sichtabnahme: Die übernimmt der Nutzer am Schluss.
macOS, Codesignierung und physische Maschinenfreigabe bleiben separat.

## Releasebezogene Änderungen statt allgemeiner 2.0-Highlights (15.11.2026)

Auf Nutzerwunsch für künftige Veröffentlichungen ergänzt: eigener Abschnitt je
Paketversion mit letztem veröffentlichtem Release desselben Kanals als Basis,
redaktionelle Versionshighlights und tatsächlicher paginierter Commitvergleich.
Merge-/doppelte Commits werden nicht doppelt aufgeführt; Features/Fixes sind
direkt sichtbar, Dokumentation/Wartung aufklappbar. Entwicklungshistorie ist als
potenziell überholte Zwischenschritte gekennzeichnet; sie wird mit redaktionellen
Highlights vollständig aufklappbar. Der allgemeine 2.0-Überblick bleibt
getrennt im aufklappbaren Versionslinien-Abschnitt. Vollständiger Vergleich und
Herkunftsmarker bleiben erhalten. Drafts/fremde Previews sind keine Vergleichsbasis;
nicht vergleichbare Historie wird abgelehnt. Bereits öffentliche Releases bleiben
unverändert. Die dev13-Versionsdatei dient als konkrete Referenz, nicht als
nachträgliche öffentliche Textänderung.

Nachweis: 20 fokussierte Releaseprüfungen bestanden, darunter Kanaltrennung,
Pagination/Deduplizierung, erste Version, abweichende Historie, Highlights und
UTF-8-Ausgabe. Reale unveröffentlichte Vorschau gegen dev12→dev13 über GitHub
erzeugt. Wartungsvertrag und Download-Anleitung aktualisiert. Kein zusätzlicher
Release allein für die Änderung des künftigen Beschreibungsgenerators.

<a id="pr5-installation"></a>

## Schritt 3 / CI1 / M1: Kandidaten-Paketabnahme (14.11.2026)

[PR #5](https://github.com/dxf2gcode/dxf2gcode/pull/5) stellt den integrierten
Stand bereit; develop bleibt auf `8aeef7f`. Geprüfter PR-Head `a4849c8`,
virtueller PR-Merge `88aec3db41124c850154e86b0a81ab9a6b55e6b8`.
[CI-Lauf 43606276059](https://github.com/dxf2gcode/dxf2gcode/actions/runs/43606276059)
mit allen sechs Jobs erfolgreich; separater Dokumentationslauf ebenfalls grün.
Die Paketversion `2.0.0.dev22` ist ein **Testkandidat**, kein veröffentlichter
Develop-Release und keine Vorwegnahme der nächsten Veröffentlichungsnummer.

| Ziel | Tatsächlicher Nachweis |
| --- | --- |
| Ubuntu 24.04 | Je 1040 Volltests unter Python 3.11/3.12/3.13 + Qt5 sowie Python 3.11 + Qt6; Quellarchiv und daraus Wheel ohne Git gebaut |
| Frische Wheel-Umgebungen Qt5/Qt6 | Ressourcen, Übersetzungen, CLI/GUI-Aufbau, Export; zusätzliche installierte Bearbeitung mit zweitem Werkzeug/Schritt, geteilter Kontur, Stegänderung und D2G-Speichern/Wiederladen/Export |
| Windows Server 2022 x64, wegwerfbarer Runner | Aus demselben Quellarchiv ZIP/MSI gebaut; ZIP-Herkunft, GUI-Start und DXF-Export; MSI tatsächlich installiert, Herkunft/GUI/Export geprüft und anschließend entfernt |
| Debian 13, Python 3.13.5 | Exaktes CI-Wheel in neuer venv installiert: CLI, Qt-Ressourcen/DE-FR-RU, Bearbeitungs-/Steg-/Projektablauf und Export; zusätzlich X11-Start über Xvfb mit PyQt5 5.15.11 / Qt 5.15.19 |

Der erste Kandidatenlauf fand 11 veraltete Anzeigeerwartungen und 17 Steg-
Unterfallfehler durch einen aus anderen Tests geerbten Fensterzustand.
`a4849c8` korrigiert die Testisolation, setzt echte Widget-Namen für die
Feedformatierung und prüft die vereinbarte Anzeigepräzision. Keine Änderung
der abgenommenen Werkzeugwegsemantik. Je 51 betroffene Tests unter Qt5/Qt6
und der verpflichtende 315-Test-Fast-Hook bestanden; danach obiger CI-Gesamterfolg.

Quelle, Wheel, Windows-ZIP und installierte Debian-Anwendung enthalten dieselbe
Version/Revision und `dirty=false`, `origin=build`. Übertragene Wheel-Prüfsumme
auf Debian bestätigt. Artefakte lokal heruntergeladen und SHA-256 erfasst;
[maschinenlesbarer Nachweis samt Manifest, Jobs und Prüfsummen](pr5-installation-acceptance.json).
CI1: realer PR-Paketablauf sowie Sieben-Tage-Aufbewahrung bestätigt; Artefakte
`release-wheel` und `release-windows` verfallen am 21.11.2026. Kein PR-Releasejob
ausgeführt. M1 ist für den vereinbarten Kandidatenumfang Windows/Ubuntu/Debian
abgeschlossen, macOS bleibt separat.

Grenzen: Windows unsigniert; Linux-GUI-Prüfung ohne reale GPU/Monitorabnahme;
keine physische CNC-Abnahme. Dokumentations-Sichtprüfung bleibt beim Nutzer.
Noch kein Merge nach develop oder Release. Etappe D muss die endgültigen
veröffentlichten Artefakte gegen Herkunft/Hashes prüfen und deren Start bestätigen;
der Kandidat allein nimmt einen anderen endgültigen Build nicht ab.

<a id="doc1-machining"></a>

## Schritt 2 / DOC1: aktuelle Anleitung und Bilder (14.11.2026)

Der Nutzer hat die revidierte IGNORE-Fassung nach eigener Prüfung ausdrücklich
abgenommen. Die Anleitung ist auf Geometrie/Bearbeitung, Schritt-/Konturwerte,
Werkzeugauflösung, Mehrfachauswahl, Undo/Redo, Stegmodus D41–D48 und D2G 2.1
abgeglichen. Einstieg, Interface, Import/Projekte, Parameter, Kontur/Tasche/Bohren,
Kompensation, Vorschau, Layerregeln, Einstellungen und Architektur sind korrigiert.
MSI-/ZIP-Weg, Übersichtslinks und Release-Highlights sind ergänzt.

Sechs veraltete Screenshots ersetzt und zehn aktuelle Aufnahmen ergänzt:
echte Qt6-Widgets, isoliertes englisches Demoprofil, eigene Beispielzeichnungen,
keine privaten Profile. Herkunft/Parameter und Nachweisgrenzen stehen in
[Bildmetadaten](../../docs/assets/images/machining/README.txt). Tutorial-Export
mit G21, Tiefen -0.5/-1 und ohne G41/G42 im Demoprofil tatsächlich ausgeführt.
Strenger Zensical-Build erfolgreich. Keine neue Vollsuite oder Paketabnahme
allein für Dokumentänderungen.

Die Browser-Sichtprüfung wurde technisch beendet, weil Computer Use die aktuelle
Browseradresse nicht sicher feststellen konnte. Der Nutzer übernimmt diese
Prüfung ausdrücklich am Schluss; sie blockiert die beauftragte Etappe C nicht.
DOC1 bleibt ausschließlich dafür offen. Noch keine Pages-Veröffentlichung,
kein Merge nach develop und kein Release durch Schritt 2.

Vorbereitung von Schritt 3: `f953d25` sichert die abgenommene IGNORE-Änderung
und ergänzt die installierte Wheel-Prüfung um echten MainWindow-Aufbau,
Werkzeug/Mehrfachbearbeitung, Stegänderung, D2G-Roundtrip und Dateiexport ohne
Quellimporte. Der vorgeschriebene Pre-Commit-Hook bestand mit 315 Fast-Tests.
Der zusätzliche Paketablauf wird erst am tatsächlichen Kandidaten-Wheel
ausgeführt; daraus ist hier noch keine Installationsabnahme abgeleitet.

## MSI-Installationsweg in der Anleitung ergänzt (14.11.2026)

Auf Nutzerrückfrage die veröffentlichte Installationsseite schreibgeschützt
geprüft: HTTP 200, keine MSI-Erwähnung. Der Text beschrieb nur Quellstart und
behauptete keine bereits veröffentlichten Windows-Pakete. Parallel bestätigte
die GitHub-Releases-API den Develop-Prerelease `develop-ci-42259036046` mit
`dxf2gcode-2.0.0.dev12-20261106-g452ba97-windows-x64.msi` und zugehörigem ZIP.

Die vorbereitete Anleitung zeigt nun GitHub Releases und den Windows-MSI-Weg
vor den Quellstart-Anforderungen: gewünschte Vorschau wählen, Assets öffnen,
Installer herunterladen und ausführen, Startmenü/Infofenster verwenden.
Portable ZIP-Installation ist getrennt erklärt. Beide Windows-Pakete enthalten
ihre Python-/Qt-Laufzeit; die Quellstart-Werkzeuge sind dafür nicht nötig.
Benutzerbezogene Ordner, getrennte Develop-/Stable-Kanäle, Deinstallation,
Signierungsstatus und Herkunftsdateien sind anhand des vorhandenen Buildcodes
und Releasevertrags beschrieben. Dauerlinks führen auf die Releaseübersicht,
statt einzelne versionsgebundene MSI-Dateien oder `releases/latest` festzuschreiben.

Nachweis: öffentliche Seite und Release-Assets live gelesen, Anleitung gegen
`source/tools/build/windows.py` und `doc/release-pipeline.md` abgeglichen;
strenger Dokumentationsbuild und Diff-Prüfung bestanden. Reine Dokumentänderung,
keine Installer-Ausführung oder neue Paketabnahme. Änderung liegt in der
Integrationskopie und ist noch nicht veröffentlicht oder committed.

## IGNORE als unzugeordnete Geometrie und Vergleichs-DXF (14.11.2026)

Auf Nachfrage zur Gleichheit mit normal unzugeordneter Geometrie hat der Nutzer
die Importänderung bestätigt und anschließend Altprojekt-Sonderbehandlung für
diesen internen Typ ausdrücklich verworfen. Die vorherige IGNORE-Fassung mit
gesperrten Sonder-Schritten ist damit abgelöst. Der interne Bearbeitungstyp
`ignored` samt GUI-, Vorschau-, Tooltabellen- und Zuordnungssperren ist entfernt.
Die DXF-Präfixerkennung und die optionale vollständige Importausblendung bleiben.
Allgemeine alte Projektformate wurden nicht entfernt; es gibt keinen speziellen
Migrationspfad für intern gespeicherte `ignored`-Schritte mehr.

Beim Erfassen einer IGNORE-Kontur wird ihre Original-Geometriereferenz erhalten,
aber keine Bearbeitung angelegt. Sie erscheint im normalen unzugeordneten Bereich,
ohne Vorschau/Export. Explizite Zuordnung erzeugt eine aktivierte normale
Bearbeitung; der DXF-Layername sperrt deren materialisierten Schritt nicht.
Undo und Projekt-Roundtrip erhalten die jeweilige Zuordnung.

Die eigene [Vergleichs-DXF](../../docs/assets/examples/ignored-layers/ignore-layers-mm.dxf)
enthält vier gleich aufgebaute Spalten mit je Rechteck 20 × 12 mm und Kreis R4:
Normal_Machining, IGNORE:Construction, IGNORE:Helpers und Compare_Unassigned.
Die beiden IGNORE-Spalten sind beim ersten Import unzugeordnet; die rechte
Spalte lässt sich durch Entfernen ihrer Bearbeitungszuordnungen direkt vergleichen.
[Bedienhinweise](../../docs/assets/examples/ignored-layers/README.md).

Nachweis: je 71 fokussierte Prüfungen unter PyQt5/PyQt6 bestanden (Projektmodell,
Bearbeitungsbefehle, Tooltabelle, echter Qt-Panelablauf und Architekturgrenzen).
Die Beispielzeichnung wird über den echten DXF-Import geladen: acht Konturen,
zwei normale Schritte, vier unzugeordnete IGNORE-Konturen. Nach Entfernen der
rechten Vergleichszuordnungen haben alle sechs unzugeordneten Konturen dieselben
deaktivierten Originalzustände und keine Vorschauzuordnung. Danach IGNORE-Kontur
normal zuordnen, Exportreihenfolge/Aktivierung und Undo prüfen. Der reine Modellfall
prüft auch Speichern/Lesen und einen frei benannten Schritt mit IGNORE-Präfix,
der trotzdem normal exportiert wird. DE/FR/RU bereinigt, QM regeneriert und geladen
geprüft; strenger Dokumentationsbuild und Diff-Prüfung bestanden. Kein Commit/Push,
keine Vollsuite oder Paket-/Maschinenabnahme für diese nachträgliche Präzisierung.

<a id="r3-ignore-complete"></a>

## Schritt 1: Integrationsbasis und IGNORE-Korrektur (14.11.2026)

Die offenen Abschluss-/Planungsdokumente sind auf `maschining-project` mit
`3e05281` gesichert. Nach Aktualisierung der Remote-Referenzen wurde eine isolierte
Arbeitskopie auf Basis des lokalen `develop` angelegt. Der Integrationszweig
`integration/maschining-project-release` enthält mit Mergecommit `f696631` sowohl
den Featurestand als auch den zusätzlichen Develop-Fix `8aeef7f`. Einziger
Mergekonflikt war das Abschlussarchiv; beide Nachweise bleiben enthalten.
Der eigentliche `develop`-Zeiger wurde nicht geändert.

IGNORE ist begrenzt korrigiert: Neue Schritt-/Zuordnungsdialoge bieten
`ignored` nicht an. Vorhandene ignorierte Schritte zeigen ihre unveränderbare
Art beim Bearbeiten weiter an. Ihre Konturen bleiben auswählbar, zeigen in
der Exportspalte „Ausgeschlossen“ statt einer Checkbox und bieten keine
Optimierungscheckbox. Hinweistext erklärt den dauerhaften Ausschluss und die
normale Exportcheckbox für vorübergehendes Ausschließen. Der Checkbox-Handler
übernimmt auch programmatisch keine Aktivierungsänderung für ignorierte Einträge.
Gespeicherte `enabled`-/Optimierungswerte werden nicht normalisiert; Import,
Altprojektmigration und Speichern bleiben erhalten. Planung und Exportregel
für `IGNORE:` wurden nicht verändert.

Nachweis: Der neue GUI-Fall reproduzierte vor dem Fix die bedienbare Checkbox.
Danach je 31 fokussierte Prüfungen unter PyQt5/PyQt6 bestanden: echte Panel-/
Dialogabläufe, Modell/Altprojekt-Roundtrip, Exportausschluss und die übernommenen
Startup-Fehlerdialogtests. DE/FR/RU einschließlich QM aktualisiert und geladen
geprüft. Strenger Dokumentationsbuild und Diff-Prüfung bestanden.

Der Integrationscommit bestand den verpflichtenden Fast-Hook mit 314 Tests.
Dessen erster Versuch scheiterte an den in einer neuen Arbeitskopie fehlenden,
nicht versionierten Qt-UI-/Ressourcenmodulen; nach Übernahme der zum identischen
UI-Quellstand generierten Module bestand der Hook. Der IGNORE-Funktionscommit
verwendet ebenfalls den verpflichtenden Hook. Keine manuelle Wiederholung einer
bereits bestandenen Fast-Suite. Keine Paket-/Debian-/Maschinenabnahme, kein Push
oder Release. Nächste Etappe: vollständiger Anleitungs-/Bildabgleich gemäß Plan.

<a id="r3-r1b-complete"></a>

## R3/R1b fachlich abgenommen und Abschlussumfang festgelegt (14.11.2026)

Der Nutzer erklärt das Feature `maschining-project` für fertig und die
Nutzerabnahme R3/R1b/P8 für durchgeführt und akzeptiert. Dieser Abnahmeblock
ist aus der aktiven Todo entfernt. Der aktuelle Stegumfang ist ausreichend;
eine zusätzliche selbsttätige Stegverteilung wird nicht weiter verfolgt.
Dies schließt die alte offene P7-Erweiterungsplanung durch Umfangsentscheidung,
ohne einen nicht implementierten Verteilungsalgorithmus als fertig auszugeben.

Die optionale Wiederverwendung historischer Fremdinhalte einschließlich ihrer
Rechteklärung wird verworfen. Keine ungeklärten Originale werden damit zur
Übernahme freigegeben. Teilkonturen bleiben ausdrücklich offen.

Der [Abschluss-/Releaseplan](planning/maschining-project-release-plan.md)
trennt IGNORE, Anleitung/Bilder, Installationsnachweis und Merge/Develop-Prerelease.
Bestätigt sind die begrenzte IGNORE-Korrektur vor dem Merge und die Matrix
Windows-ZIP/MSI, Ubuntu Qt5/Qt6 sowie Debian-Wheel. macOS bleibt separat.
DOC1 erhält einen konkreten Vorschlag zum Abgleich der gesamten betroffenen
Anleitung mit echten aktuellen Screenshots. Die eigenständige Develop-Korrektur
`8aeef7f` muss bei der Integration zusätzlich zum Featurestand `69f9767` erhalten
bleiben; diese Commitangaben beschreiben den lokalen Planungsstand.

Die Nutzerabnahme ersetzt keinen Paket-/Installations- oder physischen
Maschinennachweis. Im Planungsauftrag nur Aufgaben-/Planungsdokumente geändert;
Dokumentationsbuild und lokale Link-/Diff-Prüfung bestanden. Keine Quellcode-
Tests, Installation, SSH-Abnahme, Merge, Push oder Veröffentlichung gestartet.

## R3/D48: verbindliche Zielauswahl vor Steganlage (14.11.2026)

Nutzerregel umgesetzt: Ohne vorherige Originalkontur-/Bearbeitungsauswahl wird
kein neuer Steg erzeugt. Originalkontur umfasst alle verknüpften Bearbeitungen,
einzelne oder mehrere Bearbeitungen nur sich selbst, ein Schritt seine enthaltenen
Konturen. Die Zeichen-Zielauswahl bleibt bei fortlaufender Anlage und beim
Inspizieren der entstandenen Region erhalten. Normale neue Auswahl ersetzt sie;
Leerraumklick löscht sie. Eine Ziehbewegung ohne Ziele legt keine Region an.

Anlage verwendet ausschließlich überschneidende ausgewählte Originalkonturen;
keine automatische Fremdzuordnung oder nachträgliche Auswahl eines beliebigen
Ziels. Unterschiedliche automatische Quadratmaße ergeben getrennte Regionen
für die betreffenden Bearbeitungen. Gleiche Quadrate können ihre Zuordnung teilen.
Alle resultierenden Regionen werden in einem atomaren, validierten Befehl mit
gemeinsamem Undo/Redo erzeugt. Bestehende Stegbearbeitung bleibt unabhängig davon
möglich; kein weiteres persistentes Feld oder Format.

Nachweis: je 30 fokussierte Prüfungen unter PyQt5/PyQt6 bestanden (Panel,
Regionsmodell, Canvas-Interaktion, Architektur). Reale Ereignisse decken Auswahl
einer Bearbeitung, Mehrfachauswahl, Originalkontur mit zwei Verknüpfungen,
Schrittauswahl, fehlende Auswahl, fremde ausgewählte Kontur und zwei Werkzeuge
mit getrennten automatischen Größen ab. Batch-Anlage hat einen Undo-Schritt,
Redo erhält den ganzen Satz; ein Fehler im Batch übernimmt keine Teilmenge.
Eine zunächst veraltete Baum-ID wird bei transienter Zielaufnahme ignoriert,
statt eine Qt-Slot-Ausnahme auszulösen. DE/FR/RU-Hinweise ergänzt, QM regeneriert
und geladen geprüft. Strenger Dokumentationsbuild und Diff-Prüfung bestanden.
P8-Fachabnahme bleibt offen; kein Commit/Push und keine Vollsuite oder
Paket-/GPU-/Maschinenabnahme.

## R3/D47: Auswahl vor Ziehen und Maßfelder nur bei ruhender Auswahl (13.11.2026)

Bestätigten Ablauf umgesetzt: Erstklick auf eine Stegregion wählt sie aus.
Auch Ziehen während dieses ersten Drucks verändert keine Vertices und erzeugt
keinen Undo-Eintrag. Bereits ausgewählte Regionen lassen sich anschließend
verschieben oder über Eckgriffe ändern. Bei Überlagerungen wird die aktuelle
Auswahl bevorzugt. Nicht ausgewählte Regionen verwenden eine kleinere Rand-
Treffertoleranz und zeigen noch keine aktiven Eckgriffe. Doppelklick öffnet
weiterhin den Regionsdialog; direktes fortlaufendes Anlegen bleibt erhalten.

Maßfelder erscheinen ausschließlich an ruhender Auswahl. Jede Zeichnungs-,
Verschiebe- oder Größenänderungsgeste blendet sie aus; nach Loslassen erscheinen
sie wieder. Explizite Maßeingabe schaltet automatisch auf manuell, auch wenn
derselbe Zahlenwert erneut eingetippt wird. Unverändertes Bestätigen ohne
Eingabe, ungültige Werte und Abbruch verändern weder Modus noch Geometrie.

Nachweis: je sieben fokussierte Panel-/Canvas-Prüfungen unter PyQt5/PyQt6
bestanden. Echte Mausereignisse prüfen Erstklick samt Bewegung ohne Mutation,
Auswahl ohne Undo, anschließende Bearbeitung, Doppelklick und verborgene Maße
während Zeichnen/Größenändern/Strg-Ziehen. Eingabe desselben Werts, Wechsel auf
manuell und Undo sind ebenfalls abgedeckt. Bestehende DE/FR/RU-Texte unverändert
wiederverwendet und geladen geprüft. Strenger Dokumentationsbuild und Diff-Prüfung
bestanden. Fachliche P8-Abnahme bleibt offen; kein Commit/Push, keine Vollsuite
oder Paket-/GPU-/Maschinenabnahme.

## R3: direkte Stegzugänge und spezielles Kontextmenü entfernt (13.11.2026)

Bestätigte Ergänzungen umgesetzt: Neben dem Stegmodus-Schalter erscheint im
aktiven Modus eine Auswahl Fang/Manuell für neue Regionen. Sie aktualisiert die
vorbereitete nächste Region, ohne den Modus eines vorhandenen ausgewählten Stegs
zu ändern. Dessen individuelle Einstellung bleibt im Doppelklick-Dialog.
„Zuordnung entfernen“ ist direkt im Regionsparameterbereich verfügbar und nur
beim Bezug zu einer konkreten betroffenen Bearbeitung aktiv; globale Regions-
Auswahl aktiviert den Button nicht. Das Entfernen bleibt lokal und Undo-fähig.

Das spezielle Steg-Kontextmenü ist aus Canvas, Bearbeitungsbaum und Regionsliste
entfernt. Im Stegmodus wird kein Ersatzmenü geöffnet. Doppelklick, Löschbutton/
Entf, Aktivierungshäkchen und Modusschalter übernehmen die übrigen Aktionen.
Das normale Canvas-Menü außerhalb des Stegmodus bleibt erhalten. Keine Änderung
von Projektformat oder Werkzeugwegplanung.

Nachweis: je 21 fokussierte Prüfungen unter PyQt5/PyQt6 bestanden (Panel,
Canvas-Interaktion, 3D-Adapter mit Fake-GL). Reale Tests wechseln den nächsten
Anlegemodus, prüfen unveränderte vorhandene Regionen, deaktivierten Zuordnungs-
Button ohne Bezug, lokale Entfernung per Button/Undo und das Ausbleiben von
Kontextmenüs im Canvas und an Regionsknoten. Regionsliste verhindert Kontextmenüs,
die Modusauswahl wird beim Verlassen ausgeblendet. DE/FR/RU-Kataloge bereinigt,
QM regeneriert und geladen geprüft. Strenger Dokumentationsbuild und Diff-Prüfung
bestanden. Reale GPU-/P8-/Paket-/Maschinenabnahme bleibt getrennt; kein Commit/Push.

## R3: Stegmodus startet unmittelbar das Zeichnen (13.11.2026)

Einschalten über den Schalter in der Bearbeitungs-Werkzeugleiste startet eine
vorbereitete Zeichensitzung, ohne vorherige Kontextmenüaktion. Ausschalten
beendet sie weiterhin. Der gewählte Startmodus und die bestehende fortlaufende
Regionserstellung bleiben erhalten. Programmatische Auswahl/Bearbeitung alter
Regionen benötigt dadurch keinen erzwungenen Neustart einer Zeichensitzung.

Nachweis: je sieben fokussierte Panel-/Canvas-Prüfungen unter PyQt5/PyQt6 bestanden.
Der reale Ablauf aktiviert den Modus über die Toolbar-Aktion und zeichnet die
erste sowie eine weitere Region ohne Kontextmenü. Bestehende Katalogtexte werden
unverändert verwendet und geladen geprüft. Strenger Dokumentationsbuild und
Diff-Prüfung bestanden. Kein Commit/Push und keine Vollsuite oder Maschinenabnahme.

Menüprüfung: Bearbeiten per Doppelklick, Löschen per Entf/Button, Aktivierung per
Häkchen und Beenden über den Schalter sind direkt erreichbar. Eine Auswahl
Fang/Manuell für neue Regionen und „Zuordnung entfernen“ im Parameterbereich
wurden als noch fehlende direkte Zugänge vorgeschlagen. Diese Ergänzungen und
vollständiges Entfernen gegenüber optionalem Beibehalten des speziellen Menüs
sind ausdrücklich zur Nutzerentscheidung offen; das Menü bleibt vorerst erhalten.

## R3/D46: Werkzeugnachführung automatischer Stege und Kantenmaße (13.11.2026)

Automatische Regionen folgen dem geänderten Werkzeugdurchmesser. Der gemeinsame
Befehlsabschluss erfasst Werkzeugwechsel, Projektwerkzeug-Aktualisierung und
Werkzeugzuweisung über andere Schritte; die aktuelle konfigurierte Steglänge wird
in Projekteinheiten addiert. Manuelle Regionen bleiben unverändert. Nach bestätigter
Nutzerentscheidung werden gemeinsam verwendete automatische Regionen bei Bedarf
je Bearbeitung aufgeteilt. Unbetroffene Verwendungen behalten ihre Form; Änderung
und neue Regions-IDs sind Bestandteil desselben Undo-/Redo-Eintrags.
Scopes vor dem Werkzeugwechsel erhalten die Zuordnung auch beim Verschieben
einer Kontur in einen neuen Werkzeugschritt. Einheitenwechsel lösen diese
Nachführung nicht zusätzlich aus. Kein weiteres Speicherfeld erforderlich.

Maßfelder sitzen mittig auf oberer und rechter Kante, ohne Breite-/Höhe-Präfix;
Zahl und Einheit sowie volle Eingabegenauigkeit bleiben erhalten. Eckgriff- und
Maßklick unterscheiden sich anhand der nächstliegenden Griff-/Textmitte.

Nachweis: je 55 fokussierte Prüfungen unter PyQt5/PyQt6 bestanden
(Regions-/Projektmodell, Panel, Canvas, Architektur). Neue Fälle: Werkzeugwechsel
und Werkzeugaktualisierung mit 4+2=6, unveränderte manuelle Region, bedarfsgerechte
Aufteilung einer gemeinsamen Region, atomare Undo-/Redo-Snapshots sowie echter
GUI-Werkzeugwechsel und exakte Kantenpositionen. Paneltests zoomen für die
Griff-/Maßbedienung gezielt auf die Region; die Werkzeugwechsel-Fixture hält
ihren vorhandenen Lead-Radius gültig. DE/FR/RU-Kataloge bereinigt, QM regeneriert
und geladen geprüft. Native Windows-Aufnahme der neuen Maßpositionen visuell
geprüft. Strenger Dokumentationsbuild und Diff-Prüfung bestanden. P8-Fachabnahme
bleibt offen; keine Vollsuite, Paket-/GPU-/Maschinenabnahme und kein Commit/Push.

## R3/D45 präzisiert: Aufziehen, Modus je Steg und Doppelklick (13.11.2026)

Die nachträgliche Nutzerpräzisierung ersetzt den bisherigen Klick-/Dialogablauf:
Beide Modi beginnen durch Aufziehen eines Rechtecks. Beim Loslassen wird die
Region direkt erzeugt; Fang stellt sie auf das konfigurierte Quadratmaß samt
nominaler Ausrichtung, manuell behält die aufgezogene Form. Nur eine mehrdeutige
Bearbeitungs-/Werkzeugwahl fragt nach dem Ziel. Zeichnen bleibt anschließend aktiv.
Der Regionsdialog öffnet per Doppelklick im Canvas, im Bearbeitungsbaum und in der
Regionsliste; Original-Regionsknoten öffnen ihn ebenfalls. Bearbeitungsaktionen
im Kontextmenü/Parameterbereich öffnen denselben Dialog.

Jede Region speichert `placement_mode` als `snap` oder `manual`. Vorhandene/importierte
Regionen ohne Feld bleiben manuell. Moduswechsel über Regionsmenü oder Dialog gilt
nur für diesen Steg. Fang beim Umschalten/Größenändern übernimmt das aktuelle Maß;
direkte Maßeingabe setzt manuell, damit eigene Maße erhalten bleiben. Normales
Verschieben oder bloße Konfigurationsänderung skaliert Regionen nicht. Das optionale
Feld ergänzt das noch unveröffentlichte Format 2.1 und ist validiert/Undo-fähig.

Nachweis: je 53 fokussierte Prüfungen unter PyQt5/PyQt6 bestanden (Panel,
Regions-/Projektmodell, Canvas, Architektur). Neue/angepasste reale Abläufe:
direkte Anlage ohne Dialog, Fang/Handeingabe durch Aufziehen, Quadrat beim
Größenändern, Moduswechsel je Steg, direkte Maßeingabe, Doppelklick-Dialog,
Zielwahl/Abbruch, Undo sowie Rundlauf und Altdatei-Default des neuen Felds.
Ein Qt6-Test berechnet seine Mausposition nach Ansichtsänderungen erneut;
der anschließende Panelablauf bestand unter beiden Bindings. Bestehende
DE/FR/RU-Texte wiederverwendet und mit geladenen QM-Katalogen geprüft.
Strenger Dokumentationsbuild und Diff-Prüfung bestanden. P8-Fachabnahme bleibt
offen; keine Vollsuite, Paket-/GPU-/Maschinenabnahme, kein Commit/Push.

## R3/D45: werkzeugabhängiges Fangquadrat und Konfigurationsvorgaben (13.11.2026)

Nutzerentscheidung umgesetzt: Fang per Konturklick erzeugt ein Quadrat mit
Seitenlänge Werkzeugdurchmesser plus verbleibender Steglänge. Ø4 mm und 2 mm
Steglänge ergeben 6 × 6 mm. Die gewählte Originalkontur liefert Position und
Ausrichtung; mehrere mögliche Bearbeitungen erfordern eine Werkzeug-/Zielwahl,
wenn keine davon ausdrücklich aktiv ist. Der Regionsdialog bestätigt anschließend
Werte und Zuordnung. Fortlaufendes Anlegen und vorhandene Maßeingabe bleiben erhalten.

Neue Anwendungskonfiguration `Tab_Regions`: `creation_mode` mit Default `snap`
und Alternative `manual`, `tab_length` mit Default 2 in Konfigurationseinheiten.
Kontextmenü bietet beide Modi für die laufende Sitzung an. Die Länge wird vor
Addition des Projekt-Werkzeugdurchmessers in Zeichnungseinheiten umgerechnet.
Gespeicherte Regionen behalten ihre tatsächlichen Vertices bei Werkzeug- oder
Vorgabenänderung; kein neues Projektformat. Z-Oberkante bleibt separat.

Nachweis: je 36 fokussierte Prüfungen unter PyQt5/PyQt6 bestanden, einschließlich
Regionsmodell, echtem Panel-/Klickablauf, Konfigurationspersistenz/-übersetzungen,
Canvas und Architekturgrenzen. Neue Fälle prüfen das 4+2=6-Beispiel, Klick statt
Aufziehen, zwei Konfigurationseinheiten, Zielwahl/Abbruch bei Mehrfachbearbeitungen,
Sitzungsumschaltung, fortlaufende Anlage und Undo. Ein anfänglicher Testfehler
(`ConfigObj.Section.update` erwartet ein Dictionary) wurde korrigiert; der betroffene
Test und Panelablauf bestanden anschließend erneut unter beiden Bindings.
Neue Texte/Hilfen in DE/FR/RU ergänzt, QM regeneriert und geladen geprüft.
Strenger Dokumentationsbuild und Diff-Prüfung bestanden. Fachliche Abnahme bleibt
P8, insbesondere reale Reststege an Ecken/engen Bögen. Keine Vollsuite,
Paket-/GPU-/Maschinenabnahme und kein Commit/Push.

## R3: fortlaufende Stegsitzung, Konturwechsel und Regionszählung (13.11.2026)

Zeichnen bleibt nach bestätigter Neuanlage aktiv. Weitere Regionen können an
anderen Originalkonturen angelegt werden, ohne den Modus neu zu starten.
Konturklick wählt die entsprechende Originalgeometrie, Leerraumklick löst
Regionsauswahl und abgeleitete Markierungen; der Stegmodus bleibt offen.
Maßfelder und Eckgriffe der ausgewählten Region bleiben bedienbar.
Die Zahl am Konturknoten zählt nun die darunter aufgeführten Regionsobjekte.
Ursache der Abweichung war das Zählen einzelner geplanter Stegabschnitte;
eine einzelne Region kann mehrere davon erzeugen.

Nachweis: je sieben fokussierte Panel-/Canvas-Prüfungen unter PyQt5/PyQt6
bestanden. Echte Mausereignisse prüfen Konturwechsel im Zeichnen, Leerraum-
Abwahl, direkte zweite Neuanlage an anderer Kontur und Undo. Ein zusätzlicher
Planabschnitt derselben Region erhöht die Baumzahl nicht mehr. Bestehende
Maßeingabe/Strg-Ausrichtung sowie Katalogübersetzungen bleiben geprüft.
Strenger Dokumentationsbuild und Diff-Prüfung bestanden. Keine Vollsuite,
Paket-/GPU-/Maschinenabnahme, kein Commit/Push. Die zusätzliche Konfiguration
für Fang/Handeingabe und Standardmaß war hier noch offen; anschließend durch
D45 entschieden und umgesetzt (siehe obigen Nachweis).

## R3/D44: Live-Maße, direkte Maßeingabe und Strg-Ausrichtung (13.11.2026)

Bestätigte Bedienung umgesetzt: Breite und Höhe rechteckiger Stegregionen werden
beim Zeichnen/Größenändern und an der Auswahl angezeigt. Maße folgen der
Projekteinheit und Anzeigepräzision. Hover hebt die Zahl hervor, Klick öffnet
eine Eingabe mit voller Genauigkeit. Positive endliche Maße werden mit Enter
symmetrisch um die Mitte übernommen; die andere Kantenlänge bleibt erhalten.
Escape oder Fokuswechsel verwerfen die Eingabe. Maßfelder verdecken keine
Eckgriffe und werden beim Editieren über der Vorschau dargestellt.

Strg beim Ziehen richtet die Breitenachse an der Verbindung genau zweier
Originalkontur-Schnittpunkte aus und setzt die Mitte zwischen die Kontakte.
Die aktuellen Kantenlängen bleiben erhalten. Ein eindeutiges Ziel wirkt live;
mehrere Originalkonturen erfordern beim Loslassen eine Auswahl. Abbruch erhält
das normale Ziehergebnis. Wiederholte Bearbeitungen derselben Originalkontur
werden als Fangziel zusammengefasst; ohne geeignetes Kontaktpaar bleibt die
Ziehbewegung erhalten und eine Meldung erklärt den ausgelassenen Fang.
Geraden und Bögen verwenden dieselbe nominale Schnittgrundlage wie D41.
Jede bestätigte Änderung bleibt ein vorhandener Regions-/Undo-Befehl;
keine zusätzlichen persistenten Felder oder Formatänderungen.

Nachweis: jeweils 44 fokussierte Prüfungen unter PyQt5/PyQt6 bestanden
(Regionsmodell, nominale Stege, Architektur, Panel und Canvas-Interaktion).
Neue Fälle prüfen exakte Maßübernahme, Mittelpunkt/andere Kante, ungültige Werte,
Hover/Klick/Enter/Escape, reale Strg-Ziehereignisse und Undo, Geraden-/Kreiskontakte,
Mehrfachverwendungs-Deduplizierung sowie Auswahl/Abbruch bei mehreren Fangzielen.
DE/FR/RU ergänzt, QM regeneriert und geladen geprüft; native Windows-Aufnahmen
für Maßanzeige und Eingabefeld visuell geprüft. Strenger Dokumentationsbuild und
Diff-Prüfung bestanden. Fachliche Bedienabnahme bleibt P8; automatische Platzierung,
reale GPU-/Paket-/Maschinenabnahme bleiben getrennt. Kein Commit oder Push.

## R3: Regionszuordnung auf überschneidende Konturen begrenzt (12.11.2026)

Der bestätigte Vorschlag ist umgesetzt: Nur Bearbeitungen mit einem positiven
Originalkonturabschnitt im Regionsinneren stehen zur Zuordnung bereit. Der
nominale D41-Schnittdienst liefert dieselbe geometrische Grundlage; reine
Rand-/Eckkontakte erzeugen dort keinen Steg. Mehrfachbearbeitungen bleiben
getrennte Ziele. Schrittlisten enthalten nur Schritte mit passenden Konturen.
Genau ein Kandidat wird beim Neuanlegen vorbelegt. Ohne Schnitt zeigt der Dialog
den Hinweis und sperrt „OK“ beim Neuanlegen; Abbruch ändert nichts.

Global zeigt die passenden Bearbeitungen als mitumfasst an und erhält lokale
Ausnahmen. Geometrische Kandidaten hängen nicht von Fräserradius, Z-/Passwahl,
Aktivierung oder momentanem Scope ab. Bereits gespeicherte unwirksame Regionen
werden nicht gelöscht. Vorhandene Kandidatenwahl bleibt beim Wechsel zwischen
Global/Schritt/Bearbeitungen erhalten.

Nachweis: je 63 fokussierte Prüfungen unter PyQt5/PyQt6 bestanden, einschließlich
Regionsmodell, D41, Passregeln, Architektur und echtem Panelablauf. Neue Fälle:
Durchlauf statt Rand-/Eckkontakt, zwei Bearbeitungen derselben Kontur als getrennte
Ziele, Ausschluss einer fremden Kontur im Dialog, ein vorausgewählter Treffer,
leere Liste mit gesperrter Neuanlage selbst bei Global sowie unveränderte Daten
bei Abbruch. Bestehende Eckpunkt-Abnahmeregion wurde auf echten Durchlauf bis
zur Ecke präzisiert; der zuvor nur auf dem Rand liegende Fall gilt nun als Kontakt.
Hinweis in DE/FR/RU ergänzt, QM-Dateien regeneriert und geladen geprüft.
Strenger Dokumentationsbuild und Diff-Prüfung bestanden. Kein Commit/Push;
keine Vollsuite oder Maschinenabnahme.

## R3: sprachabhängiger Namensvorschlag für neue Stegregionen (12.11.2026)

Neue Regionen erhalten den ersten freien Namen nach übersetztem Schema:
„Steg 1“, „Steg 2“ usw.; Englisch „Tab“, Französisch „Attache“, Russisch
„Перемычка“. Die Prüfung berücksichtigt bereits gespeicherte Regionsnamen.
Der vorgeschlagene Name bleibt frei änderbar; bestehende Namen werden durch
Sprachwechsel nicht verändert. DE/FR/RU-Kataloge und QM-Dateien aktualisiert.
Je zwei fokussierte Paneltests unter PyQt5/PyQt6 bestanden, einschließlich
geladenen Übersetzungen, konkreten Vorschlägen in allen drei Sprachen und
vorbelegtem, weiterhin überschreibbarem Namensfeld im echten Anlegedialog.
Strenger Dokumentationsbuild und Diff-Prüfung bestanden. Kein Commit/Push.

## R3/D43: einheitliche Regions- und Schrittauswahl (12.11.2026)

Die bestätigte Auswahlregel ist umgesetzt: BREAKS-Layer und Regionsgruppen
verwenden die Vereinigung ihrer Regionsbezüge und heben alle wirksam verknüpften
Bearbeitungen hervor. Globale Regionen zeigen Bezüge auch in anderen Schritten.
Wiederholte Klicks bleiben stabil, Doppelklicks auf Gruppen klappen auf/zu.
Einzelne Regionsreferenzen springen nicht mehr zum ersten Vorkommen im Baum.

Schrittnachfahren und Regionsbezüge erscheinen als hellere abgeleitete
Baummarkierungen. Die tatsächliche Auswahl bleibt unverändert als Vertrag für
Parameter und Drag-and-drop: Schrittvorgaben bei Schrittwahl, Regionswerte bei
Regionswahl, gesperrte Zusammenfassung bei Regionsgruppen. Die Vorschau hebt
deren referenzierte Werkzeugbahnen mit den bestehenden Farben hervor. Rot für
Originalauswahl, Blau für Werkzeugbahn und Magenta für Stege bleiben erhalten.
Zuordnungsänderungen aktualisieren den Bezug sofort, einschließlich Auslassen
einer zuvor hervorgehobenen Bearbeitung. Kein gespeicherter Projektzustand wird
durch reine Bezugsauswahl geändert.

Nachweis: je 21 fokussierte Prüfungen unter PyQt5/PyQt6 bestanden: Panelablauf,
Canvasinteraktion und 3D-Befehle/Projektion. Erweiterte echte Mausereignisse an
`BreakExample_Circle.dxf` prüfen wiederholte Layerklicks/Doppelklicks, einzelne
Originalregionen, Regionsgruppen, Schritte sowie eine globale Region mit
Referenz in einem zweiten Schritt. Geprüft sind Vorschauauswahl, Baumrollen,
Erhalt des geklickten Knotens, Kontext, Drag-Payload, unveränderte Projektdaten
und History. Windows-Bilder für Schritt-/Gruppenmarkierung visuell kontrolliert.
Gruppenhinweis in DE/FR/RU ergänzt, QM-Dateien regeneriert und geladen geprüft.
Strenger Dokumentationsbuild und Diff-Prüfung bestanden. Kein Commit/Push;
keine Vollsuite, reale GPU- oder Maschinenabnahme.

<a id="r3-manual-regions"></a>

## R3/D42: Konturverknüpfung und manuelle Stegregionen (12.11.2026)

Der bestätigte Vorschlag und die drei Nutzerentscheidungen sind umgesetzt:
Regionen folgen der gesamten Zeichnungstransformation, Bearbeiten erfolgt in
2D und jede neue Region endet mit einem Bestätigungsdialog für Name, Höhe,
Vorschübe und Zuordnung. In der 3D-Hauptansicht öffnet ein separater 2D-Editor.
Die erste neue Höhe ist Werkstückoberkante, danach der zuletzt verwendete bzw.
zuletzt gespeicherte manuelle Wert. Vorschübe stammen aus der Auswahl.

Stegregionsobjekte besitzen eigene IDs, Quelldaten oder eigene Polygonpunkte,
Scope global/Schritt/Bearbeitungen und lokale Ausnahmen. Format 2.1 liest
weiterhin 2.0 und Legacy; alte BREAKS-Bearbeitungen werden mit ID-/Werterhalt
übernommen. Die Materialisierung filtert Regionen vor der gemeinsamen Planung
nach Scope/Ausnahmen. Undo/Redo stellt Form, Werte und Zuordnungen gemeinsam her.

Bearbeitungsbäume referenzieren Regionen direkt unter der betroffenen Kontur;
die Kontur zeigt die Anzahl wirksamer Stegabschnitte. Der Geometrie-Tab besitzt
einen eigenen einklappbaren Regionsbereich mit Herkunft/Wirkung. BREAKS-Originale
haben Regionsnamen/-symbole, entfernte Regionszuordnungen sind durchgestrichen.
Normale Konturauswahl blendet die wirksamen Rechtecke automatisch gestrichelt
magenta ein. Regionauswahl hebt zugehörige Konturen hervor, ohne selbst den
Editiermodus einzuschalten. Die bisherigen Bewegungsfarben bleiben erhalten.

Im Stegmodus: Rechteck aufziehen, Vorschau mit demselben Planer, Werte bestätigen,
Umriss verschieben und Eckgriffe ziehen. Erst Loslassen erzeugt eine Undo-Aktion.
Esc/Dialogabbruch ändern nichts. „Zuordnung entfernen“ schließt nur diese
Bearbeitung aus; globales Löschen benötigt die Rückfrage mit Betroffenenzahl.
Original-DXF-Geometrie bleibt erhalten. Während der Sichtprüfung wurde außerdem
die D41-Teilung absolut transformierter Geometrie korrigiert: Original und
Werkzeugbahn werden vor der Teilung in denselben absoluten Raum aufgelöst.

Nachweis: je 116 fokussierte Prüfungen unter PyQt5/PyQt6 bestanden, inklusive
sechs neuer Regionsmodellprüfungen und erweitertem echten Panelablauf mit
`BreakExample_Circle.dxf`: automatischer Regionsanzeige, Originalbaumauswahl,
Zeichnen mit Modalbestätigung, Vorschau, Verschieben, Eckgriffen, Esc,
Zuordnungsausnahme, Löschabbruch/Löschen, Undo, .d2g-2.1-Wiederladen und
G-Code mit gespeicherter Stegoberkante. Die 2D-Editoransicht wurde ohne realen
GL-Kontext geöffnet/geprüft. Tests sichern außerdem Transformation/Inverse,
Migrationswerte/IDs, Scopes, Undo/Redo und D41-Absolutkoordinaten.
DE/FR/RU ergänzt, QM-Dateien regeneriert und geladen verifiziert. Deutsche
Windows-Baumansichten und Regionsdialog visuell kontrolliert. Strenger
Dokumentationsbuild und Diff-Prüfung bestanden.

Offen bleiben Nutzer-/reale GPU-/Maschinenabnahme, Fang und automatische
Platzierung. Keine Vollsuite, Debian- oder Paketabnahme. Kein Commit/Push.

Commit-Vorprüfung: Der erste Fast-Hook-Lauf mit 313 Prüfungen meldete eine
fehlgeschlagene Panelprüfung: Überlauf wurde bei zufällig verfügbarer
Fensterhöhe vorausgesetzt. Der Test verkleinert den Parameterbereich jetzt
ausdrücklich, prüft die Scrollleiste und stellt die vorherige Größe wieder
her. Beide fokussierten Paneltests bestehen danach; keine Produktänderung.
Der Folgelauf fand eine weitere Randannahme desselben Tests: Ziehen gegen die
bereits erreichte Mindesthöhe kann die Größe nicht ändern. Die echte
Mausbewegung nutzt jetzt den tatsächlich verfügbaren Splitterbereich.
Die Werkzeugreihenfolge wird anhand echter `Tn M6`-Zeilen geprüft; eine
Teilstringsuche nach `T1` hatte auch den Zeitstempel `T14:…` getroffen.
Der verpflichtende Hook wird beim erneuten Commit vollständig ausgeführt.

## R3: gewähltes Stegmodus-Symbol bei den Bearbeitungsaktionen (08.11.2026)

Nutzerwahl Variante 2 umgesetzt: gestrichelte Region, kreuzende Kontur und
Bearbeitungsstift. Das Symbol wird wie die History-Icons mit Palette und
mehreren Auflösungen gezeichnet; deaktivierte Zustände erhalten eigene
Palettenfarben. Der umschaltbare Button steht unmittelbar nach „Erstellen“
links bei den Bearbeitungsaktionen. Die Baumdarstellungsbuttons bleiben rechts.
Vorhandene übersetzte Beschriftung und Funktion bleiben unverändert.

Nachweis: je zwei bestehende echte Panel-/Übersetzungsprüfungen unter PyQt5
und PyQt6 bestanden. Neue Position und aktive Darstellung im erzeugten
deutschen Windows-Fensterbild visuell geprüft. Das Aufnahmehilfsskript endete
anschließend mit Exitcode 1 ohne weiteren Trace; dies ist kein erfolgreicher
Gesamtworkflow-Nachweis des Hilfsskripts. Die getrennten Panelprüfungen sind
erfolgreich. Strenger Dokumentationsbuild und Diff-Prüfung bestanden.
Keine Vollsuite, Veröffentlichung oder zusätzliche Plattformabnahme.

<a id="d41"></a>

## D41: einheitlicher Stegbezug an der Originalkontur (08.11.2026)

Geschlossene polygonale BREAKS-Regionen werden auf der Originalkontur ausgewertet.
Der reine Wertdienst `domain/toolpath/tabs.py` überträgt deren zusammenhängende
Intervalle über Geradennormalen bzw. konzentrische Bogenradien auf die vorbereitete
Werkzeugmittelpunktbahn. Interne und maschinenseitige Korrektur verwenden damit
dieselben nominalen Bezugsstellen, ohne tangentiale Radiuszugabe. Die Region muss
die Offsetbahn nicht erreichen. Aufmaß ändert den Bezug ebenfalls nicht.

Vom Nutzer entschiedene Sonderfälle: Mehrdeutige/verschwundene Grenzen oder
getrennte Offsetteile lassen den dortigen zusammenhängenden Steg vollständig
entfallen und erzeugen eine Warnung; der Export bleibt erlaubt. Andere gültige
Stege derselben Region bleiben erhalten. Eckübergreifende Stege halten die
Verbindung durchgehend auf Steghöhe. Auch am geschlossenen Konturstart wird
nicht erst durch den Steg auf Frästiefe eingetaucht. Stegbögen bleiben Bögen;
Geometrie, Zuordnung und Kurvenform überstehen Umkehr, Exitadapter und Überfahrt.
Die Modifikatoranzeige zählt auch wirksame Bogenabschnitte.

Taschen-Randkonturen verwenden D41; Rasterfüllungen ohne Originalkonturpartner
behalten ihre räumliche Regionsauswertung. Schleppmesser bleiben unverändert.
Offene/nicht polygonale Regionen werden gewarnt und ausgelassen. Globale
Zuordnung, Z-Höhen, Vorschübe, Passauswahl und Speicherformat bleiben erhalten.
Bestehender G-Code wird nicht geändert, sondern muss neu exportiert werden.

Nachweis: je 103 fokussierte Prüfungen unter PyQt5/PyQt6 bestanden, davon
17 D41-Prüfungen mit Unterfällen. Enthalten: G40/G41/G42 intern/maschinell,
verschiedene Radien und Aufmaß, schmale/schräge Regionen, Geraden und echte
Offsetbögen, Eckverbindung ohne Zustich, Konturstart, Richtung/kollineare
Zusammenfassung, Tangentialkontakt, fehlende/mehrdeutige Grenzen, getrennte
Offsetteile und Erhalt anderer Stege. Gemeinsamer Plan mit gleicher Vorschau
und G-Code-Ausgabe geprüft; bestehende Steg-/Pass-/Lead-/Überfahrt-/Slice-
Goldens und echte Panelabläufe bestanden. Warnung in DE/FR/RU ergänzt,
QM-Dateien regeneriert und geladen geprüft. Strenger Dokumentationsbuild und
Diff-Prüfung bestanden. Keine Vollsuite, Paket-, Debian-, reale GPU- oder
Maschinenabnahme; Nutzerabnahme P8 bleibt offen. Keine Veröffentlichung.

## R3: Stegmodus-Mausauswahl unter Qt6 korrigiert (08.11.2026)

Der gemeldete `QPainterPath.contains(QPoint)`-Absturz wurde mit echten
Canvas-Mausereignissen unter PyQt6 reproduziert. Die Trefferprüfung wandelt
die Eingabeposition jetzt ausdrücklich in `QPointF` um. Der bisherige direkte
Test über `pointAtPercent()` lieferte bereits `QPointF` und deckte den realen
Ereignistyp deshalb nicht ab. Der Paneltest klickt nun zwei verschiedene
Stegregionen über das Viewport an und prüft Regionskontext und Baumzeile.

Nachweis: vor Korrektur gleicher TypeError; danach je zwei fokussierte
Paneltests unter PyQt5/PyQt6 bestanden, einschließlich der vorhandenen
Stegverwaltungs-, Export-/Undo- und Übersetzungsprüfungen. Diff-Prüfung
bestanden. Keine GUI-Texte geändert; keine Vollsuite, Paket- oder
Plattformabnahme. D41 bleibt eine separate vorgemerkte Algorithmusänderung.

## R3: importierte Haltestege als Modifikatoren (08.11.2026)

Nutzerentscheidung D40, Variante 1: BREAKS-Regionen erscheinen in besonderen
Haltesteg-Gruppen unter den tatsächlich betroffenen Bearbeitungsschritten.
Dieselbe globale Region wird referenziert, nicht kopiert. Die tatsächlichen
Planbewegungen liefern Zuordnung und Anzahl wirksamer Stegabschnitte;
Tiefenpass-Wiederholungen werden dedupliziert. Unwirksame/deaktivierte Regionen
bleiben separat erreichbar. Normale Canvas-/Rahmen-/Originalbaumauswahl
überspringt Stegregionen. Keine Werkzeuge, Exportcheckboxen, normale
Konturaktionen oder Reihenfolgeaktionen für die Modifikatorzeilen.

Ein eigener Stegmodus zeigt Umrisse in bestehendem Magenta und erlaubt
Stegoberkante, XY-/Z-Vorschübe, Aktivierung und Entfernen mit Undo/Redo.
Die Herkunft und globale Wirkung sind ausdrücklich sichtbar. Bestehende
globale Exportwirkung und Projektformat bleiben erhalten; Metadaten am Plan
verändern keine Ausgabe. Zeichnen, Formänderungen, lokale Zuordnung, Fang
und automatische Platzierung bleiben P7.

Nachweis: je 53 fokussierte Prüfungen unter PyQt5/PyQt6 bestanden:
Stegschnittpunkte und Passregeln, echte Panelereignisse, Canvasinteraktion
und 3D-Befehle/Projektion. Enthalten sind BreakExample, normale Auswahlsperre,
Regionsauswahl/-eigenschaften, Aktivierung/Entfernen mit Undo, identische
G-Code-Ausgabe danach, globale Referenz in zwei Schritten und JSON-Modell-
Roundtrip geänderter Werte. Neue Texte in DE/FR/RU ergänzt, QM-Dateien
regeneriert und geladen geprüft. Deutsche Windows-Darstellung visuell
kontrolliert. Strenger Dokumentationsbuild und Diff-Prüfung bestanden.
3D verwendet einen simulierten GL-Kontext; reale GPU-, Nutzerprofil-, Paket-,
Debian- und Maschinenabnahme bleiben offen. Keine Vollsuite oder Veröffentlichung.

## BREAKS: Endlosrekursion an Steg-Eckpunkten verhindert (08.11.2026)

Der Nutzertrace beim Laden von `dxf/BreakExample.dxf` endet wiederholt in
`breakLineGeo`. Der ursächliche Randfall wurde gezielt reproduziert: Ein
Polygon-Eckpunkt wird von seinen beiden Kanten zweimal als derselbe Schnitt
gemeldet. Das erzeugte einen Steg ohne Länge und erneute Teilung desselben
Reststücks bis zum RecursionError. Schnittpunkte werden jetzt mit der
bestehenden Geometrie-Punkttoleranz dedupliziert. Ein reiner Eckkontakt bleibt
ohne Steg; zwei unterschiedliche Eckdurchgänge erzeugen einen echten Steg.
An Originalendpunkten werden keine leeren Linienreste bzw. unbeabsichtigten
Vollkreis-Bogenreste erzeugt. Steghöhe und Vorschübe bleiben erhalten.

Nachweis: je 34 fokussierte Prüfungen unter Qt5/Qt6 bestanden (fünf neue
Schnittpunktregressionen, 27 bestehende Stegdurchgangsprüfungen, zwei
Paneltests). Enthalten sind beide Linienrichtungen, Endpunkte, Bogenende,
Import/Vorschau der Beispieldatei sowie Laden und Export aus dem echten
Hauptfenster mit weiterhin enthaltenem Steg-Z-Hub. Ursächlicher Eckkontakt
vorher mit derselben Rekursion reproduziert. Die frische Testkonfiguration
ersetzt keine Abnahme mit dem Nutzerprofil; dieses ist nicht übernommen worden.
Keine Vollsuite, Paket-, Debian- oder Maschinenabnahme. Diff-Prüfung bestanden.

## R3: Zuordnungsdialog mit stabiler Größe und Werterhalt (08.11.2026)

Alle Felder im Zuordnungsdialog bleiben sichtbar und an festen Positionen.
Vorhandenes Ziel aktiviert nur die Schrittauswahl, neues Ziel Name/Art/Werkzeug;
die jeweils anderen Felder samt Labels sind ausgegraut. Die Größe wird einmal
aus dem vollständigen Formular bestimmt und fixiert. Zielwechsel sowie
Namenseingaben lösen kein `adjustSize()` mehr aus. Die Aktion wird nur beim
Öffnen vorbelegt; selbst ein noch unberührtes „Kopieren“ bleibt beim Wechsel
zu „Neuer Schritt“ erhalten. Alle gewählten/geänderten Werte bleiben gespeichert.

Nachweis: je zwei fokussierte Paneltests unter Qt5/Qt6 bestanden, einschließlich
echtem modalem Dialog, mehrfacher Umschaltung, konstanten Fenster-/Feld-/
Buttonpositionen und Erhalt von Aktion, Name, Art, Werkzeug und vorhandenem
Ziel. Bestehende Zuordnungs-/Undo-/Abbruchabläufe bleiben geprüft. Deutsche
Windows-Darstellung in beiden Zielzuständen visuell kontrolliert. Vorhandene
DE/FR/RU-Texte unverändert weiterverwendet. Strenger Dokumentationsbuild und
Diff-Prüfung bestanden. Keine Vollsuite oder Paket-/Plattformabnahme.

## R3: passende Schritte vor automatischer Neuanlage wiederverwenden (08.11.2026)

Artwechsel, etwa Taschenfräsen/Bohren, und Konturwerkzeugwechsel prüfen zuerst
vorhandene Schritte. Kompatibel sind gleiche Zielart, vollständige
Werkzeugdefinition und identische gespeicherte Schrittvorgaben. Gleiche
T-Nummer allein reicht nicht; Namen sind kein Ausschlusskriterium. Ein Treffer
wird genutzt, bei mehreren wird gemäß Nutzerentscheidung ein Ziel verlangt.
Gleich benannte Ziele bleiben in der Auswahlliste eindeutig unterscheidbar.
Auswahlen gelten nur für einen Auftrag; Abbruch lässt Projekt/History unverändert.

Zuordnungen behalten IDs, Geometriereferenzen und eigene Werte und werden dem
Ziel hinten angefügt. Bestehende Ziele behalten Name und Vorgaben. Ohne Treffer
gelten die bisherigen Neu-/Aufteilungsregeln; bei vollständig ausgewähltem
Werkzeug-Quellschritt bleibt dessen Identität ohne Treffer erhalten. Explizit
„Neuer Schritt“ erzeugt weiterhin einen Schritt. Auch die Rückkehr von Bohren
zu Kontur kann nun den ursprünglichen passenden Konturschritt nutzen.

Nachweis: je 30 fokussierte Befehls-/Paneltests unter Qt5 und Qt6 bestanden:
wiederholte Taschenaktionen, Teil-/Vollauswahl beim Werkzeugwechsel, abweichende
Defaults und gleiche T-Nummer mit unterschiedlichem Durchmesser, explizite
Neuanlage, Zielwahl bei mehreren Treffern, Abbruch, Undo/Redo und unveränderte
Parameter-/Exportabläufe. DE/FR/RU ergänzt, QM-Dateien regeneriert und
Übersetzungen geprüft. Strenger Dokumentationsbuild und Diff-Prüfung bestanden.
Keine Vollsuite, Paket-, Debian- oder Maschinenabnahme; praktische Abnahme P8 offen.

## R3: gemeinsamer Zuordnungsdialog, Menüvariante 2 (08.11.2026)

„Bearbeitung zuordnen …“ öffnet aus Canvas, Geometrie- und Bearbeitungsbaum
denselben Dialog: Kopieren/Verschieben sowie vorhandener/neuer Zielschritt.
Vorhandene Ziele zeigen Name, Art und Werkzeug; neue Ziele ergänzen die
editierbaren Felder. Bestehendes Ziel ist mit Kopieren vorbelegt, neues mit
Verschieben, bis die Aktion ausdrücklich gewählt wird. Explizit ausgewählte
mehrere Referenzen derselben Geometrie bleiben vollständig erhalten;
mehrdeutige Originalauswahl muss zuerst aufgelöst werden.

Im Bearbeitungsmenü entfallen Schritt bearbeiten, Schrittvorgaben bearbeiten
sowie die getrennten Erstellen-/Kopieren-/Verschieben-Einträge. Doppelklick/F2
und Zeilenauswahl bleiben. Profilaktualisierung und freier G-Code sind unter
„Erweitert“ gebündelt. Das Canvas behält seine sonstigen Aktionsgruppen und
Trennlinien; Toolbar-Erstellen bleibt für den bisherigen Erstellungsablauf.
Gemischter Transfer/Erstzuordnung wird als eine Transaktion ausgeführt:
Abbruch/Ablehnung ohne Änderung, ein gemeinsamer Undo-Schritt, stabile Redo-IDs,
Originalgeometrie unverändert und eigene Werte/Zielvererbung erhalten.

Nachweis: je 26 fokussierte Befehls-/Paneltests unter Qt5 und Qt6 bestanden;
nach abschließender Textkorrektur die beiden Paneltests je Bindung erneut.
Prüft bestehende/neue Ziele, Kopieren/Verschieben, dynamische Feldsichtbarkeit,
Abbruch, Undo/Redo, gemischte Zuordnung mit atomarer Ablehnung, ausdrückliche
Mehrfachreferenzen, Canvas-Aktionsanbindung, Menübereinigung und Doppelklick.
DE/FR/RU ergänzt, QM-Dateien regeneriert und Übersetzungen geprüft. Deutsche
Dialogdarstellung nativ kontrolliert. Strenger Dokumentationsbuild und
Diff-Prüfung bestanden. Keine Vollsuite, Paket-, Debian- oder Maschinenabnahme;
praktische Abnahme im eigenen Projektablauf bleibt P8.

## R3: nicht ausgewählte Bearbeitungsbahnen gestrichelt (08.11.2026)

Nicht ausgewählte Bahnen sind zusätzlich zu 0,6 Pixel Strichstärke gestrichelt.
Die Originalkontur bleibt regulär durchgezogen, bei Teilauswahl gepunktet mit
k/n; vorhandene Deaktivierungsdarstellung bleibt erhalten. Ausgewählte und
aktive/Hover-Bahnen behalten ihre bisherigen Linienarten und Farben. Die zwei
fokussierten Qt5-Paneltests und Diff-Prüfung bestanden.

## R3: nicht ausgewählte Bearbeitungen dünner zeichnen (08.11.2026)

Nicht ausgewählte Bearbeitungsbahnen und ihre Markierungsumrisse verwenden
0,6 Pixel Strichstärke. Ausgewählte Bearbeitungen, aktive/Hover-Hervorhebung,
Farben und Linienarten bleiben erhalten. Die beiden fokussierten Qt5-Paneltests
und Diff-Prüfung bestanden. Keine Änderung an Geometrie, Planung oder Export.

## R3: Kontextzeile zwischen Baum und Parametern entfernt (08.11.2026)

Die zusätzliche Zeile „Schrittvorgaben: …“ beziehungsweise „Aktiv: …“ entfällt.
Der Parameterbereich beginnt unmittelbar unter dem Baumtrenner. Kontext- und
Sperrhinweise bleiben als Tooltip der Parameterfläche beziehungsweise des
Werkzeugfelds erreichbar. Vorhandene Übersetzungen werden weiterverwendet.
Die beiden fokussierten Qt5-Paneltests und Diff-Prüfung bestanden; keine
Änderung an Auswahl-, Parameter- oder Exportlogik.

## R3: gemeinsame Parameterbearbeitung und eindeutige Auswahl (08.11.2026)

Mehrfachauswahl ist wieder gemeinsam editierbar: gleiche geerbte Werte grau,
gleiche Werte mit eigenen Overrides normal, unterschiedliche Werte als
editierbarer Platzhalter. Maßgeblich sind ungerundete Werte und gespeicherte
Herkunft. Symbole unterscheiden eigene/geerbte/gemischte Herkunft und nennen
Zähler, Quellen sowie tatsächliche Werte. Dropdowns zeigen gemischte Werte
ausdrücklich; nicht für alle anwendbare Felder bleiben einzeln gesperrt.

Eine Eingabe ändert nur diesen Parameter aller ausgewählten Zuordnungen;
Rücksetzen entfernt deren Overrides zugunsten individueller Schrittvorgaben.
Platzhalter/Fokuswechsel/unveränderte Bestätigungen schreiben nichts. Volle
Zahlengenauigkeit bleibt erhalten. Gemeinsame Rückzugs-/Sicherheitsänderungen
werden einmal je betroffenem Schritt gesetzt und ihr größerer Wirkungsbereich
am Symbol erläutert. Start-X/Y lässt die jeweils andere Koordinate individuell.
Jede Sammelaktion ist ein Undo-Schritt; Auswahl und Werkzeugdefinitionen bleiben.

Eindeutige Originalkonturen können direkt gemeinsam editiert werden. Bei
Originalgeometrie mit Mehrfachverknüpfungen bleiben auch Werkzeugwechsel
gesperrt, bis die gewünschten Zuordnungen ausdrücklich im Baum oder Canvas
gewählt wurden. Die aktive Bearbeitung hebt nur die Vorschau hervor; die
Parameter gelten bei Mehrfachauswahl für die gesamte Auswahl.

Nachweis: je 25 fokussierte Befehls-/Paneltests unter Qt5 und Qt6 bestanden.
Geprüft sind Sammeländerung, Reset, Undo/Redo, unveränderte Bestätigungen,
Präzision, gemischte Herkunft, beide Auswahlwege, gemeinsame Schrittwerte,
Startkoordinaten und atomare Ablehnung ungültiger Batches. DE/FR/RU ergänzt,
QM-Dateien regeneriert und Übersetzungen geprüft. Deutsche Windows-Darstellung
visuell kontrolliert; strenger Dokumentationsbuild und Diff-Prüfung bestanden.
Keine Vollsuite, Paket-, Debian- oder Maschinenabnahme; praktische Abnahme P8
bleibt offen.

## R3: Bearbeitung als Startansicht (08.11.2026)

Das Hauptfenster öffnet standardmäßig den Tab „Bearbeitung“, nachdem beide
Tabgruppen aufgebaut wurden. Ein späterer manueller Tabwechsel bleibt erhalten;
das Laden einer Zeichnung erzwingt keinen erneuten Wechsel. Bestehender lokaler
Qt5-Panelablauf mit echtem Hauptfenster bestanden. Keine
neuen GUI-Texte oder Formatänderungen.

## R3: verständliche Konturlabels und gebündelte Rahmenauswahl (08.11.2026)

Canvas-Beschriftungen verwenden jetzt Schrittname, dieselbe Konturnummer wie
im Bearbeitungsbaum und Werkzeug, beispielsweise „7 · Kontur 0 · T5“. Die
zusätzliche ab eins laufende Schritt-/Zuordnungsposition entfällt; bestehende
DE/FR/RU-Übersetzungen für „Kontur“ werden wiederverwendet.

Ursache der trägen Mehrfachauswahl: Die 2D-Rahmenauswahl meldete jeden
einzelnen Auswahl-/Abwahlwechsel an die Bäume. Jeder Callback berechnete die
gesamte Bearbeitungsvorschau neu. Die Auswahl wird jetzt vollständig gesetzt
und anschließend einmal gemeinsam gemeldet. Keine über Bearbeitungsänderungen
hinweg gespeicherten Werkzeugpläne und keine Änderung an Exportreihenfolge
oder Exportroutenbedienung.

Lokale Profilierung mit `dxf/1997.DXF`: sechs Konturen, sechs auf eine
Vorschau-Aktualisierung; einschließlich Ereignisverarbeitung etwa 0,617 auf
0,117 Sekunden. Das sind Vergleichswerte dieses Laufs unter Qt5/offscreen mit
Profilierungsaufwand, keine garantierte Reaktionszeit anderer Systeme.
Je sieben fokussierte echte Qt-Ereignis-/Paneltests unter Qt5 und Qt6 bestanden:
Rahmenauswahl und gemeinsames Leeren melden genau einen vollständigen Zustand,
Labels stimmen mit dem Baum überein, bestehende Auswahl-/Undo-/Exportabläufe
und Übersetzungen bleiben geprüft. Dokumentationsbuild und Diff-Prüfung
bestanden. Praktische Bedienabnahme bleibt P8; keine Vollsuite oder Paketabnahme.

## R3: fehlende G40-Einfahrt in gemeinsamem Plan korrigiert (08.11.2026)

Die Einfahrgeometrie für G40 wurde korrekt vorbereitet, aber die Konturstrategie
übernahm sie nur bei interner Werkzeugradiuskorrektur in den Werkzeugplan.
Bei normalem G40 fehlten Gerade und Bogen damit sowohl in der Vorschau als
auch im G-Code. Die G40-Verzweigung übernimmt jetzt auch diese vorbereitete
Einfahrt nach dem Eintauchen und vor dem ersten Konturschnitt. „Aus“ bleibt
ohne Einfahrt; Ausfahrt sowie G41/G42 behalten ihr Verhalten.

Regression zuerst mit zwölf fehlgeschlagenen Unterfällen reproduziert, danach
bestanden: offene/geschlossene Konturen, beide Kompensationskonfigurationen und
Aus/Gerade/Radius/Startbewegung. Prüft Planreihenfolge, 2D-/3D-Projektion,
2D-Leadpfad sowie erste tatsächlich exportierte XY-Bewegung und Bogenbefehle.
Je 64 fokussierte Vorschau-/Leadmodus-/Golden-Tests und zwei Paneltests unter
Qt5 und Qt6 bestanden. Strenger Dokumentationsbuild und Diff-Prüfung bestanden.
Kein vollständiger Testlauf, keine Controller-/Maschinenabnahme. Bestehende
G-Code-Dateien bleiben unverändert; zur Übernahme erneut exportieren und prüfen.

## R3: gemeinsame Parameterfläche mit vier Group Boxes (08.11.2026)

Nach erneuter Nutzerpräzisierung entfällt der innere Werkzeug-/Konturtrenner
einschließlich separater Klapp-/Scrollbereiche. Der Trenner zwischen Baum und
dem gesamten Eingabebereich bleibt. Ein gemeinsamer Scrollbereich zeigt
Werkzeugauswahl/Drehzahl sowie Z-Werte, Vorschübe, Lead in/out und Offset in
normalen Group Boxes. Jeweils zwei Werte stehen nebeneinander; kurze Labels
tragen die Einheit direkt. Herkunftssymbole folgen mit 2 Pixel Abstand auf das
Feld, zusätzlicher Leerraum erst danach. Maschinenfilter, Vererbung, volle
Zahlengenauigkeit und Befehlsverlauf bleiben erhalten. Alte gespeicherte innere
Trenner-/Klappzustände werden ignoriert; äußere Größen bleiben gespeichert.

Nachweis: je zwei fokussierte Paneltests unter Qt5 und Qt6 bestanden, mit
echten Auswahl-/Bearbeitungs-/Undo-/Exportabläufen, Vererbung, Maschinenfiltern,
Zahlenpräzision, zwei Werten je Zeile und direkt angrenzenden Symbolen bei
breiter und schmaler Ansicht. DE/FR/RU ergänzt und QM-Dateien regeneriert;
Übersetzungen geprüft. Deutsche Windows-Darstellung visuell kontrolliert.
Strenger Dokumentationsbuild und Diff-Prüfung bestanden. Keine Vollsuite,
Paket-, Debian- oder Maschinenabnahme; praktische Bedienabnahme bleibt P8.

<a id="r3-preview-layout"></a>

## R3: Mehrfachvorschau, Canvas-Auswahl und korrigiertes Formular (08.11.2026)

Originalauswahl stellt alle verknüpften Bearbeitungspläne mit tatsächlichen
Leads, Start/Ende und Tiefen dar. Direkte Pfad-/Labelauswahl, Strg-Umschaltung,
Treffermenü bei Überlagerung und Hover-Hilfe synchronisieren Baum und Canvas.
Eine aktive Bearbeitung zeigt ihre Parameter; Werkzeugwechsel wirken auf die
gesamte markierte Auswahl. Teilauswahl punktiert die Originalkontur mit k/n.
Die zunächst zusätzlich eingeführten Schrittfarben wurden nach Nutzerkorrektur
entfernt: bestehende semantische Bewegungsfarben bleiben, Hervorhebung nutzt
Strichstärke. Keine künstlichen Bahnverschiebungen oder automatische Exportroute.

Der reproduzierte 2D-Versatz entstand durch Qt-Scrolling von Viewport-Kindern:
Das Overlay wurde zusätzlich zur bereits umgerechneten Zeichenposition bewegt.
`scrollContentsBy` verankert es wieder im Viewport; die Abbildung verwendet die
gleiche Fließkommatransformation wie die Szene. G40 ohne Zusatz-Offset ist am
Originalpfad geprüft; berechnete Kompensationsabstände bleiben unverändert.

Drehzahl, Leads, Überfahrt und gegebenenfalls ein expliziter abweichender
Alt-Startradius stehen ausschließlich im Konturbereich. Die Werkzeuggruppe
zeigt die Auswahl samt Durchmesser. Alle Werte bleiben untereinander in
ausgerichteten Gruppen, mit kurzen Zahlenfeldern und eigenen Herkunftssymbolen.
Messerparameter nur bei Dragknife; Standard-Fräsleads/Überfahrt nicht bei Drehen
oder Dragknife. Der Filter umfasst ganze Zeilen. R3-ROWS ist damit erledigt.

Fenstervergrößerung hält linke Breite und untere Meldungshöhe konstant. Im
Bearbeitungstab wächst der Baum statt des Parameterbereichs. QSettings merkt
manuelle Trennergrößen und Klappzustände; Mindestmaße schützen den Canvas.

Nachweis: je 20 fokussierte Panel-/Canvas-/3D-Tests unter Qt5 und Qt6 bestanden.
Darunter echte Qt-Auswahl-/Scrollereignisse, G40-Koordinaten, bestehende Farben,
gestapelte Spalten bei breiter/schmaler Ansicht, Maschinenfilter, unveränderte
Projektwerte sowie Speichern/Wiederherstellen der Fensteraufteilung. DE/FR/RU
ergänzt, QM-Dateien erzeugt und Übersetzungen geprüft. Deutsche native Windows-
Ansicht visuell kontrolliert. Strenger Dokumentationsbuild und `git diff --check`
bestanden. Die 3D-Projektionsmathematik und Zeichenbefehle
sind geprüft; reale GPU-/Treiberdarstellung bleibt Teil von P8. Keine Vollsuite,
Paket-, Debian- oder Maschinenabnahme. Nutzeraufgaben stehen im
[P8-Prüfablauf](planning/r3-r1b-implementation-plan.md#r3-ui-user-check).

## R3: bündige Eingabespalten und getrennte Tooltips (08.11.2026)

Die kompakten Zeilen verwenden gemeinsame Unterbeschriftungs-, Eingabe- und
Symbolspalten über beide Parametergruppen. Erste und zweite Eingabefelder
stehen jeweils bündig; auch die Werkzeugauswahl beginnt an der ersten
Eingabespalte. Zahlenfelder sind auf ungefähr acht Zeichen plus Rahmen
begrenzt, Dropdowns dürfen breiter sein. Bei Platzmangel wechseln alle
Wertepaare gemeinsam auf zwei Zeilen. Lange Eingaben bleiben per Textscrollen
vollständig editierbar; die Modellwerte werden nicht gerundet oder geändert.

Feld-Tooltips erklären ausschließlich die Parameterfunktion. Herkunft steht
nur am Symbol: Parametername, eigener Konturwert samt Kontur/Schritt oder
eigener Schrittwert beziehungsweise geerbte Quelle aus Schritt/Werkzeug/
Projektvorgabe und der wirksame Wert. DE/FR/RU-Texte und QM-Dateien ergänzt.

Nachweis: je zwei Paneltests unter Qt5/Qt6 bestanden, einschließlich exakter
Spaltenpositionen bei breiter/schmaler Darstellung, kollektivem Umbruch,
Zahlenfeldbreite und getrennter Feld-/Symbolhilfe. Die fünf Zahlenanzeigetests
je Bindung bestanden ebenfalls; nach der abschließenden Layoutanpassung wurden
die betroffenen Paneltests erneut geprüft. Deutsche Windows-Darstellung
visuell kontrolliert. Keine Vollsuite oder Paketabnahme.

## R3: kompakte und responsive Parameterpaare (08.11.2026)

Gemäß Nutzerfreigabe sind Zahlenfelder schriftabhängig schmaler und verwandte
Werte in gemeinsamen Zeilen angeordnet: Vorschub XY/Z, Einfahrt/Ausfahrt,
Zustellung/Endtiefe und Rückzug/Sicherheit; beim Werkzeug Radius/Gerade.
Werkzeugauswahl, Drehzahl, Überfahrlänge, Werkstückoberfläche, Zusatz-Offset und
Überfahrtwahl bleiben separat. Der Durchmesser steht nur noch in der
Werkzeugauswahl. Jeder Wert behält seinen eigenen Herkunftsknopf und die
bestehenden Eingabeschnittstellen. Kurze Labels erhalten erklärende Tooltips.

`CompactFields` stellt Paare bei genügend Breite nebeneinander, sonst
untereinander dar. Die vorhandenen Widgets werden umgeordnet, nicht ihre Werte.
Zahlenfelder erlauben weiter vollständige Eingaben mit horizontalem Textscrollen.
Beschriftungen erhalten bei Umbruch ausreichend Höhe; Einheiten bleiben zusammen.
Optionale versteckte Felder halten keine leeren Wertecontainer offen.

Nachweis: je sieben fokussierte Panel-/Zahlenanzeigetests unter Qt5 und Qt6
bestanden. Geprüft sind breite/schmale Anordnung, sichtbare feste Herkunftsknöpfe,
beschriftungsabhängige Höhe, Wegfall der Durchmesserzeile, unveränderte
Projektwerte beim Skalieren und bestehende Eingabe-/Undo-/Exportabläufe.
DE/FR/RU ergänzt, QM-Dateien regeneriert und GUI-Übersetzungen geprüft.
Die deutsche Darstellung wurde nativ unter Windows visuell kontrolliert.
Keine Vollsuite, Paket-/Debian- oder Maschinenabnahme.

## R3: Auswahl beim Umordnen von Schritten erhalten (08.11.2026)

`reorder_steps` übernahm fälschlich die gesamte neue Schrittfolge als Auswahl.
Pfeil- und Drop-Aktionen übergeben jetzt die tatsächlich verschobenen Schritte;
ohne ausdrückliche Angabe behält der Befehl seine vorherige Auswahl. Beim
Neuaufbau des Baums wird außerdem die aktuelle ausgewählte Zeile mit
`NoUpdate` wiederhergestellt, ohne zusätzliche Zeilen zu markieren.

Nachweis: je zwei Paneltests unter Qt5/Qt6 bestanden. Echte Pfeilaktionen nach
oben/unten, Schritt-Drop und Undo/Redo behalten genau die ausgewählte
Schritt-ID und die aktuelle Zeile; Reihenfolge und Projekt-Roundtrip bleiben
geprüft. Keine neuen GUI-Texte, keine Vollsuite oder Paketabnahme.

## R3: leere Haltestegzeile zwischen Tiefe und Vorschub entfernen (08.11.2026)

Die optionale Zeile „Haltestege ab Durchgang bearbeiten“ wurde ohne aktive
Haltestege bereits ausgeblendet, ihr Herkunftsknopf jedoch nicht. Dieser hielt
die Zeile zwischen Frästiefe und XY-Vorschub offen. Der Herkunftsknopf folgt jetzt
derselben Sichtbarkeitsentscheidung wie Beschriftung und Auswahlfeld, sowohl bei
der Erstellung als auch beim Aktualisieren. Die Haltestegfunktion bleibt erhalten.

Nachweis: je zwei Paneltests unter Qt5/Qt6 bestanden; sichtbare/ausgeblendete
Haltestegzeile einschließlich Herkunftsknopf, zusammenfallender Abstand zwischen
Tiefe und Vorschub und unveränderte Projektwerte geprüft. Keine neuen GUI-Texte,
keine Vollsuite oder Paketabnahme. Der separat vorgemerkte Werkzeugformular-
Leerraum R3-ROWS bleibt offen.

## R3: Werkzeugwechsel einer Einzelkontur auf Auswahl begrenzen (08.11.2026)

Die bisherige Mehrfachauswahl-Korrektur ließ den Einzelkonturpfad unverändert;
dieser änderte weiterhin das Werkzeug des ganzen Schritts. Jetzt verwendet auch
eine einzelne aktive Bearbeitungskontur den auswahlbezogenen Werkzeugbefehl.
Enthält die Quelle weitere Einträge, wird nur die Kontur in einen neuen Schritt
gleichen Typs und mit vollständig kopierten Quellvorgaben verschoben. Eigene
Konturwerte und IDs bleiben unverändert. Ein vollständig gewählter Schritt
bleibt bestehen. Die ausdrücklich gewählte Schrittzeile und der explizite
Profilaktualisierungsbefehl behalten ihre schritt-/definitionsweite Wirkung;
die Werkzeug-Tooltips unterscheiden die Kontexte.

Nachweis: je zwei Paneltests unter Qt5 und Qt6 bestanden. Echte Listenaktivierung
mit einer beziehungsweise mehreren ausgewählten Konturen prüft vollständigen
Werterhalt der Zuordnungen, Quellvorgaben, ungewählte Konturen und Undo/Redo
einschließlich stabiler IDs. Keine neuen Übersetzungstexte oder Vollsuite.

## R3: Werkzeugwechsel für mehrere ausgewählte Konturen (08.11.2026)

Die Werkzeugauswahl bleibt bei mehreren ausgewählten Bearbeitungszuordnungen
bedienbar. Gemäß Nutzerentscheidung betrifft der Wechsel nur die Auswahl:
vollständig ausgewählte Schritte behalten ihre Identität und bekommen das neue
Werkzeug; Teilauswahlen erhalten unmittelbar hinter ihrem Quellschritt einen
neuen Schritt gleicher Art und mit denselben Vorgaben. Kontur- und Geometrie-IDs,
eigene Werte, Start/Richtung, Export- und Optimierungsflags bleiben erhalten.
Mehrere Quellen werden getrennt behandelt. Die gesamte Aktion ist atomar und
bildet einen Undo-/Redo-Schritt. Nicht ausgewählte Zuordnungen und andere
Benutzer derselben Werkzeugdefinition bleiben unverändert.

Bei gemischten Werkzeugen zeigt die Auswahl einen entsprechenden Platzhalter.
Die übrigen Parameterfelder bleiben bei Mehrfachauswahl gesperrt, damit kein
beliebiger Einzelwert als gemeinsamer Wert erscheint. Die ausdrücklich
ausgewählte einzelne Schrittzeile verwendet weiterhin den Vorgabeneditor.
Einzelkontur-/Schrittauswahl und der dort vereinbarte gemeinsame Ersatz einer
Projektwerkzeugdefinition bleiben unverändert.

Nachweis: 21 Befehlsregressionen unter Qt5 sowie je zwei Paneltests unter Qt5
und Qt6 bestanden. Enthalten sind echte Werkzeuglisten-Aktivierung mit Teil-/
Gesamtauswahl, mehrere Quellschritte, eigene Werte/Vorgaben, stabile Undo-/Redo-IDs
und atomarer Abbruch bei fremden beziehungsweise unpassenden Zuordnungen.
DE/FR/RU einschließlich QM-Dateien aktualisiert und im GUI-Workflow geprüft.
Keine Vollsuite, Paket-/Debian- oder Maschinenabnahme.

## Hauptfenster: Meldungsausgabe per Trenner skalieren (08.11.2026)

Ein vertikaler Splitter trennt jetzt Zeichen-/Bearbeitungsbereich und zentrale
Meldungsausgabe. Der sechs Pixel breite Griff oberhalb der Ausgabe lässt sich
ziehen; die frühere feste Begrenzung auf 100 Pixel entfällt. Anfangshöhe etwa
100 Pixel, Mindesthöhe 48 Pixel; die Bereiche klappen beim Ziehen nicht vollständig
zu. Der Meldungsinhalt bleibt erhalten. MessageBox berücksichtigt nun ihren
übergebenen Qt-Elternknoten. Die UI-Quelle wurde geändert und die lokalen
Qt5-/Qt6-Module neu erzeugt; generierte Dateien bleiben ignoriert.

Nachweis: je zwei fokussierte Paneltests unter Qt5 und Qt6 bestanden,
einschließlich echter Mausereignisse am neuen Splittergriff, erhaltener
Meldungsausgabe und unverändertem Projekt/Befehlsverlauf. Keine neuen GUI-Texte,
keine Vollsuite oder Paketabnahme.

## R3: Änderungsdetails in der zentralen Meldungsausgabe (08.11.2026)

Die separate Meldungsfläche unter den Bearbeitungsfeldern wurde entfernt.
Vorliegende Änderungsdetails laufen als INFO über den vorhandenen Fensterlogger
in die Meldungsausgabe unten im Hauptfenster; Warnungen und abgelehnte Aktionen
verwenden WARNING am selben Ort. Der allgemeine Hinweis „Bearbeitung geändert.
Rückgängig ist verfügbar.“ entfällt. Die aktivierten/deaktivierten
Historienknöpfe zeigen die verfügbaren Aktionen weiterhin an.

Nachweis: je zwei fokussierte Panel-/Übersetzungstests unter Qt5 und Qt6
bestanden. Ein echter Werkzeugwechsel der Projektdefinition schreibt seine
Wertänderung über einen StreamHandler in die vorhandene MessageBox; eine
abgelehnte Aktion meldet dort den Grund und erhält den Projektzustand.
Rückgängig stellt den Projektstand wieder her. Keine neue GUI-Beschriftung,
keine Vollsuite oder Paketabnahme.

## Konfiguration: kompakte Zahlenfelder ohne Pfeiltasten (08.11.2026)

Die Zahlenfelder der Konfiguration und Werkzeugtabelle zeigen keine
Hoch-/Runter-Knöpfe mehr; direkte Eingabe, Validierung und vollständige
Speichergenauigkeit bleiben erhalten. Die Formularfelder können zwischen
80 und 160 Pixeln liegen. Die interne Double-Präzision von 323 Stellen bestimmt
nicht mehr die bevorzugte Feldbreite. Die Werkzeugspalten teilen sich die
verfügbare Tabellenbreite; lange technische Spaltennamen werden umgebrochen.
Die anfängliche Dialogaufteilung wird nach der Layoutberechnung gesetzt und
Abschnittsüberschriften können umbrechen. Der Layout-Timer gehört dem Dialog
und wird bei dessen Zerstörung mit entfernt.

Nachweis: sechs Konfigurations-/Übersetzungstests sowie zwölf Zahlenanzeige-/
Präzisionstests je Qt5/Qt6 bestanden; nach der abschließenden Headeranpassung
den betroffenen Layouttest je Bindung erneut bestanden. Standardbreite 1000,
schmalere bestehende Prüffälle und DE/FR/RU/Englisch berücksichtigt. Alle Seiten
und die Werkzeugtabelle passen bei Standardgröße ohne horizontales Scrollen;
unter nativem Windows visuell bestätigt. Keine neuen GUI-Texte, keine erneute
QM-Erzeugung erforderlich. Keine Vollsuite oder Paket-/Plattformabnahme.

## R3: gebogene Pfeile für Rückgängig/Wiederherstellen (08.11.2026)

Die Navigationswinkel im Bearbeitungstab sind durch gespiegelte gebogene
Pfeile ersetzt: links Rückgängig, rechts Wiederherstellen. Vektorpfade werden
für mehrere Symbolgrößen und aktive/deaktivierte Palettenfarben gerendert.
Tooltips zeigen Aktionsname und natives Tastenkürzel für Ctrl+Z beziehungsweise
Ctrl+Shift+Z. Die bisherigen Tastaturaktionen und die Deaktivierung bei leerer
Historie bleiben erhalten. DE/FR/RU-Beschriftungen vereinheitlicht und QM-Dateien
regeneriert. Je zwei bestehende Panel-/Übersetzungstests unter Qt5 und Qt6
bestanden; aktive und ausgegraute Symbole visuell geprüft. Keine Paketabnahme.

## R3-TOOLS: Exportsperre bei Werkzeugkonflikten (08.11.2026)

Gemäß ergänzender Nutzerentscheidung prüft der gemeinsame Exportweg nur die
Werkzeuge aktivierter Bearbeitungen gegen die aktuelle Werkzeugtabelle.
Abweichende Definitionen und vollständig fehlende Nummern sperren den gesamten
Export vor der Ausgabe. Leere, vollständig deaktivierte, ignorierte und reine
Steg-Schritte bleiben ausgenommen. Die Vorschau und gespeicherte Projektwerte
bleiben nutzbar. Die DE/FR/RU-Diagnose nennt Nummer, Schritte und die gespeicherten
Werte beziehungsweise die Projekt-/Tabellenunterschiede; sie schlägt ausdrücklich
Anlegen/Korrigieren in der Werkzeugtabelle oder Zuweisen eines vorhandenen
Werkzeugs vor. Es erfolgt kein automatisches Anlegen oder Ersetzen.

Der gleiche Abgleich gilt für GUI, CLI und historische Projektdateien.
Vorhandene Zieldateien werden bei einer Sperre nicht geöffnet oder überschrieben;
stdout bleibt leer. Die tatsächliche Einheit der geladenen Tabellenwerte wird
berücksichtigt; gerundete Anzeigeübereinstimmung genügt nicht. Die zuvor
erlaubten unterschiedlichen gespeicherten Definitionen bleiben erhalten,
müssen vor ihrer Verwendung aber mit der Tabelle abgeglichen werden.

Nachweis: sechs fokussierte Policy-/Postprozessor-/Übersetzungstests jeweils
unter Qt5 und Qt6 bestanden; zusätzlich zwei Paneltests je Bindung mit echtem
GUI-Exportabbruch, erhaltener Datei und erfolgreichem Export nach Korrektur.
26 Projektregressionen unter Qt5 bestanden, einschließlich erfolgreichem
CLI-Export und echtem CLI-Abbruch mit fehlendem T99 für neue und historische
Dateien. Vollständige Wertvergleiche, mm/inch, aktive/gemischte Aufträge und
ausgenommene Schritte sind abgedeckt. DE/FR/RU-QM-Dateien regeneriert und ihre
Diagnosen im Qt-Übersetzungssystem geprüft. Keine Vollsuite, Debian-, Paket-
oder Maschinenabnahme. Die praktische Nutzerabnahme bleibt Teil von P8.

<a id="r3-tools"></a>

## R3-TOOLS: gemeinsame Werkzeugliste und geteilter Ersatz (07.11.2026)

Die anschließende Nutzerentscheidung ersetzt die unten dokumentierte
Gruppierung: eine gemeinsame Liste ohne getrennte Projekt-/Tabellengruppen.
Vollständig gleiche Definitionen erscheinen einmal; beim Laden werden gleiche
Projektdefinitionen zusammengeführt. Der Vergleich verwendet Nummer und alle
ungerundeten Werkzeugwerte nach Einheitenumrechnung. Abweichende Definitionen
bleiben mit Herkunft und abweichenden Werten erkennbar. Beim Ersatz einer
Projektabweichung durch die passende Tabellendefinition wechseln alle Schritte
mit dieser Projektdefinition gemeinsam; andere Definitionen derselben Nummer
bleiben erhalten. Der Wechsel zu einer anderen Nummer betrifft nur den
ausgewählten Schritt. Gemeinsamer Ersatz, Zusammenführung und die übrigen
Dialogänderungen bilden eine atomare Undo-Aktion. Explizite Konturwerte bleiben
erhalten; spätere Tabellenänderungen werden nicht automatisch übernommen.

Nachweis: 47 fokussierte Modell-/Befehls-/Paneltests unter PyQt5 und zwei
Paneltests unter PyQt6 bestanden. Abgedeckt sind vollständige Gleichheit gegen
kleine ungerundete Unterschiede, mm/inch, gemeinsame Benutzer versus separate
Definitionen derselben Nummer, Zusammenführung mit bereits vorhandenem Ziel,
GUI-Auswahl, Undo/Redo, Roundtrip und atomarer Abbruch bei ungültiger
Bearbeitungsart. DE/FR/RU und QM-Dateien aktualisiert. Keine Vollsuite,
Paket-/Debian- oder Maschinenabnahme; R3-ROWS und R3-IGNORE bleiben offen.

## R3-TOOLS: verständliche Werkzeugauswahl (07.11.2026)

Werkzeugfeld und Schrittdialog verwenden dieselbe Auswahlliste mit nicht
auswählbaren Überschriften „Projektwerkzeuge“ und „Werkzeugtabelle“.
Einträge zeigen T-Nummer, Durchmesser und Projekteinheit statt interner
Reihenfolgezusätze wie `#1`. Bei gleicher Nummer unterscheiden zusätzliche
Angaben die gespeicherten Drehzahl-/Einfahrwerte; verdeckt die Anzeigepräzision
einen Unterschied, wird der betreffende Wert vollständig angezeigt.
Tooltips zeigen die weiteren Werkzeugdaten und erklären die Übernahme aus der
Tabelle. Projektwerte, erlaubte unterschiedliche Definitionen derselben Nummer
und der bisherige Werkzeugwechselvertrag bleiben erhalten.

Nachweis: jeweils zwei fokussierte Paneltests unter PyQt5 und PyQt6 bestanden,
einschließlich mm/inch, nahezu gleicher Definitionen, nicht auswählbarer
Gruppentitel, Schrittdialog, realer Auswahl/Übernahme von T10 und Undo ohne
Änderung der Originallayer-Werkzeuge. DE/FR/RU ergänzt, QM-Dateien regeneriert
und im Qt-Workflow gegen die Katalogtexte geprüft. `git diff --check` bestanden.
Keine vollständige Suite, Paket-/Debian- oder Maschinenabnahme. Der mögliche
Formularleerraum R3-ROWS bleibt eine gesonderte offene Aufgabe.

## R3: Bearbeitungsart „Ignoriert“ untersucht (07.11.2026)

Quellcode und ein lokaler Modell-/Befehlsversuch bestätigen die bestehende
Ausschlusswirkung für `IGNORE:`-Importe: Die projizierte Kontur bleibt unabhängig
vom gespeicherten Aktivierungsflag deaktiviert; ihre Exportreihenfolge ist leer.
Ein neuer leerer `ignored`-Schritt ist zulässig, das Verschieben einer normalen
Kontur dorthin wird jedoch atomar abgelehnt. Der Dialog und die Exportcheckbox
stellen diesen Sonderstatus derzeit nicht eindeutig dar. Keine Quellcodeänderung,
keine neue vollständige Export-, GUI-, Paket- oder Maschinenabnahme.
Die [Bedienentscheidung R3-IGNORE](planning/r3-r1b-implementation-plan.md#r3-ui-followups)
bleibt offen; Werkzeugmenü und möglicher Formularleerraum sind dort ebenfalls
ausdrücklich für später vorgemerkt.

Dieses Dokument bewahrt abgeschlossene Implementierungen, deren dokumentierte
Prüfergebnisse und die historische Ausgangslage. Die
[aktive Todo](../todo.md) enthält die verbleibenden Aufgaben
in empfohlener Umsetzungsreihenfolge. Die Trennung ändert keinen fachlichen
Status und ist keine erneute Codeprüfung oder Testfreigabe.

Historische Testergebnisse gelten für den jeweils beschriebenen Stand.
Insbesondere liegen die Vollsuite-Ergebnisse mit 775 Tests vor der späteren
Darstellungskorrektur; diese wurde anschließend mit jeweils 21 gezielten
Tests unter Qt5 und Qt6 abgesichert. Daraus folgt keine neue Paketabnahme.

## Qt6 – Konfigurationsfehler beim Start anzeigen (07.11.2026)

Die drei kritischen Fehlerdialoge in `presentation/qt/application.py` nutzen
`QMessageBox.Icon.Critical`, das unter PyQt5 und PyQt6 verfügbar ist. Dadurch
verdeckt unter Qt6 kein `AttributeError` mehr die eigentliche Meldung über eine
inkompatible Konfigurationsversion; die Konfiguration wird weiterhin abgelehnt.

**Prüfung:** `dxf2gcode_startup_error_test.py` bestand mit jeweils zwei Tests
unter lokalem PyQt5 und PyQt6 (`.tox/package-build`). Der GUI-Startpfad erzeugt
eine echte QMessageBox; geprüft werden Icon, Titel, Fehlertext und Beenden.
Der Quiet-Startpfad beendet ohne Dialog mit Fehlercode 2. Die Tests ersetzen
die Konfiguration und schließen den Dialog ohne interaktive Bedienung.
Keine Vollsuite, Paket-/Debian- oder Maschinenabnahme; GUI-Texte unverändert.

## R3/R1b: Arbeiten auf Feature-Zweig isoliert (07.11.2026)

Auf Nutzerauftrag wurde `maschining-project` bei `5415018`
(`feat(core): introduce project-owned machining operations`) angelegt und
als aktiver Zweig ausgecheckt. Anschließend wurde ausschließlich der lokale
`develop`-Zeiger auf dessen Vorgänger `4346709` gesetzt. Dieser entspricht dem
live per `ls-remote` geprüften GitHub-Stand. Es war kein Umschreiben eines
veröffentlichten Commits und kein Remote-Push erforderlich.

Alle 53 zuvor geänderten/unversionierten Pfade blieben erhalten; vor/nach der
Trennung stimmen Statusliste und SHA256 des vollständigen getrackten Diffs
überein. `develop...origin/develop` ist `0/0`. Der aktuelle Arbeitsstand bleibt
uncommittet auf dem aktiven Feature-Zweig; dieser ist bislang nur lokal.
Plan und Abschlussnotiz halten den zukünftigen Arbeitszweig fest. Keine
Quellcodeänderung, deshalb kein Testlauf oder Build für die Branch-Trennung.

## R3: Gruppenhöhe auf tatsächlichen Inhalt begrenzen (07.11.2026)

Die Nutzerpräzisierung zu D33 begrenzt geöffnete Parametergruppen auf ihre
vollständige Inhaltshöhe. Die nächste Überschrift folgt direkt darunter;
überschüssiger Platz bleibt unter den Gruppen. `ParameterSplitter` verwendet
die Inhaltsgrenzen als bevorzugte Gesamthöhe. `ParameterSection` berechnet
die Obergrenze bei Auswahl- und Breitenänderungen neu. Ein Verkleinern per
Trenner mit Scrollen bleibt möglich. Das gilt auch ohne aktive Bearbeitung.

**Nachweis:** je **2 Paneltests unter Qt5 und Qt6** bestanden. Geprüft sind
beide Auswahlzustände mit großem freien Bereich, vollständige Werkzeugfelder,
direkt folgende Konturüberschrift, Größenbegrenzung, unveränderte Werte und
History sowie weiterhin bewegliche Trenner/Scrollbereiche. Native Windows-Qt-
Ansicht mit geöffneter Werkzeug- und eingeklappter Konturgruppe verdeckt
visuell geprüft. Keine neuen GUI-Texte. Strikter Dokumentationsbuild und
Diff-Prüfung ohne Fehler. Kein Commit/Push; `develop` unverändert.

## R3: Bereiche oben statt mittig ausrichten (07.11.2026)

Bei komplett eingeklappten Gruppen zentrierte das Layout den verkleinerten
Splitter im freien Bereich. Bearbeitungs- und Geometriegruppen werden in
diesem Zustand nun oben ausgerichtet; Leerraum bleibt darunter. Beim Öffnen
füllen die Splitter wieder die verfügbare Höhe. Auch die Formularlayouts
bleiben innerhalb großer Scrollbereiche oben ausgerichtet.

**Nachweis:** je **2 Paneltests plus 1 Baum-Bedientest unter Qt5 und Qt6**
bestanden. Geprüft sind Position und Abstand beider eingeklappten Überschriften,
oben bleibende Eingabefelder nach Vergrößerung, Geometriegruppen, Wiederöffnen
und weiterhin bewegliche Trenner. Der gemeldete Zustand wurde zusätzlich
mit nativer Windows-Qt-Darstellung verdeckt gerendert und visuell geprüft.
Keine neuen GUI-Texte. Strikter Dokumentationsbuild und Diff-Prüfung ohne
Fehler. Kein Commit/Push; Änderungen nur auf `maschining-project`.

## R3: verstellbare und einklappbare Bearbeitungsbereiche (07.11.2026)

D33 ergänzt im Bearbeitungstab einen vertikalen Splitter zwischen Baum und
Eingabebereich. Ein weiterer Splitter trennt Bearbeitungswerkzeug und
Konturwerte. Beide Gruppen haben Klapppfeile wie im Geometrie-Tab und eigene
Scrollbereiche. Die Überschriften bleiben beim Einklappen erreichbar;
Wiederöffnen stellt die vorherige Höhenverteilung her. Klappzustände bleiben
bei Auswahlwechsel/Refresh erhalten. Ohne aktive Bearbeitung sind die Werte
deaktiviert, die Überschriften bleiben bedienbar. Die bisherige kompakte
Zeilendichte und gleich ausgerichtete Spalten bleiben erhalten.

**Nachweis:** je **25 gezielte Tests unter Qt5 und Qt6** bestanden (Panel,
MainWindow, GUI-/CLI-Projektweg, Genauigkeit und Übersetzungen). Geprüft sind
echte Mausereignisse an beiden Splittergriffen, Ein-/Ausklappen einzeln und
gemeinsam, Wiederherstellung der Größen, Erhalt bei Refresh, Bedienbarkeit
ohne aktiven Arbeitsgang, scrollbare Inhalte und unveränderte Projektwerte/
History. Native Windows-Qt-Ansicht verdeckt gerendert und visuell geprüft.
Bestehende DE/FR/RU-Bereichstitel werden wiederverwendet, keine neuen Texte.
Strikter Dokumentationsbuild und Diff-Prüfung ohne Fehler. Nutzerprüfung auf
eigener Auflösung/Skalierung bleibt P8. Kein Commit/Push; `develop` unverändert.

## R3: kompakte Formularzeilen wiederhergestellt (07.11.2026)

Die Nutzerbeobachtung betrifft das Parameterformular: Beim Umbau waren
4 zusätzliche Pixel zwischen den Zeilen hinzugekommen. Dieser Abstand ist
wieder entfernt. Die Symbolknöpfe bleiben 32 Pixel breit, ihre Höhe folgt
dem zugehörigen Feld statt einer festen Höhe, die unter Qt6 zusätzliche
Zeilenhöhe verursachen konnte. Skalierbare Spalten und nötiger Textumbruch
bleiben erhalten; am Baum selbst wurde keine Zeilenhöhe geändert.

**Nachweis:** je **2 gezielte Paneltests unter Qt5 und Qt6** bestanden,
einschließlich tatsächlicher Zeilenzellabstände und schmaler/breiter Formulare.
Native Windows-Qt-Messung: Z-Eingabefelder jeweils 24 Pixel hoch; Abstand der
Feldanfänge von 28 auf 24 Pixel reduziert, wie in der ursprünglichen UI.
Gemessene Baumzeilen: Bearbeitung 22, Original-Layers 24 Pixel, somit keine
vergrößerten Baumzeilen. Strikter Dokumentationsbuild und Diff-Prüfung ohne
Fehler. Nutzerbildschirm/DPI bleibt Teil der Sichtprüfung P8. Kein Commit/Push.

## R3: vertraute Canvas-Kontextmenüstruktur (07.11.2026)

D32 setzt die Nutzerkorrektur anhand der beiden Screenshots um: Das Canvas-Menü
hat wieder die bisherigen Beschriftungen, Reihenfolge und Trennlinien zwischen
Nullpunkt, Auswahl, Richtung/Konturstart sowie Bearbeitungsarten/Kompensation.
„Bearbeitungsschritt erstellen …“ steht in einer getrennten Gruppe am Ende.
Der Canvas zeigt passende Pocket-/Bohraktionen; der zusätzliche Kontur-Eintrag
bleibt im Bearbeitungsbaum. Keine Änderung an `develop`; Arbeitszweig ist
`maschining-project`.

Auswahl aktivieren/deaktivieren sowie Richtung und nächster/schärfster
Konturstart sind wieder verfügbar und ändern atomar die aktiven Zuordnungen.
Die Startpunktalgorithmen laufen auf isolierten Bearbeitungsansichten;
gespeichert werden lokale Startkoordinaten und Richtung. Andere Referenzen
und Originalgeometrien bleiben erhalten. Die 3D-Auflösung verwendet je
Bearbeitung die effektive Werkstückoberfläche. Undo und manuelle Routenanzeige
bleiben erhalten. Nullpunkt bleibt unabhängig von der Auswahl verfügbar.

**Nachweis:** je **45 gezielte Tests unter Qt5 und Qt6** bestanden (Befehle,
Baum-/Canvas-Menüs, GUI-/CLI-Projektweg, MainWindow und Modusregeln). Geprüft
sind die konkrete Aktions-/Separatorenfolge, Aktivierung und Richtung einer
geteilten Kontur, Startpunktaktionen über echte QAction-Signale, lokale Starts
bei gedrehter/skalierten sowie offenen/geschlossenen Geometrien, Undo und
manuelle/live Routenanzeige. Deutsche native Windows-Qt-Menüansicht mit
`1997.DXF` verdeckt gerendert und visuell mit der bisherigen Struktur
verglichen. **14 bestehende Menütexte je DE/FR/RU** gegen fertige TS-Einträge
und geladene QM-Kataloge geprüft; neue Übersetzungstexte waren nicht nötig.
Strikter Dokumentationsbuild und Diff-Prüfung ohne Fehler. Kein Commit/Push,
keine zusätzliche Vollsuite-/Paket-/Debian-/Maschinenabnahme. Der praktische
Menüvergleich auf dem Nutzerbildschirm bleibt P8.

## R3: Nullpunkt ausschließlich im Canvas-Menü (07.11.2026)

D31 klärt den Nutzerbegriff: Gemeint ist der Werkstücknullpunkt. Der
missverständliche „Startpunkt“-Eintrag für den Bearbeitungsstart einer
Kontur ist aus dem Kontextmenü des Bearbeitungsbaums entfernt.
„Werkstücknullpunkt hierher …“ bleibt ausschließlich im Canvas-Menü und
ist bei geladener Zeichnung mit und ohne Konturauswahl verfügbar. Die
vorhandenen Nullpunkt-/Fangfunktionen bleiben bestehen. Konturstarts
werden dadurch nicht verändert.

**Nachweis:** je **3 gezielte Tests unter Qt5 und Qt6** bestanden
(Panel und Nullpunkt-Workflow). Nach zusätzlicher expliziter Assertion
für vorhandene Auswahl den **Nullpunkttest je Bindung** erneut bestanden.
Baummenü ohne Startpunkt, Canvas mit/ohne Auswahl, Dialog/Abbruch,
mm/inch und unveränderte Konturstarts sind abgedeckt. Bestehende übersetzte
Nullpunkt-Texte werden weiterverwendet. Strikter Dokumentationsbuild
und Diff-Prüfung ohne Fehler. Kein Commit/Push; P8 bleibt Nutzerabnahme.

## R3: Bearbeitungs-Kontextaktionen wiederhergestellt (07.11.2026)

D30 ist nach ausdrücklicher Nutzerentscheidung umgesetzt: Kontur,
Taschenfräsen, Bohren und G40/G41/G42 stehen im Bearbeitungsbaum und im
Canvas wieder bereit. Die Aktionen ändern ausgewählte Bearbeitungszuordnungen.
Bei Artwechsel entstehen neue Schritte unmittelbar nach dem jeweiligen
Quellschritt, mit dessen Werkzeugdefinition und Vorgaben. Arbeitsgang- und
Geometrie-IDs, eigene Werte, Start und Richtung bleiben erhalten. Andere
Bearbeitungen derselben Originalkontur bleiben unverändert. Mehrere
Quellschritte/Werkzeuge bleiben getrennt. Rückgängig stellt die gesamte Aktion
wieder her; Wiederherstellen erhält auch neue Schritt-IDs.

Bohren setzt bewusst G40. Kompensationswahl auf einer Bohrkreis-Zuordnung
kehrt zur Konturbearbeitung zurück. Ungültige Geometrie-/Maschinenkombinationen
werden ohne Teiländerungen abgelehnt. Mehrdeutige Canvas-Auswahl ohne aktive
Bearbeitung deaktiviert die Aktionen, statt willkürlich eine Referenz zu wählen.
Die fachlichen Konfliktregeln bleiben erhalten; keine Original-Shape-Mutation
über die alten Signalpfade.

**Nachweis:** je **43 gezielte Qt5-/Qt6-Tests** bestanden (Befehle, echte
Baum-/Canvas-Menüaktionen, GUI-/CLI-Projektweg, MainWindow und Modusregeln).
Zusätzlich je **3 betroffene Tests** mit Assertions für aktive Taschenvorschau
und materialisierte Bohr-/Konturzustände bestanden. Abgedeckt sind stabile
IDs, Quellvorgaben, getrennte Werkzeuge, Einzelzuordnung einer mehrfach
bearbeiteten Kontur, atomarer Abbruch und Undo/Redo. Sieben vorhandene
Menütexte werden wiederverwendet und in DE/FR/RU gegen fertige TS-Übersetzungen
und geladene QM-Dateien geprüft. Strikter Dokumentationsbuild und Diff-Prüfung
ohne Fehler. Keine neue Vollsuite-, Paket-, Debian- oder Maschinenabnahme;
kein Commit/Push. Die Sicht-/Bedienprüfung bleibt Teil von P8.

[Anleitung](../../docs/user-guide/machining-steps.md),
[Entscheidung und Nutzerprüfung](planning/r3-r1b-implementation-plan.md#r3-ui-user-check).

## R3: Vorschub-/Winkelanzeige präzisiert (07.11.2026)

Die spätere Nutzerkorrektur zu D28 ersetzt den Vorschub-/Winkelstandard des
folgenden Nachweises: Längen bleiben bei mm 3 / inch 5 Nachkommastellen;
**Vorschübe und Winkel erhalten jeweils Standard 1**, unabhängig von mm/inch.
Beide sind unter Zahlenanzeige getrennt von 0–12 konfigurierbar. Schema 9.21
ergänzt `Display.decimals_feed`; gespeicherte individuelle Anzeigeeinstellungen
bleiben erhalten. Ein bereits gespeicherter Winkelwert 3 wird daher nicht
ungefragt überschrieben. Formular und Konfigurationsfelder verwenden die
getrennten Einstellungen ohne Änderung der Eingabe-/Speichergenauigkeit.

**Nachweis:** je **20 gezielte Tests unter Qt5 und Qt6** bestanden
(Anzeige, Konfigurationsfelder, Eingabe-/Exportpräzision, Altprofile und Panel).
Vorschub-/Winkelstandard, unabhängige Änderung, beide Längeneinheiten und
vollständige Werte bleiben abgesichert. Neuer Config-Text DE/FR/RU übersetzt,
QM-Dateien regeneriert und geladene Übersetzungen geprüft. Strikter
Dokumentationsbuild und Diff-Prüfung ohne Fehler. Kein Commit/Push.

<a id="r3-numeric-layout"></a>

## R3: Anzeigepräzision und skalierende Formularbreiten (07.11.2026)

Nutzerkorrektur D28/D29 ist umgesetzt. Zahlenfelder zeigen standardmäßig
3 Nachkommastellen für mm und 5 für inch. Vorschübe folgen der Einheit;
Winkel verwenden eine eigene Vorgabe mit Standard 3. Ganzzahlige
Werkzeugnummern/Drehzahlen bleiben ganzzahlig. Unter Konfiguration → Allgemeine
Einstellungen → Zahlenanzeige sind die drei Werte von 0 bis 12 einstellbar.
Konfigurationsversion 9.20 übernimmt alte unterstützte Profile mit 3/5/3.

Die gemeinsame Formatierung gilt für Bearbeitungsfelder, Werkzeugwerte,
Konfiguration, numerische Popups und numerische Entities-Einträge. Beim
Bearbeiten wird der vollständige Float-Wert sichtbar. Unveränderte Felder
schreiben keinen gerundeten Anzeigetext zurück. Die bisherigen Spinbox-
Begrenzungen betreffen nun nur die Anzeige; zusätzliche Eingabestellen und
Schritte verwenden die vollständigen Werte. Auch der Startpunktdialog nutzt
jetzt die gemeinsame Eingabe statt `%g` mit verkürzten Rückgabewerten.
Anzeigeeinstellungen verändern weder Projektwerte noch Exportpräzision.

Beschriftungen, Einheiten und Wertfelder beider Parametergruppen skalieren
über gemeinsame Spaltengewichte. Die Startbreite links ergibt sich aus den
jeweils breitesten Inhalten. Beschriftungen umbrechen bei Bedarf, Einheiten
sind gleich ausgerichtet, die Symbolspalte bleibt 32 Pixel breit. Das gesamte
Formular wird beim Verkleinern nicht mehr seitlich aus dem Sichtbereich
hinausgeschoben.

**Nachweis:** je **47 gezielte Tests unter PyQt5 und PyQt6** bestanden.
Nach abschließender Einheiten-/Startbreitenanpassung die **2 Paneltests je
Bindung** erneut bestanden. Enthalten sind volle zusätzliche Eingabestellen,
unveränderte Übernahme, kleine Werte unterhalb der Anzeigeauflösung,
mm/inch/Winkel, Punkt/Komma, Konfigurations-/Projekt-/Export-Roundtrip,
3/5/3-Migration für unterstützte Altprofile, Anzeigeänderung ohne
Projektmutation sowie breites/schmales Formular mit bündigen Spalten und
sichtbaren Symbolen. **6 neue Texte je DE/FR/RU-Katalog**, QM-Dateien neu
kompiliert und neue Übersetzungen gegen geladene Kataloge geprüft. Native
Windows-Qt-Ansichten in mm/inch und mit 620/340 Pixel Seitenleistenbreite
verdeckt gerendert und visuell kontrolliert. Strikter Dokumentationsbuild
und Diff-Prüfung ohne Fehler.

[Bedienung](../../docs/user-guide/machining-steps.md),
[technische Notizen](../documentation-notes/gui-numeric-display.md).
Die [Nutzerprüfung](planning/r3-r1b-implementation-plan.md#r3-ui-user-check)
auf realem Monitor/Skalierung bleibt P8. Kein Commit, Push, Release oder
zusätzlicher Vollsuite-/Paket-/Debian-/Maschinenlauf.

<a id="r3-ui"></a>

## R3-UI: Geometrieansicht und Bedienkorrektur (07.11.2026)

Nach ausdrücklicher Nutzerfreigabe sind D23–D27 umgesetzt. Die zwei Original-
Auswahlbäume liegen unverändert in den einklappbaren, vertikal verstellbaren
Gruppen Entities und Layers im Tab Geometrie. Bearbeitung ist der zweite Tab.
Die ursprünglichen Layers-Sortierpfeile entfallen aus der Originalansicht.

R3-MENU öffnet in beiden Originalbäumen zunächst ein Kontextmenü an der
Viewport-Klickposition. Verknüpfte Schritte sind in Bearbeitungsreihenfolge
anspringbar. Erst die Erstellen-Aktion öffnet den Dialog nahe dem Auslöser.
Ohne Auswahl entsteht ein leerer Schritt; mit Auswahl ist Verschieben
vorbelegt, Kopieren und „Auswahl nicht verwenden“ sind Alternativen.
Navigation und Abbruch verändern weder Projekt noch Befehlsverlauf.

Die Werkzeugleiste oben gruppiert Erstellen, Umordnen, Rückgängig/
Wiederherstellen und Baumansicht. Ein-/Ausklappen steht rechts; ohne mögliche
Aktion sind die betreffenden Knöpfe grau. Bearbeiten (F2), Entfernen (Delete),
Richtung und Startpunkt liegen im Baumkontextmenü. Die unteren Buttonreihen
sind entfernt. Der Baum hat drei Spalten: Bezeichnung, Export und Optimierung;
Schrittzeilen nennen Name, Art und Werkzeug, Tooltips Herkunft und Diagnose.

Bearbeitungswerkzeug und Konturparameter verwenden bündige Spalten für
Bezeichnung, Einheit, Wert und ein einziges Herkunftsmenü. Kette/Stift zeigen
Vererbung/eigenen Wert; das Menü bietet Bearbeiten und Schrittvorgabe.
Die Anzeige verwendet zehn signifikante Stellen; ein unverändertes Feld
behält den vollständigen gespeicherten Wert. Eine im neuen Checkbox-Test
gefundene native Qt5-Zugriffsverletzung ist behoben: Der Baum wird erst nach
Abschluss des Checkbox-Ereignisses erneuert.

**Nachweis:** je **38 gezielte Tests unter PyQt5 und PyQt6** bestanden
(Panel, GUI-/CLI-Projektweg, Befehle, MainWindow, Übersetzungen und
Architekturgrenzen). Nach der abschließenden Werkzeugleistenanordnung die
**2 Paneltests je Bindung** erneut geprüft. Abgedeckt sind ganze Layer,
beide Rechtsklick-Ansichten, Popup-Position, bestehende Mehrfachverknüpfungen,
Navigation, Verschieben/Kopieren/Leer/Abbruch, Gruppen-Einklappen,
Export-/Optimierungscheckboxen, Undo/Redo und Erhalt voller Zahlengenauigkeit.
Native Windows-Qt-Ansichten verdeckt gerendert und visuell kontrolliert.
**14 neue Texte je DE/FR/RU-Katalog**, QM-Dateien regeneriert und alle drei
GUI-Sprachkontexte gegen geladene Kataloge geprüft. Strikter Dokumentations-
build und Diff-Prüfung ohne Fehler.

Die [konkreten Aufgaben für P8](planning/r3-r1b-implementation-plan.md#r3-ui-user-check)
bleiben offen: Nutzerablauf, Bildschirm-/Skalierungseindruck, Referenzprojekte
und Wiederladen. Keine erneute Vollsuite-, Paket-, Debian-, GPU- oder reale
Maschinenabnahme. Kein Commit, Push oder Release in diesem Auftrag.

<a id="r3-parameter-form-correction"></a>

## R3: vertraute Parameterfelder und Herkunftssymbole (07.11.2026)

Auf Nutzerkorrektur D22 sind die vorhandenen Bereiche für Werkzeug und
Konturparameter aus Layers in Bearbeitung verschoben und direkt mit dem
Bearbeitungsmodell verbunden. Die zunächst eingeführte Parametertabelle ist
entfernt. Die bisherigen Eingabefelder bleiben erhalten; zuvor reine
Werkzeug-Wertanzeigen für Drehzahl und Lead-Abmessungen sind an gleicher
Position editierbar, damit eigene Werte weiter bedienbar sind.

Bei Schrittauswahl bearbeiten die Felder Schrittvorgaben, bei aktiver
Bearbeitungskontur deren Werte. Werkzeugwahl sowie Rückzugs-/Sicherheitshöhe
bleiben schrittbezogen. Alte Schreibsignale auf Original-Layer/Shapes sind
abgeklemmt; Änderungen laufen über dieselben atomaren Modellbefehle und Undo.
Entities/Layers enthalten diese Parameterbereiche nicht mehr.

Kettenglied/Stift als skalierte monochrome Vektorpfade kennzeichnen geerbte
und eigene Werte. Tooltips nennen Herkunft und wirksamen Wert. Ein separater
Rücksetzpfeil entfernt einen eigenen Konturwert und aktiviert die Vererbung.
Herkunft hängt nicht von Wertgleichheit oder Farbe ab. Symbole und Aktionen
besitzen zugängliche Namen, Tooltips sind auch per Symbolaktivierung erreichbar.
Ohne eindeutigen Bearbeitungskontext sind die Felder gezielt deaktiviert.

**Nachweis:** jeweils **38 fokussierte Tests unter PyQt5 und PyQt6** bestanden
(Panel, echter GUI-Workflow, Modellbefehle, MainWindow, Übersetzungs- und
Architekturgrenzen). Nach abschließender Einheitenkorrektur die **3 betroffenen
Panel-/Einheitentests je Bindung** erneut bestanden. Geprüft sind echte
Tastatureingabe, eigener/geerbter Wert mit Rücksetzen, unverändertes Feld ohne
neuen History-Eintrag, Undo/Redo, Schrittvorgaben ohne Überschreiben eigener
Konturwerte, Werkzeugwahl ohne Original-Layer-Änderung, ungültige Zahlen ohne
Mutation, korrekte mm/in-Anzeigen sowie Export-Roundtrip. Das Formular wurde
zusätzlich mit nativer Windows-Qt-Darstellung verdeckt gerendert und visuell
kontrolliert. Das ersetzt keine gemeinsame Nutzerabnahme P8.

**13 zusätzliche Texte je DE/FR/RU-Katalog** übersetzt, QM-Dateien regeneriert
und beide Sprachkontexte gegen geladene Qt-Kataloge geprüft. Strikter
Dokumentationsbuild und Diff-Prüfung gehören zum Abschluss. Kein Commit/Push,
keine Vollsuite-, Paket-, Debian- oder Maschinenabnahme in diesem Folgeauftrag.

[Anleitung](../../docs/user-guide/machining-steps.md),
[Modellnotizen](../documentation-notes/machining-project-format.md).

<a id="r3-r1b-p4-p6"></a>

## R3/R1b P4–P6: Bearbeitungstab, Befehle und Ausgabe (07.11.2026)

Vor Beginn wurde der geprüfte P1–P3-Stand als **`5415018`** lokal committet.
Der verpflichtende Fast-Hook bestand mit **277 Tests**. Für diesen Auftrag
wurde kein Push oder Release ausgelöst.

**P4:** Dritter Tab „Bearbeitung“ mit benannten Schritten, genau einer Art
und Werkzeugdefinition je Schritt, Original-/Bearbeitungsauswahl und aktivem
Editierkontext umgesetzt. Originalkonturen werden einmal gezeichnet; alle
Verknüpfungen sind auffindbar. Parameter zeigen ihre Herkunft und können
bewusst wieder geerbt werden. Richtung/Start ändern nur die Bearbeitung.
Schritte anlegen, umbenennen, Art/Werkzeug ändern und ganze Layer über die
Originalauswahl zuordnen ist möglich. Bekannte Planungsdiagnosen erscheinen
bei der aktiven Bearbeitung. Neue/unzugeordnete Konturen haben keine
willkürliche Bearbeitungsvorschau.

**Zusätzliche Nutzerentscheidung D20:** Exportcheckboxen nur in Bearbeitung;
Entities/Layers behalten Originalstruktur und Auswahl. Die Zeichnungs-
Aktivdarstellung berücksichtigt, ob mindestens eine verknüpfte Bearbeitung
aktiviert ist. Alte Parameterfelder sind dort nicht mehr editierbar.

**P5:** Reine `MachiningCommands` mit Transaktionen und History implementiert.
Drag-and-drop mit Einfügemarkierung, Ctrl-Kopieren, Menüwege, Auf-/Ab-Sortieren,
Zuordnung, Entfernen sowie Werkzeug-/Schrittvorgabenübernahme benutzen dieselbe
Befehlsschicht. Eigene Werte bleiben erhalten, Zielwerte werden geerbt.
Ungültige Mehrfachaktionen melden die betroffenen Konturen und verändern
weder Daten noch History. Verschieben erhält IDs, Kopieren erzeugt neue
Bearbeitungs-IDs, Redo stellt dieselben IDs wieder her. Beim Entfernen eines
gefüllten Schritts wird sein Inhalt ausdrücklich entfernt oder verschoben;
Originalgeometrie bleibt erhalten. Undo/Redo erfasst die neuen Aktionen,
nicht alle früheren CAD-Funktionen; Import/Reload beginnt eine neue History.

**P6:** Sichtbare Schritt-/Eintragsreihenfolge ist der Exportvertrag und wird
gespeichert. Beide relativen Optimierungsmodi bleiben erhalten, Optimierung
überschreitet weder Schritt- noch Custom-G-Code-Grenzen. Vorschau und Route
verwenden getrennte Projektionen desselben Plans; Routenenden enthalten
Anfahrt, Abfahrt und Overcut. Eine Vorschauaktion aktiviert keine manuelle
Routenanzeige. Aktive Richtungs-/Startpfeile und 3D-Planverbrauch sind an die
Bearbeitung gekoppelt. Projektionsdaten werden nur innerhalb eines
synchronen Neuzeichnens wiederverwendet, nicht über Änderungen hinweg.

**Zusätzliche Nutzerentscheidung D21:** Werkzeugwechsel weiterhin nur bei
anderer Ausgabenummer. Unterschiedliche Definitionen/Drehzahlen gleicher
aufeinanderfolgender Nummer erzeugen weder einen weiteren Werkzeugwechsel-
Profilblock noch eine zusätzliche Drehzahlausgabe. Dies ist ausdrücklich
beibehaltenes Verhalten, geprüft für Legacy- und verwaltete Werkzeugwechsel.
Bestehende Einschränkungen verwalteter Makros für opaken freien G-Code bleiben.

Bewusste Maschinenart-/Kompensations-/Toleranzänderungen über vorhandene
Bedienwege wirken weiterhin auf den Auftrag; externe Werkzeugprofiländerungen
werden erst bewusst übernommen. Einheitenwechsel konvertiert Bearbeitungswerte
einmal und speichert die ausdrückliche Interpretation der Zeichnungseinheit.
Der dabei sichtbar gewordene `None`-Fall des optionalen Startradius ist behoben.

**Nachweis:** gezielte Integrationsgruppe mit **134 Tests unter PyQt5 und
134 unter PyQt6** bestanden. Anschließend **29 gezielte Befehls-/Panel-/
Modusprüfungen je Bindung** einschließlich der letzten Änderungen bestanden.
Enthalten sind reine Befehlsregressionen, echte Qt5-/Qt6-Drop-Events,
Ablehnung veralteter Nutzdaten, Auswahl mehrfach referenzierter Konturen,
ursprüngliche Geometrie bei Richtungswechsel, eigene/geerbte Werte,
Exportaktivierung/Sichtbarkeit, stabile Undo-/Redo-IDs, Unit-Override,
Fremdprojekt-Ablehnung, Routenendpunkt gegen ausgegebene Lead-out-Koordinate,
Optimierungsgrenzen sowie sichtbare T2→T1-Folge gegen echten GUI-/CLI-Export.
Die ganze Layerauswahl wurde zusätzlich über echte Auswahlsignale und den
modalen Schritt-Dialog bis zur Übernahme und Undo geprüft. Umbenennen oder
Ändern der Kompensation erhält widersprüchliche Altmodi; erst eine ausdrücklich
gewählte Schrittart löst sie auf.
Architektur-, bestehende MainWindow-, Werkzeugwechsel-, Plan-, Vorschau- und
3D-Adapterregressionen sind einbezogen. Frühere Qt-Callbackabbrüche durch eine
zu frühe Neuzeichnung bzw. Diagnoseformatierung wurden korrigiert und die
betroffenen Abläufe anschließend erneut erfolgreich geprüft.

Alle **102 neuen Texte je Katalog** in DE/FR/RU sind fertig übersetzt,
QM-Dateien regeneriert und gegen die tatsächlich geladenen Qt-Übersetzungen
geprüft. Der Austausch zweier QM-Dateien benötigte wegen abweichender
Windows-Berechtigungen einen erlaubten Schreibzugriff außerhalb der Sandbox;
ein Neustart oder Schließen eines Benutzerfensters war dafür nicht notwendig.
Strikter Zensical-Build, relative Dokumentdateilinks und `git diff --check`
bestanden.

**Grenzen:** P8 bleibt die gemeinsame fachliche Nutzerabnahme an konkreten
Projekten, einschließlich aktueller Screenshots und Prüfung verbliebener
Legacy-Kompatibilitätsaufrufer vor Entfernung. P7 bleibt separat. 3D-Tests
verwenden gemocktes OpenGL und sind kein GPU-Nachweis. Keine neue Vollsuite-,
Debian-, Paket- oder physische Maschinenabnahme. P4–P6 wurden in diesem
Auftrag nicht committet oder gepusht.

[Anleitung](../../docs/user-guide/machining-steps.md),
[Plan und Entscheidungen](planning/r3-r1b-implementation-plan.md),
[Modell-/Formatnotizen](../documentation-notes/machining-project-format.md).

<a id="r3-r1b-p1-p3"></a>

## R3/R1b P1–P3: Modell, Projektionen und Persistenz (07.11.2026)

**P1:** Qt-freie Geometrie-, Werkzeugdefinitions-, Schritt- und
Bearbeitungsidentitäten mit geordneten Einträgen, eigenständigen Starts und
Richtungen sowie Resolver und Parameterherkunft implementiert. Gemäß D7 bleiben
unklare alte Zahlenwerte eigene Werte. Gemäß der zusätzlichen Nutzerentscheidung
D19 dürfen unterschiedliche Werkzeugdefinitionen dieselbe Ausgabenummer tragen.
Die Definitions-ID bestimmt die gemeinsame Aktualisierung, nicht die Nummer.

**P2:** Legacy-Shape/Layer-Zustand lässt sich in das Bearbeitungsmodell
übernehmen. Getrennte Projektionen verwenden gemeinsame gespeicherte Werte für
Planung, Vorschau und Export, ohne die Originalgeometrie bei ihrer Erzeugung zu
ändern. Eigene Werkzeuge/Arten und freier G-Code begrenzen Migrationsschritte;
die bisherige Reihenfolge sowie BREAKS-/Ignore-Semantik bleiben erhalten.
Geladene Konflikte werden erhalten und durch bestehende Diagnosen blockiert.

**P3:** UTF-8-JSON `.d2g` 2.0 mit validierten IDs, Konfiguration und Referenzen
ergänzt; Leser 1.1–1.5 bleiben erhalten. GUI-Speichern, Projektladen, kleiner
Transformationsreload, erneuter DXF-Import und CLI-Projektexport sind angebunden.
Gespeicherte Werkzeug-/Bearbeitungsvorgaben bleiben von globalen Profiländerungen
unabhängig. Neue Quellkonturen bleiben unzugeordnet; aktive fehlende oder
mehrdeutige Verknüpfungen stoppen den gesamten Export vor der Ausgabe.
Atomarer Dateiersatz schützt bestehende Dateien; migrierte Legacy-Dateien müssen
zunächst unter neuem Namen gespeichert werden.

**Lokaler Nachweis:** gezielte Integrationsgruppe mit **86 Tests unter PyQt5
und 86 unter PyQt6** bestanden (Modell/Format, echter Qt-Workflow, Architektur,
Importfilter, Bearbeitungsmodi, Legacy-Projekte, MainWindow, CLI und
Exportreihenfolge). Die Migration 1.1–1.5 erhält im geprüften Konturfall die
Programmausgabe. Der echte offscreen MainWindow-Workflow prüft zwei Bearbeitungen
derselben Kontur mit unterschiedlichen Tiefen gegen den echten CLI-Export:
Programmbefehle stimmen überein. Fehlreferenztest: CLI-Code 2, stdout leer,
vorhandene Zieldatei unverändert. Weitere Fälle prüfen Mehrdeutigkeit,
unabhängige Richtungen, Profilstabilität, doppelte Werkzeugnummern und atomaren
fehlgeschlagenen Dateiersatz. Tests sind in der Fast-Auswahl registriert.
`git diff --check` und strikter Zensical-Dokumentationsbuild bestanden.

**Grenzen:** P4/P5/P6/P8 bleiben offen: dritter Tab, Zuordnungsbedienung,
Verschieben/Kopieren mit Zielvalidierung/Undo, sichtbarer Reihenfolgevertrag,
Profilübernahme mit Änderungsanzeige und integrierte Nutzerabnahme. Bis dahin
synchronisiert eine begrenzte Brücke Eingaben des bestehenden Editors in den
eindeutigen/ausdrücklich aktiven Arbeitsgang. Bei Mehrfachreferenzen ohne Kontext
wird keine Bearbeitung willkürlich ausgewählt. Keine neue manuelle
Stegregionenbedienung. Keine neuen GUI-Beschriftungen hinzugefügt. Keine neue
Vollsuite-, Paket-, Debian-, GPU- oder Maschinenabnahme und kein Release.

[Detailplan](planning/r3-r1b-implementation-plan.md),
[Zuordnungstabelle, Dateivertrag und Quellen](../documentation-notes/machining-project-format.md).

<a id="develop-r3-checkpoint"></a>

## Develop-Release vor R3/R1b veröffentlicht und geprüft (06.11.2026)

Der bestätigte Plan und die Release-Zusammenfassung wurden als
[`452ba97`](https://github.com/dxf2gcode/dxf2gcode/commit/452ba97c863be9769d9e74903bfe43f4d30cafde)
committet und auf `origin/develop` gepusht. Der Commit ändert ausschließlich
Dokumentation; relative Dokumentlinks, Diff-Format und strikter Zensical-Build
bestanden. Der Fast-Hook wurde gemäß AGENTS.md nur für diesen Dokumentations-
commit mit befehlslokalem leerem `core.hooksPath` ausgelassen.

Der manuell auf Develop gestartete
[Release-Lauf 42259036046](https://github.com/dxf2gcode/dxf2gcode/actions/runs/42259036046)
bestand mit allen sieben Jobs: je **925 Tests** unter Python 3.11/3.12/3.13
mit PyQt5 sowie Python 3.11 mit PyQt6, Quellarchiv/Wheel-Build und Prüfung in
frischen Qt5-/Qt6-Umgebungen, Windows-ZIP-/MSI-Build samt automatisierter
Prüfung und Veröffentlichung. Ein wegen langsamer Ubuntu-Downloads verzögerter
Python-3.12-Job wurde auf frischem Runner wiederholt; die drei bereits
erfolgreichen Ergebnisse blieben erhalten. Kein Quellcode wurde dafür geändert.

Veröffentlicht ist
[DXF2GCODE Develop 2.0.0.dev12](https://github.com/dxf2gcode/dxf2gcode/releases/tag/develop-ci-42259036046)
mit Tag `develop-ci-42259036046`, Buildnummer 12 und MSI-Version `2.0.12`.
Der Release ist ein sichtbarer Prerelease, kein Draft oder stabiler Release.
Die Windows-Pakete sind wie im Manifest ausgewiesen **unsigned**.

**Reale Downloadprüfung:** Alle sechs veröffentlichten Dateien heruntergeladen
(135.427.923 Bytes): Windows x64 MSI und ZIP, Python-Wheel, Quellarchiv,
`release-manifest.json` und `SHA256SUMS`. Dateinamen und Größen entsprechen den
Release-Assets; sämtliche SHA-256-Werte stimmen mit `SHA256SUMS` sowie den
GitHub-Asset-Digests überein. Das Manifest nennt den vollständigen Commit
`452ba97c863be9769d9e74903bfe43f4d30cafde`, Run `42259036046`, Version und
Develop-Kanal korrekt. Die heruntergeladenen Pakete wurden lokal nicht installiert.

Damit ist der manuelle Develop-Veröffentlichungsablauf einschließlich
öffentlicher Downloads real nachgewiesen. CI1 behält seine offenen PR-/Stable-
und Signierungsprüfpunkte; M1, gesonderte Debian-/GPU-/Maschinenabnahme und
die stabile Version 2.0.0 bleiben separat. R3/R1b ist geplant, noch nicht
implementiert. Der Release fixiert ausdrücklich den Stand vor dieser Umsetzung.

<a id="r3-r1b-plan"></a>

## R3/R1b – Gemeinsamer Umsetzungsplan abgestimmt (06.11.2026)

Der Nutzer hat den [Detailplan](planning/r3-r1b-implementation-plan.md)
nach mehreren Entscheidungsrunden bestätigt. Entities/Layers bleiben für
Originalgeometrie und Auswahl; ein dritter Tab enthält Bearbeitungsschritte
mit je einer Art und einem Werkzeug. Bearbeitungskonturen referenzieren die
Originalkontur; Verschieben und bewusstes Kopieren sind getrennte Aktionen.
Eigene Werte bleiben erhalten, Zielvorgaben werden geerbt. Neue DXF-Konturen
nach Reload werden erst bewusst zugeordnet. Unpassende Mehrfachaktionen
werden vollständig abgelehnt. Direkte Ausführung, Änderungsanzeige und Undo
sind vereinbart. Projektwerte bleiben bis zur bewussten Aktualisierung stabil.

Neue `.d2g`-Version mit Lesern für 1.1–1.5, Erhalt unklarer Altwerte und
Migration ohne geänderte Ausgabereihenfolge sind geplant. Manuelle Stege,
Automatik/Fang und Teilkonturbedienung folgen später; bestehende BREAKS:-
Funktion bleibt im Grundumfang erhalten. P0 (Planung) ist abgeschlossen;
P1–P6/P8 sind noch nicht implementiert oder als Software abgenommen.

Prüfung dieser Dokumentationsänderung: relative Dokumentlinks und Diff-Format;
strikter Dokumentationsbuild beim Commitabschluss. Kein neuer lokaler
Softwaretest erforderlich. Vor der Umsetzung sind Commit, Push und ein
Develop-Prerelease des bisherigen Softwarestandes ausdrücklich beauftragt.
Keine Freigabe einer stabilen Version oder neuen Debian-/Maschinenabnahme.

<a id="a1-complete"></a>

## A1 – Vollständiger Architekturabschluss (06.11.2026)

Die beauftragte Variante V ist vollständig umgesetzt: P0–P4 und I0–I5 aus
dem [Abschlussplan](planning/a1-completion-plan.md). Die frühere
[Bestandsaufnahme](planning/architecture-acceptance.md) bleibt historisch
erhalten; A1 steht nicht mehr in der offenen Todo.

**Fachlicher Vertrag:** Pocketing ist nur beim Fräsen mit Softwarekompensation
unterstützt. Maschinenkompensation, Schleppmesser und Drehen blockieren die
Vorbereitung und Planung mit `machining.pocket_unsupported`. Gespeicherte
Werte bleiben erhalten. Projektladen sowie Maschinen-/Kompensationswechsel
aktualisieren Pläne und Warnungen. Ausstehende Vorschaufehlermeldungen werden
bei Reloads bereinigt und mit aktuellen Warnungen zusammengeführt.
Jedes aktive Shape mit blockierendem Planungsfehler stoppt den gesamten
Export vor der Ausgabe; vorhandene Dateien bleiben unverändert, stdout leer.
GUI-Filter und CLI melden Fehlerstatus. Gültige Software-Pocket-, Bohr-,
Kontur-, Dreh- und Messerfälle behalten ihre bisherigen Planverträge.

**Architektur:** Alle Domain-/Application-Module werden ohne Qt, Presentation,
Runtime-Globals oder konkrete Adapter importiert. Shape/LayerContent erhalten
`config` explizit und optional eine Übersetzungsfunktion; geerbte Werkzeug-
und Messerwerte bleiben aktuell. Project erhält Konfiguration, Dokumente bzw.
Decoder und Lebenszyklus-Callbacks. Qt koordiniert Tree/Canvas/Cursor/Reload
in `presentation/qt/project_session.py`; reine Dokumentdaten liegen im Domain,
der sichere Codec im Adapter. `.d2g` 1.1–1.5 bleiben unterstützt.
CLI-DrawingSession benötigt keine GUI-No-ops. Reader, Vorbereitung und Decoder
werden im Composition Root injiziert. Qt-Runtime-Metadaten liegen außerhalb
des Domain. Interne Konstruktoraufrufe und Qt-Projektmetadaten sind umgestellt.

**Prüfnachweise:** 76 fokussierte Qt5-Tests und 88 Qt6-Tests bestanden
(Importgrenzen, Machining, Plan/Projektion, Projekte, CLI/Filter, Hauptfenster,
Werkzeugwechsel und Messer; überlappende Gruppen, keine addierte Gesamtzahl).
Der anschließend ergänzte reale Hauptfenster-Test für Maschinen-/Kompensations-
wechsel und Korrektur besteht unter beiden Bindungen. Gemischte Aufträge
prüfen Dateierhalt, ausbleibende Neuanlage und leeres stdout. Ein echter CLI-
Unterprozess und der GUI-Filter liefern bei ungültigem Pocket-Auftrag Status 2.
Der Importtest führt zusätzlich Shape-/Layer-/Projektoperationen mit expliziten
Werten ohne Qt/Globals aus. Neue Diagnose in DE/FR/RU übersetzt, QM regeneriert
und geladene Übersetzungen unter beiden Bindungen geprüft.

**Commit und Bereitstellung:**
[`a552dc9`](https://github.com/dxf2gcode/dxf2gcode/commit/a552dc9e055f6ee636b542bf12c49b2cb8e38563)
(`refactor(core): complete A1 model and export boundaries`) ist auf
`origin/develop` gepusht. Der verpflichtende Pre-Commit-Hook bestand mit
**251 Tests in 43,262 Sekunden**. Lokaler strikter Dokumentationsbuild und
Prüfung der relativen Dokumentlinks bestanden.

**CI-Nachkontrolle:** Die
[Dokumentationsprüfung](https://github.com/dxf2gcode/dxf2gcode/actions/runs/42244121005)
und die [Develop-Dokumentationsvorschau](https://github.com/dxf2gcode/dxf2gcode/actions/runs/42244121008)
sind erfolgreich. Die automatische
[Vollprüfung des ursprünglichen Commits](https://github.com/dxf2gcode/dxf2gcode/actions/runs/42244120989)
fand 14 Fehler in drei Testdateien: fehlender Runtime-Import in GIR-/Offset-
Testhelfern und eine alte Pocket-Erwartung für Maschinenkompensation. Die
Testhelfer sind korrigiert; die Pocket-Regression prüft jetzt ausdrücklich
Blockierung und Werterhalt. Alle 58 betroffenen Tests bestehen lokal unter
PyQt5 und PyQt6. Das CI-Ergebnis des ursprünglichen Commits ist damit kein
erfolgreicher Gesamtnachweis.

**Nachbesserung und aktueller Freigabestand:**
[`7335d09`](https://github.com/dxf2gcode/dxf2gcode/commit/7335d09d4b0f795ce3685b57d73eda6323e2bc77)
enthält die korrigierten Regressionen und ist auf `origin/develop` gepusht.
Der Pre-Commit-Hook bestand erneut mit **251 Tests in 44,680 Sekunden**.
Die 58 gezielten Qt5- und 58 Qt6-Tests bestanden ebenfalls; sie ersetzen keine
lokale Vollsuite. Der zunächst wartende
[CI-Lauf für 7335d09](https://github.com/dxf2gcode/dxf2gcode/actions/runs/42245781440)
wurde durch den Dokumentationscommit `d44976f` abgelöst.

**CI-Gesamtergebnis abgeschlossen (06.11.2026):** Der
[Prüflauf 42245959419](https://github.com/dxf2gcode/dxf2gcode/actions/runs/42245959419)
für den exakten Stand
[`d44976f`](https://github.com/dxf2gcode/dxf2gcode/commit/d44976fc2bac76a1d1f2cdc216d2fa90809ccf07)
ist vollständig mit **success** beendet; alle sechs Jobs sind erfolgreich.

| CI-Prüfung | Ergebnis |
| --- | --- |
| Python 3.11 / PyQt5, Ubuntu 24.04 | 925 Tests bestanden |
| Python 3.12 / PyQt5, Ubuntu 24.04 | 925 Tests bestanden |
| Python 3.13 / PyQt5, Ubuntu 24.04 | 925 Tests bestanden |
| Python 3.11 / PyQt6, Ubuntu 24.04 | 925 Tests bestanden |
| Quellarchiv und Wheel | Gebaut; Wheel in frischen Qt5-/Qt6-Umgebungen geprüft |
| Windows x64 ZIP und MSI | Gebaut; ZIP und installiertes MSI auf GUI-Start, DXF-Export, Ressourcen und Herkunft geprüft |

Ein überholter, bereits fehlerhafter Lauf blockierte zunächst die Warteschlange
und wurde abgebrochen. Im aktuellen Lauf verzögerte der Ubuntu-Paketserver
den Qt6-Abhängigkeitsdownload; der betroffene Job wurde auf einem frischen
Runner wiederholt und bestand anschließend. Die drei erfolgreichen PyQt5-
Ergebnisse blieben erhalten. Die Wiederholung änderte keinen Quellcode.
Damit sind die A1-Softwareprüfung und das ausstehende CI-Gesamtergebnis erledigt.

Keine neue lokale Vollsuite oder Debian-/SSH-Prüfung. Die automatisierte
Ubuntu-/Windows-Paketprüfung ersetzt keine gesonderte M1-/CI1-Betriebsabnahme,
GPU-Prüfung, physische Maschinenabnahme oder Release-Freigabe. Diese bleiben
separat; der frühere AXIS-Nachweis ist kein erneuter Debian-/Maschinennachweis
dieser A1-Änderungen.

<a id="a1-p2-menu"></a>

## A1-P2 – Pocket-Menü verwendet gemeinsame Gültigkeitsregel (06.11.2026)

Das echte Qt-Kontextmenü verwendet nun dieselbe `pocket_supported`-Regel
wie Vorbereitung und Planer. Pocketing wird nur im Fräsmodus mit
Softwarekompensation und ausschließlich geschlossener Auswahl angeboten.
Im Drehmodus entfällt damit der bisher fälschlich vorhandene Menüeintrag.
Gesetzte Pocket-Werte bleiben auch beim erneuten Öffnen in einem nicht
unterstützten Modus erhalten; das Menü korrigiert sie nicht stillschweigend.

Je 17 gezielte Menü-/Machining-Tests unter Qt5 und Qt6 bestanden. Die echten
QMenu-/QAction-Objekte werden aufgebaut, nur der blockierende Popup-Aufruf
ist ersetzt. Geprüft: Dreh-/Messer-/Fräsmodus, Wechsel der Kompensationsart
und erneutes Öffnen, Erhalt gesetzter Pocket-Werte sowie offene, gemischte
und leere Auswahl. Der widersprüchliche Lathe-Test erwartet jetzt die
ausdrücklich beschlossene Sperre. Keine neuen GUI-Texte oder Übersetzungen.

Projektlade-Meldungen, vollständige Aktualisierung bei Einstellungswechsel,
auftragsweiter Exportabbruch und I0–I5 bleiben offen.
[Restplan](planning/a1-completion-plan.md). Keine Vollsuite, Debian-/SSH-,
Paket- oder Maschinenprüfung. Kein Commit.

<a id="a1-p1"></a>

## A1-P1 – Gemeinsame Pocket-Gültigkeitsregel (06.11.2026)

Nach Nutzerentscheidung Pocketing bei Maschinenkompensation, Schleppmesser
und Drehen blockieren. `pocket_supported` in `domain/project/machining.py`
definiert die reine Regel; StMove prüft sie vor Geometrieerzeugung und der
Planer vor Strategieauswahl. Nicht unterstützte Pocket-Zustände erzeugen
`machining.pocket_unsupported` ohne Plan. Gespeicherte Drill-/Pocket-/G40-
Werte bleiben erhalten; bestehende Drill-Konflikte behalten Vorrang.

44 gezielte Planvertrags-, Machining-, Importgrenz- und Toolpath-Slice-Tests
unter Qt5 sowie dieselben 44 unter Qt6 bestanden. Neue Regressionen prüfen
direkte Requests für alle nicht unterstützten Maschinen-/Kompensations-
Kombinationen mit G40/G41/G42, unveränderte Requests, Vorrang der alten
Konfliktregel und frühe Vorbereitung ohne Pocket-Geometrie. Vorhandene
positive Software-Pocket-Fälle bleiben erfolgreich. Die neue Meldung ist
in DE/FR/RU übersetzt; QM-Dateien regeneriert und über geladene Kataloge
unter beiden Qt-Bindungen geprüft. Generierte QM-Dateien bleiben ignoriert.

Dies ist bewusst nur die gemeinsame Regel mit frühen Sperren. Menüfreigaben,
Projektlade-Meldungen und der bestätigte auftragsweite Exportabbruch sind
noch nicht vollständig angebunden. Keine entsprechende Gesamtfreigabe;
auch I0–I5 bleiben offen. [Restplan](planning/a1-completion-plan.md).
Keine Vollsuite, Debian-/SSH-, Paket- oder Maschinenprüfung. Kein Commit.

<a id="a1-auswertung"></a>

## A1 – Architekturgrenzen und konkrete Falllücken ausgewertet (05.11.2026)

Quellbasis `7246810` mit bestehender Testabdeckung abgeglichen. Die
[A1-Auswertung](planning/architecture-acceptance.md) benennt die
repräsentative Maschinen-/Kompensations-/Profilmatrix und die genaue
Importgrenze. Der Geometry-/Toolpath-Kern ist Qt-/Runtime-frei; die pauschale
Aussage für sämtliche Domain-/Application-Module ist nicht zutreffend.

41 gezielte Architektur-, Planvertrag-, Fallmatrix- und B1/B2-Tests unter
Windows/Python 3.11/PyQt5 bestanden. Ergänzende AST-Importprüfung und drei
Modellzustandsproben fanden konkrete Pocket-Gültigkeitslücken: keine
blockierende Diagnose bei Maschinenkompensation oder Schleppmesser trotz
gesetztem Pocket-Wert; beim Drehen werden Pocket-Aktionen geplant. Die
GUI-Freigaben und ein widersprüchlich benannter Menütest sind im Bericht
zugeordnet. Keine neue fachliche Semantik implementiert.

Offen bleiben ausschließlich die benannten Entscheidungen
[A1-P/A1-I](#a1-complete), keine unbestimmte Vollmatrix.
Keine Quellcodeänderung, Vollsuite, Debian-/SSH-, Paket- oder Maschinenprüfung.
Dies dokumentiert die abgeschlossene Untersuchung und noch keine pauschale
Architektur-, Release- oder Maschinenfreigabe.

**Planung ergänzt:** Der Nutzer möchte die verbleibende Arbeit vor einer
Entscheidung im Detail verstehen. Der [A1-Abschlussplan](planning/a1-completion-plan.md)
trennt P0–P4 (konkrete Pocket-Fälle) und I0–I5 (zusätzliche Modell-/CLI-
Entkopplung), benennt Dateien, notwendige Entscheidungen, Regressionen und
Abschlusskriterien für beide möglichen Abnahmegrenzen. Keine Implementierung,
neuen Testläufe, Commits oder Pushes durch diesen Planungsschritt.

<a id="lc1-bestandsaufnahme"></a>

## LC1 – Bestandsaufnahme des LinuxCNC-Dateifilters (05.11.2026)

Historie, heutige Aufruf-/stdout-Pfade, Logging und vorhandene Testabdeckung
auf Quellbasis `7864ba2` im Windows-Checkout geprüft; historische Projektanleitung
mit offiziellem LinuxCNC-2.9-Handbuch und AXIS-Quellcode abgeglichen.
Der Filtermechanismus besteht weiterhin. Empfehlung: beibehalten und gezielt
modernisieren; GUI-Postprozessorauswahl, Fehler-/Abbruchstatus und veraltete
Einrichtung sind die konkreten Ansatzpunkte.

[Befunde, Quellen und konkreter Prüfplan](../documentation-notes/linuxcnc-integration.md)
bewahren das Ergebnis. Nur statische Untersuchung und Dokumentationsprüfung;
keine neuen Tests, Programmstarts, Debian-/SSH-, LinuxCNC- oder Maschinenläufe.
Keine Aussage über aktuelle praktische Funktionsfähigkeit oder Paketabnahme.
Zum Zeitpunkt der Bestandsaufnahme waren Umfangsentscheidung, Implementierung,
Regressionen, Simulation und geprüfte Anwenderanleitung noch offen. Der folgende
Abschlussnachweis dokumentiert die inzwischen umgesetzte lokale Filterkorrektur;
die verbleibenden Aufgaben stehen unter [LC1](toolpath-refactoring-completed.md#lc1-auto-dropped).

<a id="lc1-filter"></a>

## LC1 – GUI-Dateifilter lokal abgesichert (05.11.2026)

Nach Nutzerfreigabe die gezielte Filterkorrektur umgesetzt: Im GUI-stdout-
Modus wählt `--postpro` anhand der Beschreibung oder des vollständigen
Filtertexts genau einen Postprozessor; unbekannte oder mehrdeutige Namen
scheitern. Ohne Angabe bleibt die bisherige Auswahl von Index 0 erhalten.
Die Ausgabe wird erst nach fehlerfreiem Export freigegeben. Gesammelte
Exportfehler und Exceptions verwerfen den gepufferten Programmtext.
Status 0 bezeichnet erfolgreichen Export, 1 Schließen ohne Export und 2
Import-/Exportfehler. Fehlende Eingaben öffnen keinen Ersatz-Dateidialog;
Start-Exporte schließen ohne anschließenden leeren Eventloop ab.

Nachweis im Windows-Checkout: 12 neue reale Qt-Prozessregressionen unter
PyQt5 und erneut unter PyQt6 bestanden (24 Ausführungen). Sie prüfen den
tatsächlichen Argumentparser, DXF mit Leerzeichen im Pfad, Qt-Eventloop und
Fensterschließen, Profile unabhängig von Dateireihenfolge, Standardauswahl,
unbekannte/mehrdeutige Profile, fehlende/ungültige DXF, echten Drill-/Pocket-
Planungskonflikt und injizierte Exportexception mit Teilausgabe. stdout/stderr
und Prozessstatus werden von außen geprüft. Die zwei vorhandenen GUI-/CLI-
Dateiexportregressionen bestanden ebenfalls unter beiden Bindungen (vier
Ausführungen). Neue Filterregressionen sind in der Fast-Suite registriert.

### Reproduzierbarer lokaler Prüfnachweis

Prüfdatum: **05.11.2026**, Windows, Python 3.11. Geprüft wurde der geänderte,
noch nicht committete Arbeitsstand auf Basis von `7864ba2`. Die Tests starten
isolierte Unterprozesse mit temporärem Benutzer-/Konfigurationsverzeichnis
und `QT_QPA_PLATFORM=offscreen`; die Timer ersetzen die Nutzeraktion.

| Umgebung | Filterprozesse | Vorhandener GUI-/CLI-Dateiexport | Ergebnis |
| --- | --- | --- | --- |
| PyQt 5.15.8 / Qt 5.15.2, System-Python | 12 Tests | 2 Tests | 14 bestanden |
| PyQt 6.12.0 / Qt 6.12.0, `.tox/package-build` | 12 Tests | 2 Tests | 14 bestanden |

Ausgeführte Aufrufe aus dem Repository-Verzeichnis (PowerShell):

```powershell
$env:DXF2GCODE_QT = '5'
python -m unittest discover -s tests -p dxf2gcode_linuxcnc_filter_test.py -v
$env:PYTHONPATH = 'tests'
python -m unittest dxf2gcode_mainwindow_workflow_test.TestMainWindowWorkflow.test_mainwindow_load_edit_preview_and_export dxf2gcode_test.TestDXF2Gcode.test_quiet_cli_exports_real_dxf_without_gui_shutdown_errors -v

$env:DXF2GCODE_QT = '6'
.tox/package-build/Scripts/python.exe -m unittest discover -s tests -p dxf2gcode_linuxcnc_filter_test.py -v
.tox/package-build/Scripts/python.exe -m unittest dxf2gcode_mainwindow_workflow_test.TestMainWindowWorkflow.test_mainwindow_load_edit_preview_and_export dxf2gcode_test.TestDXF2Gcode.test_quiet_cli_exports_real_dxf_without_gui_shutdown_errors -v
```

Alle vier abschließenden Testaufrufe meldeten `OK` (28 Testausführungen
insgesamt). Die Registrierung in der Fast-Suite ist kein Nachweis eines
vollständigen Fast-Suite-Laufs. `git diff --check` bestand ebenfalls.
Für diese Ergänzung des Abschlussnachweises wurden die bereits bestandenen
Tests nicht erneut ausgeführt.

### Abschlussstatus und verbleibende Grenzen

**Lokale Softwarekorrektur abgeschlossen.** Die Status-/Ausgabeverträge sind
durch echte Qt-Prozesse geprüft; die Verwendung in einer laufenden AXIS-
Sitzung und Linux-Desktop-Integration sind dadurch nicht nachgewiesen.

Keine neuen GUI-Texte, keine Übersetzungsänderung. Keine Vollsuite, Builds,
Debian-/SSH-, LinuxCNC- oder Maschinenläufe. Kein Commit beauftragt.
[Einrichtungshinweise und Grenzen](../documentation-notes/linuxcnc-integration.md#lokal-umgesetzter-gui-filter)
bleiben von der noch offenen [LinuxCNC-Abnahme](toolpath-refactoring-completed.md#lc1-auto-dropped)
getrennt; ein automatischer CLI-Filter wurde nicht ergänzt.

<a id="lc1-axis"></a>

## LC1 – Reale AXIS-Filterabnahme auf Debian (05.11.2026)

Nach ausdrücklichem Auftrag auf `christian@192.168.178.183` (Host
`chriskodxf2gcode`) geprüft: Debian 13, Kernel 6.12.113+deb13-amd64,
Python 3.13.5, LinuxCNC 2.9.4 (`1:2.9.4-2+deb13u1`), PyQt 5.15.11 /
Qt 5.15.15. Die notwendigen Debian-Pakete wurden vom Nutzer installiert.

Eigene Kopie der mitgelieferten `sim/axis/axis_mm.ini`, separates HOME,
eigenes dxf2gcode-Profil und Xvfb-Anzeige verwendet. LinuxCNC meldete
`Using POSIX non-realtime`; ausschließlich Simulations-HAL geladen.
AXIS öffnete die eigene 20×10-mm-DXF mit Leerzeichen im Pfad über `[FILTER]`.
Ein protokollierender Wrapper startete den tatsächlichen Quellcode-Einstieg
mit `--cfg lc1 --postpro "LinuxCNC LC1 selected"` und reichte dessen stdout,
stderr und Exitstatus weiter. Export/Abbruch wurden per echten Qt-Tastenkürzeln
ausgelöst; keine AXIS-/Qt-Mocks. Der gewählte Postprozessor stand hinter einem
anderen Profil in der Dateireihenfolge.

Der erste Lauf fand einen echten Interpreterfehler: Die Versionskopfzeile
enthielt einen verschachtelten Kommentar `(Version: … (Py…) …)`. AXIS meldete
`Nested comment found`. Runtime-Metadaten innerhalb dieser Kommentarzeile
verwenden nun eckige Klammern. Die 24 fokussierten Postprozessorprüfungen
einschließlich neuer Regression bestanden unter Windows/PyQt5; danach
derselbe AXIS-Lade-/Exportweg mit korrigiertem Quellstand erfolgreich geprüft.

| Reale AXIS-Prüfung | Ergebnis |
| --- | --- |
| DXF laden, Export, Rückkehr zur Vorschau | Status 0, 910 Byte G-Code, richtiger Postprozessor, Rechteck-Werkzeugbahn sichtbar, kein Fehlerdialog |
| Fenster ohne Export schließen | Status 1, stdout leer, AXIS zeigt Filterfehler |
| Unbekannter Postprozessor | Status 2, stdout leer, AXIS zeigt Filterfehler |
| Ungültige DXF | Status 2, stdout leer, AXIS zeigt Filterfehler |

Bei allen Fehler-/Abbruchfällen blieb das gültige Programm geladen.
AXIS/Interpreter blieben in ESTOP/IDLE und sämtliche Positionen unverändert
bei null. Kein Programmstart, Homing, Jogging oder Maschinenbewegung.
Die gestarteten AXIS-/LinuxCNC-/Xvfb-Prozesse wurden anschließend beendet.

Remote-Nachweise: `/home/christian/dxf2gcode-test-work/runs/lc1-axis-20261105`
mit `report.json`, `filter.py`, `run_cases.py`, Simulations-INI, G-Code,
Logs und Vorher-/Nachher-Screenshots. Lokal gesichert unter
`.tox/lc1-axis/evidence/` sowie als `.tox/lc1-axis/evidence.tar.gz`.
Snapshot-SHA-256 vor der Kopfzeilenkorrektur:
`78ed6959392b6b4abb3ae55201dcd305527bcf670be8d33ef74e1e1d01148c5a`.
SHA-256 des korrigierten, lokal mit dem geprüften Remote-Modul abgeglichenen
`postprocessor.py`:
`5e89a5dd5d61c65339a8da9af3b6761194d62cd0204b789c7b485a8360e887c3`.

**Abgenommen ist der interaktive Filter-/Vorschauablauf in dieser realen
AXIS-Simulation.** Keine Maschinen-/Materialfreigabe, Paket-/Wheel-Abnahme,
GMOCCAPY-, Wayland- oder Debian/PyQt6-Abnahme. Keine Vollsuite oder Builds.
[Anwenderanleitung](../../docs/user-guide/linuxcnc-axis.md) ergänzt;
[optionaler automatischer CLI-Filter](toolpath-refactoring-completed.md#lc1-auto-dropped)
bleibt eine gesonderte Entscheidung. Kein Commit erstellt.

<a id="ci1"></a>

## CI1 – Paketpipeline implementiert und aktiviert (02.11.2026)

**Ergänzung – eindeutiger Release-Workflow (03.11.2026):** Datei und Link heißen
jetzt `publish-release.yml`, der Anzeigename bleibt **Publish release**.
Develop-Versionsnummern werden aus den veröffentlichten eigenen Releases
weitergezählt und sind nicht mehr an Workflow-Dateiname oder Laufzähler
gebunden. Wiederholungen veröffentlichter Runs behalten ihre Version;
unterbrochene Drafts bekommen beim Wiederbefüllen passende Metadaten.
13 gezielte Release-Regressionen und die Actionlint-Prüfung bestanden.
Ein neuer Release wird durch diese Umbenennung nicht gestartet.

**Ergänzung – getrennte Workflows:** **Tests and package checks** prüft Pushes
auf `develop` und PRs nach `develop` automatisch. **Publish release** startet
Develop-Veröffentlichungen manuell und Stable-Veröffentlichungen per Tag.
Beide nutzen dieselben Tests und Paketprüfungen über einen gemeinsamen
`workflow_call`-Ablauf. Lokal bleibt der Fast-Hook vor Commits erhalten.
Der Release-Versionszähler ist inzwischen von der Workflow-Kennung getrennt.
Die drei Workflow-Dateien wurden mit Actionlint geprüft;
ein manueller Release wurde durch diesen Umbau nicht gestartet.

**Ergänzung – manuelle Develop-Veröffentlichung:** Develop-Releases werden
jetzt ausschließlich über **Actions → Publish release → Run workflow →
develop** gestartet. Pushes und PRs behalten automatische Tests und
Paketprüfungen, veröffentlichen aber nicht. Stabile Releases bleiben an
passende Versionstags gebunden; Hauptschalter, Draft-Prüfung und Aufbewahrung
gelten weiter. Workflow, Manifest und Publisher erzwingen dieselbe Regel.
Zehn gezielte Release-Tests sowie Actionlint bestanden. Ein neuer manueller
Release wurde bei dieser Umstellung nicht gestartet; die früher automatisch
veröffentlichten dev10/dev11 bleiben erhalten.

**Ergänzung – Release-Texte:** Für die nächsten Veröffentlichungen ist eine
kompakte Zusammenfassung statt einer Commitliste vorbereitet. Die Vorlage
`doc/release-notes/2.0.0.md` bündelt die Highlights der Versionslinie; die
Pipeline setzt Downloadhinweise und aufklappbare Build-Details darunter.
Bestehende Releases werden dabei nicht nachträglich geändert. Die Vorlage
und der Vorschau-/Stable-Text sind durch eine gezielte Regression geprüft.
Die Zusammenfassung wurde anhand der Git-Historie seit Merge `f5520a8`
(11.10.2026) um die früheren Geometrie-, Fräs-, Profil-, Werkzeugwechsel-,
Bedienungs- und Prüfarbeiten ergänzt. Sie erklärt 2.0 als neue Entwicklungslinie
aus Architekturumbau und erweiterter Bearbeitung, begleitet vom GitHub-Umzug;
Migrations- und Kompatibilitätsgrenzen bleiben ausdrücklich benannt.

Der am 01.11.2026 vereinbarte Download-Ablauf ist implementiert. Am
02.11.2026 wurden SemVer mit Ziel **2.0.0**, Windows x64 mit Python 3.11 /
PyQt5 ohne Signatur sowie die Aktivierung auf GitHub freigegeben.
`CI_RELEASES_ENABLED=true` ist gesetzt; die Änderungen sind auf `develop`.

- Quellarchiv und Wheel entstehen außerhalb des Checkouts aus dem getesteten
  Commit; Windows-ZIP und benutzerbezogener MSI aus genau diesem Quellarchiv.
  Herkunft, Übersetzungen und beide Qt-Varianten werden mitgeliefert.
- `2.0.0.devN` und `v2.0.0` sind getrennte Kanäle. MSI nutzt gültige Zahlen,
  eigene Upgrade-IDs und getrennte Installationsordner. Datum und Commit stehen
  in Dateinamen beziehungsweise Wheel-Build-Tag und im Release-Manifest.
- Veröffentlichung erst nach Tests und Paketprüfungen über einen vollständig
  hochgeladenen Draft mit SHA-256-Prüfsummen. Develop ersetzt kein stabiles
  „Latest“. Fehlgeschlagene und überholte Builds veröffentlichen nichts.
- Temporäre Testpakete verfallen nach sieben Tagen. Nach Veröffentlichung
  werden die doppelten Actions-Kopien dieses Runs entfernt. Bereinigung
  begrenzt sich auf die letzten zehn eigenen Develop-Releases und deren
  verifizierte Tags; Stable, fremde Previews und Drafts bleiben erhalten.
- Tarif und Speicher vor Aktivierung geprüft; keine Build-Caches. Windows ist
  ausdrücklich unsigniert. Regeln und Bedienhinweise stehen in der
  [Release-Pipeline](../release-pipeline.md) und den
  [Dokumentationsnotizen](../documentation-notes/downloads-and-versions.md).

**Nachweis:** [GitHub-Lauf 41499754219](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41499754219)
für Commit `5b348ec` ist vollständig erfolgreich: Python-/Qt-Vollmatrix,
Wheel in frischen Qt5-/Qt6-Umgebungen einschließlich DXF-Export,
Windows-ZIP sowie real installierter MSI mit GUI-Start und DXF-Export.
Das [Develop-Prerelease 2.0.0.dev10](https://github.com/dxf2gcode/dxf2gcode/releases/tag/develop-ci-41499754219)
wurde veröffentlicht; temporäre Paketkopien wurden danach entfernt.
Lokal bestanden **206 Fast-Tests über den Commit-Hook**, acht gezielte
Release-Regressionen und die Actionlint-Prüfung. Keine lokale Vollsuite,
Release-/MSI-Installation oder Debian-/SSH-Abnahme gestartet.

Die ersten GitHub-Läufe blockierten die Veröffentlichung bei Test- und
Paketprüffehlern wie vorgesehen. Veraltete Testannahmen wurden an das aktuelle
Projektformat, den Vorschau-Vordergrund und die Schleppmesser-Exit-Vorschau
angepasst. Staging erhält die Build-Werkzeuge; der gemischte Qt-Build wählt
explizit den Qt6-Compiler. Die Windows-Prüfung kontrolliert den bestehenden
G-Code-Kopf mit Version und Commitdatum und die vollständige Commitkennung
in den Paket-Metadaten.

**Grenzen:** PR-Artefakte und der erste stabile Tag sind noch nicht real
abgenommen; für diesen Auftrag wurde kein stabiler Tag erzeugt. Retention
ist mit kontrollierten Daten einschließlich Schutz stabiler Releases geprüft.
Codesignierung, M1 und physische Maschinenabnahmen bleiben separat offen.
Die [aktive Todo](../todo.md#ci1) enthält ausschließlich diese Restarbeiten.

<a id="doc1-wp1"></a>

## DOC1/WP1 – First DXF to G-code ausgearbeitet (03.11.2026)

Auf dem vorgesehenen Inhaltsbranch `docs/wiki-migration` ist das englische
Einstiegskapitel `docs/getting-started/first-dxf-to-gcode.md` erstellt und in
Navigation, Home und Introduction verlinkt. Installation bleibt unverändert.
Eine eigene 20 × 10-mm-DXF mit Ursprung (0,0) und zwei aktuelle MainWindow-
Aufnahmen erklären Import, Enable/Auswahl, G40, Parameter, Vorschau und den
normalen Export ohne Optimierung. Das frische Anwendungsprofil `wp1-demo`
und der mitgelieferte LinuxCNC-Postprozessor sind ausdrücklich benannt.

**Prüfung:** Eine geschlossene Kontur mit vier Segmenten und korrekten
Millimetereinheiten wurde über den realen Import geladen. Der finale Export
wurde über `actionExportShapes` / `exportShapes` / `ExportToolpath` in einem
isolierten Profil verfolgt. G21/G90/G40, alle Rechteckpunkte und Tiefen −0,5 /
−1 mm sowie Rückzug 15 mm / Sicherheitsabstand 3 mm sind im Ergebnis geprüft.
Windows, Python 3.11.1, PyQt5 5.15.11, Qt 5.15.2; Anwendungsbasis `935bfc8`.
Screenshots sind visuell geprüft; der strikte Zensical-Build bestand.

**Herkunft:** Neue Texte, eigene Zeichnung und neue Widget-Aufnahmen; keine
fremden Wiki-Texte oder Medien übernommen. Rechte und Umgebung stehen in
`docs/assets/examples/first-dxf/README.txt`, fachliche Zusammenhänge in den
[WP1-Notizen](../documentation-notes/first-dxf-workflow.md).

**Veröffentlichung:** Mit WP2 als `5cee4ad` committet, vom Anwender zur
Veröffentlichung freigegeben und über
[PR #1](https://github.com/dxf2gcode/dxf2gcode/pull/1) nach `develop` integriert
(`39351f8`). Der Pages-Build und das Deployment sind erfolgreich abgeschlossen;
siehe WP2-Veröffentlichungsnachweis unten.

**Grenzen:**
Keine reale Maschinenfahrt, kein Release-/MSI-Build, keine Debian-/SSH- oder
Paketabnahme; der vereinbarte spätere 2.0.0-Release bleibt davon unabhängig.

<a id="doc1-wp2"></a>

## DOC1/WP2 – Oberfläche, Import und Projekte dokumentiert (03.11.2026)

Zwei neue englische Anwenderkapitel erklären Fensterbereiche, 2D-Navigation,
Auswahl gegenüber Aktivierung, Eingabeformate und externe Konverter sowie
Speichern/Öffnen von D2G-Projekten. Sie verwenden WP1s eigene Rechteckzeichnung
und den bestehenden aktuellen Screenshot. Navigation, Home und Introduction
verlinken beide Kapitel; es werden keine fremden Wiki-Inhalte übernommen.

Die Anleitung unterscheidet Geometrie, Vorbereitung und G-Code. Sie benennt
den gespeicherten Zeichnungspfad, die manuelle Neuzuordnung fehlender Dateien,
Reload ohne Zusage einer Einstellungserhaltung und die Grenzen des
Geometrieabgleichs nach CAD-Änderungen. Ein Schrittbeispiel speichert die
WP1-Vorbereitung als `rectangle-20x10-mm.d2g` und öffnet sie wieder.

**Prüfung:** Aussagen gegen aktuelle Menütexte, 2D-Ereignisse, Importpfad,
Zeichnungsmodell, Projektserialisierung/-wiederherstellung und Codec verglichen;
vorhandene Import-/Projekt-Testverträge gelesen. Strikter Zensical-Build und
Dokumentationslinks geprüft. Keine Anwendung geändert; keine neue Quellcode-
oder Fast-Suite gestartet. Die Dokumentationsausnahme steht jetzt in AGENTS.md
und den Arbeitsvereinbarungen; die persistente Git-Hook-Einstellung bleibt
unverändert.

**Veröffentlichung:** Am 03.11.2026 vom Anwender freigegeben. PR #1 ist gemergt;
der [Pages-Lauf 41712224311](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41712224311)
hat Build und Deployment erfolgreich abgeschlossen. Beide WP2-Kapitelseiten
wurden direkt abgerufen (HTTP 200, erwartete Überschriften vorhanden).
Die PR-Dokumentationsprüfung, vier Python-/Qt-Testläufe und die Python-
Paketprüfung waren vor dem Merge erfolgreich; der automatisch gestartete
Windows-ZIP-/MSI-Lauf war dabei noch nicht abgeschlossen. Daraus wird keine
neue Windows-Paketabnahme abgeleitet.

**Grenzen:** Codegestützte Dokumentation, kein neuer GUI-Roundtrip, keine
PDF-/PS-Konverter-, Fremdplattform- oder Maschinenabnahme. Fachliche Quellen und
weitere Redaktion: [WP2-Notizen](../documentation-notes/interface-import-projects.md).

<a id="doc1-wp3-wp5"></a>

## DOC1/WP3–WP5 – Reihenfolge und Bearbeitung dokumentiert (03.11.2026)

Sieben neue englische Seiten ergänzen den User Guide auf
`docs/user-guide-wp3-wp5`:

- **WP3:** Shapes, Layers and Tree Order; Route Optimization. Manuelle
  Baumreihenfolge, Export, Routenanzeige und Optimierung sind einzeln erklärt.
  Vorher-/Nachher-Tabellen zeigen beide bestehenden Constraint-Modi und
  Custom-G-Code-Positionen bei einem ausdrücklich angenommenen Optimierergebnis.
- **WP4:** Machining Parameters; Contours, Pockets and Drilling. Einheiten,
  vorzeichenbehaftete Tiefen, mehrere Zustellungen, gemeinsame/gemischte Werte,
  Werkzeugübersteuerungen und gezielte Rückkehr zu Vorgaben sind beschrieben.
  Taschen-/Bohr-Eignung, Moduswechsel und blockierende Projektkonflikte sind
  gegen den aktuellen Code abgeglichen.
- **WP5:** Cutter Compensation and Lead Moves; Preview and Export; Toolpath
  Diagnostics. Maschinen-/Softwarekompensation, Seiten/Richtung, Lead-Methoden,
  geschlossene Überfahrt, 2D-Farben, Profilabhängigkeit und fehlende oder
  ungültige Geometrie werden mit konkreten Einstellbeispielen erläutert.

**Material:** Eigene metrische DXF mit Rechteck A, Kreis B und offener Kontur C
sowie zwei aktuelle MainWindow-Aufnahmen. Die Kompensationsaufnahme verwendet
WP1s Rechteck mit G41 außen, Werkzeug Ø2 mm, Lead-Radius 2 mm, geradem Anteil
3 mm und Überfahrt 1 mm. Werkzeugvorgaben und angezeigte Werte stimmen überein.
Herkunft: `docs/assets/examples/machining-basics/README.txt`; keine fremden
Wiki-Texte, DXFs oder Bilder übernommen.

**Prüfung:** Aktuelle Baum-/Optimierungs-, Parameter-, Modus-, Lead-, Offset-,
Planungs- und Vorschaupfade sowie relevante bestehende Testverträge gelesen.
Die Beispiel-DXF wurde im isolierten echten MainWindow als drei Konturen
importiert (zwei geschlossen, eine offen); das kompensierte Rechteck besitzt
einen Plan ohne Fehlerdiagnosen. Screenshots visuell geprüft. Windows,
Python 3.11.1, PyQt5 5.15.11, Qt 5.15.2; Quellbasis `6c4bcc9`.
Strikter Zensical-Build, lokale Dokumentationsverweise und Diff-Format geprüft.

**Veröffentlichung:** Commit, Integration und Veröffentlichung zur ersten
Ansicht sind jetzt beauftragt. Veröffentlichungsergebnis siehe Nachtrag unten.

**Grenzen:** Kein Quellcode geändert, keine Fast-/Vollsuite, kein neuer
G-Code-Export, keine Konverter-, Paket-, Fremdplattform- oder Maschinenabnahme.
Die Optimierungstabellen sind eine belegte Ordnungsregel, kein Versprechen
eines bestimmten stochastischen Suchergebnisses. Quellen und Redaktionshinweise
stehen in den [WP3–WP5-Notizen](../documentation-notes/order-machining-and-preview.md).

<a id="doc1-wp6-wp8"></a>

## DOC1/WP6–WP8 – Maschinenarten, CLI und Konfiguration dokumentiert (03.11.2026)

Sieben weitere englische Kapitel ergänzen den lokalen User Guide:

- **WP6:** Tabs and Breaking Layers, Machine Modes und Drag-knife Cutting.
  Eigene Haltesteg-DXF und Tiefendiagramm erklären absolute Steg-Z-Werte,
  Last-pass/Explizit/Never und die Grenze bereits abgetragenen Materials.
  Fräsen, der tatsächliche Dreh-Ausgabefaktor und Schleppmesser sind getrennt
  dargestellt. Die Messeranleitung umfasst Offset, Ausrichtung, Schwenkhöhe,
  Tiefenschnitte, XYZ-Rampen, offene Umkehr, Rampenausgleich und Überfahrt.
- **WP7:** Command-line Usage und Troubleshooting/FAQ. Reale Flags,
  vollständige Headless-Aufrufe, Profilpriorität, Postprozessorbeschreibung
  statt Dateiname, aktueller Fallback bei unbekannter Beschreibung,
  Fehlerstatus und ungespeicherte GUI-Werte sind erläutert. Support verweist
  auf GitHub Issues, das bestehende Forum und den separaten Installer-Tracker.
- **WP8:** Application Settings und Layer Naming Rules. Echte Seitenzuordnung,
  Windows-/Linux-Pfade, Profile, ausgewählte 9.19-Vorgaben, Sofortwirkung/
  Neustart, Versionsprüfung sowie `.bad`-Wiederherstellung sind erklärt.
  Präfixe, Aliaslisten, Parameterreihenfolge, Lead-Nummerierung und
  IGNORE-Deaktivierung gegenüber Importfilter werden unterschieden.

**Prüfung:** Aussagen gegen aktuelle CLI-, Profil-, Layer-, Break-, Knife-,
Formatierungs- und Konfigurationspfade sowie vorhandene Fachnotizen geprüft.
`python source/dxf2gcode.py --help` ausgeführt. Die eigene DXF wurde im
isolierten echten MainWindow als zwei geschlossene Konturen importiert;
Frästiefe −1,5 mm, Zustellung −0,5 mm und Steg-Z −1 mm bestätigt. Das zweite
Layernamen-Beispiel ergibt Werkzeug 1, Ø2, Radius 2, Länge 3, gerade Leads und
Überfahrtlänge 1. Zwei echte ConfigWindow-Aufnahmen sowie das eigene SVG-
Diagramm visuell geprüft. Strikter Zensical-Build und lokale Links geprüft.
Windows, Python 3.11.1, PyQt5 5.15.11, Qt 5.15.2; Quellbasis `6c4bcc9`.

**Quellen:** Eigene Texte und Assets; historische Messerreferenzen direkt
geprüft und nur verlinkt, ohne deren Bilder/Dateien zu übernehmen. Herkunft und
Umgebung stehen in `docs/assets/examples/tabs/README.txt`; Fachquellen und
weitere Hinweise in den [WP6–WP8-Notizen](../documentation-notes/modes-cli-and-configuration.md).

**Veröffentlichung:** Commit, Integration und Veröffentlichung zur ersten
Ansicht sind jetzt beauftragt. Veröffentlichungsergebnis siehe Nachtrag unten.

**Grenzen:** Keine Fast-/Vollsuite, keine
CLI-Beispielexporte, keine Fremdplattform-, Konverter-, Paket- oder
Maschinenabnahme. Die Drehbeschreibung belegt die vorhandene Formatierung,
kein abgenommenes Drehprofil. Das fehlende historische `Spant.png` bleibt
separat offen; das neue Stegdiagramm übernimmt dessen Herkunft nicht.

<a id="doc1-wp3-wp8-publication"></a>

## DOC1/WP3–WP8 – Öffentliche Erstansicht veröffentlicht (03.11.2026)

Der Anwender hat die Veröffentlichung aller neuen Kapitel und das Entfernen
der bisherigen Doku-Prototypseiten freigegeben. `docs/introduction.md` entfällt;
die technische Seite `docs/documentation-preview.md` ist als interne
[Website-Pflegeanleitung](../documentation-notes/documentation-site-maintenance.md)
erhalten. Navigation, Startseite und betroffene Verweise sind umgestellt.
Installation und die in Kapiteln verlinkten eigenen DXF-Beispiele bleiben.

Die vierzehn Kapitel aus WP3–WP8, die neuen Beispiele/Abbildungen und die
gesammelten Fach-/Prüfnotizen sind als `73d4503` committet und über
[PR #2](https://github.com/dxf2gcode/dxf2gcode/pull/2) nach `develop` integriert
(`f55c550`). Lokaler strikter Build, 230 lokale Markdown-Verweise und die
GitHub-Dokumentationsprüfung waren erfolgreich; keine lokale Fast-Suite.
Der [Pages-Lauf 41723317919](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41723317919)
hat Build und Deployment erfolgreich abgeschlossen. Direkt online geprüft:
alle vierzehn Kapitelseiten mit erwarteten Titeln (HTTP 200), aktuelle
Navigation, beide entfernten Prototypseiten (404) sowie beide neuen DXF-
Downloads (200). Die allgemeine automatisch gestartete Quellcode-/Paketmatrix
lief unabhängig weiter und wurde nicht als Voraussetzung für diese reine
Dokumentationsveröffentlichung abgewartet.

Diese Erstansicht
ist eine Dokumentationsveröffentlichung; WP9–WP13 und die spätere stabile
Softwareversion 2.0.0 bleiben davon unabhängig offen.

<a id="doc1-wp9-wp13"></a>

## DOC1/WP9–WP13 – Restliche Dokumentationsinhalte erstellt (04.11.2026)

19 neue englische Seiten vervollständigen die geplanten Dokumentationsthemen.
Die Website umfasst damit 38 Markdown-Seiten. Neue Navigationsgruppen
erschließen Postprozessorreferenz, Beispiele, Developer Guide und Projektseiten.
Installation/Einstieg sind passend verlinkt; die früher entfernten öffentlichen
Prototypseiten bleiben entfernt.

- **WP9:** Schema-/Dateireferenz einschließlich 8.3 und XYZ-Template,
  General/Program/Format/Zeilennummern/Custom-G-Code, Bewegungsplatzhalter
  und Werkzeugwechselvertrag. Legacy/Managed, effektive Werkzeugfolge,
  absolute Makroziele bei G91, skalare Referenzen, H-Zuordnung und
  CustomGCode-Beschränkungen sind gegen die Implementierung abgeglichen.
  Das vorhandene LinuxCNC-Manual-Beispiel bleibt mit seinen Voraussetzungen
  verlinkt; englische und deutsche Makronotizen widersprechen einander nicht.
- **WP10:** Fünf eigene Referenzseiten für Laser, Heißdraht, Drehen, DXF und
  Python. Die ersten drei waren zunächst steuerungsneutrale Fragmente und
  sind jetzt auf Hobby-Steuerungen konkretisiert (Nachtrag unten). Eigene ladbare
  DXF-Linien- und Python-Ereignislistenprofile demonstrieren Dateiausgabe.
  Es wird keine historische Fremdvorlage als aktuelles Vollprofil ausgegeben.
- **WP11:** Entwicklerinstallation, Architektur und Tests mit aktuellen
  Paketpfaden, echten Verantwortungsgrenzen und eigenem Diagramm. Python-
  Mindestdeklaration, CI-Matrix und verbleibende Qt-/Runtime-State-Kopplung
  sind getrennt beschrieben; keine öffentliche Altimport-API versprochen.
- **WP12:** Qt-/TS-/QM-Abläufe, Paket-/Windows-Build, Beiträge und Doku-Pflege.
  Compile-only und Textextraktion, beide Qt-Bindings für Releases, generierte
  Dateien, Herkunft und lokale Prüffreigaben sind erklärt. CONTRIBUTING und
  Tests-README entsprechen jetzt den aktuellen CI-Namen und der Doku-Ausnahme.
- **WP13:** Downloads/Versionen/Retention, Support, Lizenz/Credits und Historie.
  Stabiles 2.0.0 bleibt an die gesamte Todo gebunden. Es werden weder
  ungeklärte Wiki-Originale noch persönliche Roharchive veröffentlicht.

**Prüfung:** Strikter Zensical-Build erfolgreich; lokale Markdown-Verweise
und Navigation geprüft. Zwei neue Demoprofile über `MyPostProConfig` in einem
temporären Profil geladen: keine Versionsabweichung oder Default-Recovery.
Synthetische DXF-LINE-Ausgabe auf Gruppenpaare/Koordinaten geprüft; Python-
Program-Records mit `ast.parse` geprüft, nicht ausgeführt. Architektur-SVG
gerendert und visuell geprüft. Bestehendes Website-Logo und Symbol zusätzlich
visuell kontrolliert. Projekt, Releases, Issue-Auswahl, Linux-Installer und
Forum jeweils direkt erreichbar (HTTP 200). Offizielle LinuxCNC-G43-/M6-
Manualtoolchange-Quellen geöffnet und mit den Aussagen verglichen.

**Herkunft:** Neue Texte, eigenes Diagramm und eigene Beispieldateien, keine
unklar lizenzierten Wiki-Texte/-Profile/-Bilder übernommen. Anwendungsversion
als Quellbasis `bf1ac6d`; Windows, Python 3.11.1, PyQt5 5.15.11, Qt 5.15.2 für
Profil-/Template-/SVG-Prüfung. [Assetnachweis](../../docs/assets/examples/postprocessors/README.txt)
und [Fachquellen](../documentation-notes/postprocessors-and-development.md).

**Veröffentlichung (04.11.2026):** Auf ausdrücklichen Auftrag als `b32c89e`
committet und über [PR #4](https://github.com/dxf2gcode/dxf2gcode/pull/4) nach
`develop` integriert (`0d47323`). Die PR-Dokumentationsprüfung war erfolgreich.
Der [Pages-Lauf 41908888199](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41908888199)
hat Build und Deployment erfolgreich abgeschlossen. Alle 19 neuen Seiten mit
erwarteten Überschriften, fünf Profil-Downloads, die neue Dreh-DXF und die
aktuelle Startseitennavigation direkt online geprüft (HTTP 200). Damit sind
alle geplanten Kapitel WP1–WP13 veröffentlicht. Die automatisch gestartete
allgemeine Quellcode-/Paketmatrix lief unabhängig weiter.

**Grenzen:** Keine neuen Anwendungs-/Test-/Tooländerungen,
Fast-/Vollsuite, Qt-Neugenerierung, CLI-Beispielexporte, kompletten
DXF-Reimport-/Controllerprüfungen oder Paket-/Release-/MSI-/Debian-/SSH-Läufe.
Keine Maschinen-, Material- oder frische Plattformabnahme. Konkrete
Anpassungen am realen Aufbau sowie historische Wiederverwendung benötigen
bei Bedarf einen eigenen Auftrag; ihre Grenzen sind Inhalt der fertigen Seiten.
Konkrete fachliche Rückmeldungen bleiben in der Todo.

### WP10-Nachtrag: konkrete Hobby-Steuerungsbeispiele (04.11.2026)

Auf Wunsch des Anwenders sind die Beispiele jetzt auf Grbl 1.1 für einen
DIY-Diodenlaser sowie LinuxCNC 2.9 für eine parallele XYUV-Heißdrahtmaschine
und eine lineare Z/X-Durchmesser-Drehbahn konkretisiert. Drei vollständige
eigene `.cfg.example`-Downloads und eine eigene offene Stufenkontur ergänzen
die vorhandenen DXF-/Python-Demos; insgesamt stehen fünf ladbare Profile bereit.

Die Grbl-Demo verwendet M4 S0 beim Schnitt und M5 S0 bei Travel/Ende, ohne
Fräsdrehzahl als Leistung, M6, Kühlmittel oder Z. Heißdraht bildet bei Rapid
und Schnitt X=U/Y=V ab, ohne Heizung oder unabhängige Konusplanung. Die
Drehdemo verwendet G18/G7/G94/G97, linearisiert Bögen und startet weder
Spindel noch Werkzeugwechsel; eine freie Rückzugsbahn ist nicht vorgegeben.
Offizielle Grbl- und LinuxCNC-2.9-Quellen sind auf den Seiten verlinkt.

**Prüfung:** alle drei neuen Profile im isolierten temporären Profil geladen,
keine Default-Recovery. Synthetische Formatierung prüft XYUV-Koordinaten,
Z/X-Durchmesserwerte, S0 und das Fehlen unerwünschter M-/Z-Ausgabe. Die neue
metrische Dreh-DXF importiert als eine offene Kontur mit drei Linien,
Z-Ausdehnung −20…0 und Radius 3…5 mm sowie einer initialisierten Planerpassfolge.
Strikter Dokumentationsbuild und lokale Verweise geprüft. Kein vollständiger
Anwendungsexport, Controller-Interpreter, Materialversuch oder Maschinenlauf.
Commit und Veröffentlichung sind mit WP9–WP13 abgeschlossen (Nachweis oben).

## Postprozessorprofile vollständig als Code anzeigen (04.11.2026)

Auf allen fünf Beispielseiten werden die bisher nur herunterladbaren Profile
zusätzlich vollständig als hervorgehobener INI-Codeblock mit Kopierfunktion
angezeigt. Die bestehenden Downloads bleiben erhalten. Snippet-Einbindung
verwendet dieselben `.cfg.example`-Dateien; es gibt keine separat gepflegte
Konfigurationskopie in den Markdown-Seiten. Fehlende Quelldateien werden beim
Build als Fehler behandelt.

**Prüfung:** Strikter Zensical-Build erfolgreich. In allen fünf erzeugten
HTML-Seiten den vollständigen Codeblock nach HTML-Dekodierung mit der
Download-Quelldatei verglichen: identischer Inhalt, Kopierfunktion aktiviert,
keine unaufgelösten Include-Anweisungen. Keine Anwendung oder Profile geändert,
keine Quellcode-/Fast-Suite nötig. Der Dokumentationscommit für diese
verbliebenen Änderungen wurde am 06.11.2026 beauftragt; Veröffentlichung
und ein weiterer Release sind nicht Teil dieses Commitauftrags.

## Issue-Formulare und Anhanghinweise (03.11.2026)

Bug report und Feature request sind erweitert; Documentation issue sowie
eine Auswahl mit Forum-/Installer-Links sind ergänzt. Formulare bleiben
englisch und erlauben Beschreibungen auf Englisch oder Deutsch. Vorhandene
Labels werden verwendet. Freie Issues sind für normale Nutzer deaktiviert;
Nutzer mit Schreibrechten behalten die Option „Maintainers only“. Im Fehlerformular
sind Installationsweg und Problembereich auswählbar; Maschinenkontext und
Anhänge bleiben optional.

Bei relevanten Konfigurations-/Exportfehlern werden `config.cfg` und die
tatsächlich verwendete Postprozessor-`.cfg` erbeten. Der Hinweis enthält
Windows-/Linux-Dateipfade, benannte Profile und den Link zum aktiven Ordner
in der Meldungsleiste. Die aktuelle Windows-Konfiguration liegt ebenfalls
unter `.config`, nicht AppData. ZIP dient zum Bündeln zusammengehöriger Dateien.

**Prüfung:** Drei Formulare und die Auswahlkonfiguration sind als YAML
eingelesen und auf eindeutige Feldkennungen, unterstützte Feldtypen,
Auswahlwerte, Sprachnotiz und vorhandene Labels geprüft. Ordnerkonstanten
und Profilnamensbildung sind gegen den Anwendungscode geprüft. Keine GUI-
Texte oder Übersetzungskataloge geändert; keine Vollsuite oder Builds gestartet.
**Abschluss:** Umsetzung und Veröffentlichung sind freigegeben. Die Vorlagen
werden mit Veröffentlichung dieses Commits auf dem Standardbranch aktiviert;
zur Prüfung wird kein öffentliches Test-Issue angelegt.
Material für spätere Anleitungen steht in den
[Supportnotizen](../documentation-notes/issue-reporting.md).

## Linux-Installer-Verweise (03.11.2026)

Der freigegebene Link **Linux Installer** steht direkt nach **Downloads** auf
der Organisationsseite. Im Hauptrepository ist er oben bei den Schnelllinks
und zusätzlich unter „Installation and startup → Linux installer“ ergänzt.
Beide Seiten verweisen auf das Installer-Repository mit dessen Anleitung.
Der Tooltip nennt Debian/Ubuntu, Linux Mint und Arch-basierte Systeme; die
Bezeichnung behauptet keine Beschränkung auf Debian oder Unterstützung aller
Linux-Distributionen. Grundlage ist die aktuelle Installer-README.

Profil-Commit: `3b1262a918832a3b7b906c9860c39bdadfdf8255` im Repository
`dxf2gcode/.github`. Änderungen sind reine Dokumentations-/Navigationsänderungen;
keine Installer-Ausführung, Paket-/MSI-Builds oder GUI-Textänderungen.
Die Pflegehinweise stehen in den
[Profilnotizen](../documentation-notes/organization-profile.md).

## GitHub-Organisationsseite und Logo-DXF (02.11.2026)

Die Organisationsseite <https://github.com/dxf2gcode> ist veröffentlicht.
Das neue öffentliche Repository [dxf2gcode/.github](https://github.com/dxf2gcode/.github)
enthält die englische Profil-README mit unverändertem Projektlogo, Links zu
Downloads/Dokumentation/Quellcode/Issues, drei aktuellen Anwendungsbildern und
dem Hinweis auf die Entwicklung Richtung 2.0. Commit:
`980beb53772ef9c22a1e72c92548d85dd707892b`.
Der Organisations-Website-Link führt jetzt auf die GitHub-Dokumentation.

Das Hauptbild zeigt das eigene Logo als DXF im aktuellen Programm. Weitere
Bilder zeigen Taschenfräsen und Schleppmesser mit eigenen kleinen Beispielen.
Die Aufnahmen stammen vom realen MainWindow unter PyQt5 mit isolierten
Profilen. Schriftarten, Logo-Clipping und tatsächlicher Maschinentyp wurden
bei der Bildprüfung berücksichtigt; die veröffentlichten Bilder enthalten
keine persönlichen Konfigurationspfade.

Die Logo-DXF ist zusätzlich unter `dxf/dxf2gcode-logo.dxf` als Test-/Beispiel
gespeichert: mm, 180-mm-SVG-Zeichenfläche, 46 geschlossene Konturen auf sechs
Ebenen. Text ist als Kontur enthalten; Kurven sind durch Polylinien angenähert.
Herkunft und Grenzen stehen in der zugehörigen README. Eine Download-Kopie
und die weiteren Beispiele sind im Profil-Repository veröffentlicht.

**Prüfung:** Alle drei Zeichnungen wurden über den realen Import-/MainWindow-
Ablauf geladen (46/1/1 Konturen); die Bilder wurden visuell kontrolliert.
Die öffentliche Organisationsseite enthält die neuen Texte und alle drei
Bildverweise. Bild-URLs und Organisations-Website-Link sind erreichbar.
Kein Release-/MSI-Build oder Debian-Lauf wurde gestartet.

**Abschluss:** Hauptprojekt `dxf2gcode` und der zusätzliche Installationsweg
`dxf2gcode_installer` sind beide auf der Organisationsseite angeheftet.
Die öffentliche GitHub-API bestätigt beide Einträge. Der bisherige offene
Todo-Punkt ist damit erledigt. Herkunft und Pflege stehen in den
[Dokumentationsnotizen](../documentation-notes/organization-profile.md).

## Überblick

| Abgeschlossen | Inhalt |
| --- | --- |
| Werkzeugweg-Etappen 1–6 | Planvertrag, native Strategien, Fallmatrix, Profilformatierung, gemeinsame Werkzeugwegvorschau und Entkopplung |
| Etappe 5a | Shape-spezifische Werkzeugzuordnung einschließlich Persistenz und Anzeige |
| Darstellungskorrektur | Originalgeometrie bleibt Grunddarstellung und Auswahlfläche; Werkzeugweg erscheint zusätzlich bei Auswahl in den bestehenden Farben |
| Importreihenfolge | Rückwärts importierte Kurvenketten behalten die korrekte Reihenfolge ihrer Teilstücke; rote Kontur und G40-Plan sind zusammenhängend |
| V1 / U3 / U5 | Unabhängiger 2D-Werkzeugkreis, vorbelegter Nullpunktdialog im Kontextmenü und Tastenkürzel für beide Bäume |
| U1 / U2 | Werkzeugauswahl ausrichten; Klappbuttons nach Baumzustand und Hänger-Nachbesserung |
| U4 / I2 | Konfigurierbarer Startzustand des Layerbaums; optionale Importfilter |
| R1a | Drag-and-drop-Absturzpfade und Qt5-/Qt6-Kompatibilität |
| R2 | Sichtbare Exportreihenfolge, Treeview-Synchronisierung und gemeinsame GUI-/CLI-Optimierungsmodi |
| K1 | Stabile Konfigurations-Übersetzungskontexte, Hilfetexte, Auswahlanzeigen und Maschinenmenüs in DE/FR/RU |
| D1 / D2 | Gemeinsamer Schleppmesser-Ablauf, Migration alter Tiefenwerte, bearbeitbare Schwenktiefe je Kontur und geprüfte Vorschau/Export-Verträge |
| DOC1 Phase 1 | Dokumentationsprototyp, Integration, Veröffentlichung, Branding und vorbereitete Migrationsmatrix |
| K2 | Geladene Profilwerte von Werkseinstellungen unterscheiden, schemaabhängige Tooltip-Vorgaben und GitHub-Dokumentationsverweise |
| P1 | Verwaltete Werkzeugwechsel plus vereinbarter manueller LinuxCNC-Ablauf, Standard-Abgleich und G90-/G91-Referenzen; Maschinenprüfung beim Anwender |
| K3 | Vierstellige Längeneingabe und Erhaltung genauer Originalwerte bis zur bewussten Bearbeitung; Profilformatierung bleibt maßgeblich |
| B1 / B2 | Gemeinsame Bearbeitungszustände, sichtbare Konflikte alter Projekte und korrekte Geometrieprüfung für Bohren/Pocketing |
| Versionsmetadaten | Provider, Build-Anbindung, Infofenster/G-Code-Kopf und Entfernung der alten Keywords; Paketabnahme M1 bleibt offen |
| GUI-Branding | Native Windows-Symbolgrößen, Taskleistenkennung, kompakte Infofenster-Wortmarke und Dokumentationslink |
| Vorschau und Neustart | Lead-/Überfahrtdetails über allen 2D-Konturbahnen; bestätigter Neustart nach dem Schließen der Konfiguration bei Start-Einstellungen |
| Bereinigung | `.kilo/` und erzeugte `.coverage` entfernt |

Die weiterhin geltenden [Architekturverträge](../architecture.md#weitergeltende-architekturverträge)
stehen in der aktuellen Architekturdokumentation. Dieses Archiv bewahrt
Umsetzungshistorie und damalige Prüfergebnisse.

Lokaler Commitabschluss am **02.11.2026**: `eda8e2a` ergänzt das manuelle
LinuxCNC-Profil samt Referenzausgaben; `4d061fc` enthält Übersetzungen,
GUI-Branding und den Dokumentationslink. Vor jedem Commit läuft die Fast-Suite
über den Pre-Commit-Hook: jeweils **156 Tests bestanden**. Zusätzlich bestanden
zehn gezielte Qt6-Tests für Programmstart, Konfiguration und Infofenster.

<a id="v1-u3-u5"></a>

## V1/U3/U5 – Bedienung (02.11.2026)

### V1 – Werkzeugkreis unabhängig vom Lead-in

Abgestimmt und umgesetzt zunächst für 2D, standardmäßig eingeschaltet und über
„Werkzeugkreis am Einstieg anzeigen (2D)“ ausschaltbar. Konfigurationsversion
9.19 ergänzt die persistierte Option; frühere Profile erhalten den eingeschalteten
Standard. Zeichenposition und Bounding-Box verwenden denselben Einstiegspunkt
des gemeinsamen Werkzeugwegplans, auch ohne Lead-in. Effektive Konturwerkzeuge,
Transformationen und Szenenskalierung bleiben maßgeblich. Bei Maschinenkompensation
kennzeichnet der Tooltip die nur angenäherte Fräserposition. Ein ungültiger Plan
erhält keinen erfundenen Einstiegspunkt; bestehende Fehler bleiben sichtbar.
Die Anzeige verändert weder Plan noch G-Code. Mehrere resultierende Teilkonturen
bleiben Teil der gesondert zurückgestellten Erweiterung, keine neu implementierte
Bedienmöglichkeit.

### U3 – Werkstücknullpunkt am angeklickten Punkt

„Werkstücknullpunkt hierher verschieben …“ öffnet den bestehenden Verschiebungsdialog
mit den berechneten Offsets. Standardmäßig wird nicht gefangen; es geht um den
Werkstück-/Zeichnungsnullpunkt, nicht um die Maschinenreferenz. Die Aktion ist bei
geladener Geometrie auch ohne Konturauswahl verfügbar. Sie verwendet die aktuelle
Translation und den bereits transformierten Klickpunkt. Abbrechen verändert nichts;
Bestätigen oder Bearbeiten nutzt denselben Neuladeablauf wie das Optionen-Menü.
Der normale numerische Menüweg und der Projekt-Roundtrip bleiben erhalten.
Der Dialog zeigt maximal drei Nachkommastellen bei mm und fünf bei inch.
Unveränderte Felder behalten beim Bestätigen ihren exakten internen Wert.
Die Hauptbuttons stehen als **OK – Auto – Abbrechen**, mit OK als Standard
für Enter. Bei genau einer ausgewählten Kontur ist zusätzlich
„Fangen: nächster Konturpunkt“ verfügbar. Geschlossene Konturen verwenden
Segmentanfänge, offene nur Anfang und Ende, wie die vorhandene Startpunktaktion.
Fangen berücksichtigt die aktuellen Dialogwerte und übernimmt die exakten
Fangkoordinaten unmittelbar beim Schließen des Dialogs. Ein zusätzliches OK
ist nicht erforderlich. Konturstart, Richtung und Reihenfolge bleiben erhalten;
Abbrechen ohne Fang verändert den Nullpunkt nicht.
Der gemeinsame 3D-Menüweg projiziert den Klick auf die Zeichnungsebene Z=0;
eine praktische GPU-/3D-Abnahme war nicht Teil dieser Änderung.

### U5 – Baum über Tastenkürzel vollständig ein-/ausklappen

**Strg+Umschalt+Rechts** klappt den gesamten fokussierten Baum aus,
**Strg+Umschalt+Links** klappt ihn ein. Dies gilt für Layer und Entities,
unabhängig von einer Gruppenauswahl. Es werden dieselben vollständigen
Klappaktionen und Verfügbarkeitsregeln wie bei den Buttons verwendet. In
Eingabefeldern oder bei Canvas-Fokus wird kein Baum über diese Kürzel verändert.
Die Buttons erläutern die Kürzel in übersetzten Tooltips.

### Prüfung und Dokumentationsmaterial

Je **64 fokussierte Tests unter Qt5 und Qt6 bestanden**: Lead an/aus,
G40/G41/G42 einschließlich ungültigem fehlendem Maschinen-Lead, Konturwerkzeug,
Transformationen, Kreis/BBox, unveränderte Exportausgabe, alte Profile und
Speichern/Laden der Anzeigeoption. Echte Qt-Tastenevents prüfen leere, gemischte
und vollständig geklappte Bäume sowie Eingabefokus. Der Hauptfensterablauf prüft
Nullpunkt-Dialogwerte, Abbrechen, Bestätigen, Bearbeiten, wiederholte Verschiebung,
Rotation/Skalierung/Spiegelung, mm/in, Projekt-Roundtrip und gleichen Vorschau-/Exportplan.
Zusätzliche Dialogtests prüfen die mm-/inch-Anzeige, exakte unangetastete Werte,
Enter auf OK, Buttonreihenfolge, optionalen Fang, ungültige Fang-Eingaben und
Abbrechen ohne Fang. Die Fang-Nachbesserung schließt und bestätigt den Dialog
direkt, ohne die intern übernommenen Koordinaten zu runden.
Die bestehenden Startpunktprüfungen bleiben erhalten.
DE/FR/RU-Kataloge sind gepflegt, kompiliert und mit echten Translatoren geprüft.
Werkzeugkreis ohne Lead-in und vorbelegter Nullpunktdialog wurden zusätzlich
bei 125 % unter Qt6 gerendert und geprüft. Keine Vollsuite, Paket- oder
Maschinenabnahme wurde gestartet.
Hinweise für die spätere Anleitung stehen in den
[Dokumentationsnotizen](../documentation-notes/configuration-and-preview.md#bedienung-v1-u3-u5).

<a id="d1-d2"></a>

## D1/D2 – Gemeinsamer Schleppmesser-Ablauf (02.11.2026)

Offene und geschlossene Konturen erreichen die Endtiefe über Slice-Zustellungen.
Geschlossene Umläufe bleiben ohne Zwischenrückzug kontinuierlich; nur der erste
Einstieg verwendet die externe Ausrichtung und den Lead-in. Rampenausgleich,
Überfahrt und optional genau ein zusätzlicher vollständiger Endtiefenschnitt
sind getrennte Funktionen. Offene Konturen unterstützen Rückkehr oder die
externe Umkehr über gerade Leads. Messerstellung und Rückausrichtung sind
auswählbar; auch eine unbekannte Stellung mit externer Ausrichtstrecke ist
berücksichtigt.

Ein gemeinsamer Plan steuert Vorschau und Export einschließlich XYZ-Rampen.
Der Freischalter „Geplante Messerschnitte“ entfällt. Konfiguration 9.18 und
Projektformat 1.5 migrieren alte Schwenktiefen; abweichende Werte bleiben je
Kontur bearbeitbar. Werkzeugtabellenprüfung, Übersetzungen und 2D-Ebenenfolge
sind nachgebessert. Der [abgestimmte Plan](../drag-knife-plan.md) bewahrt
Entscheidungen und historische Regressionsergebnisse, die
[Bedienungsgrundlage](../drag-knife-usage.md) die aktuellen Einstellungen.

Lokaler Abschluss mit `fa8335b`: **189 Tests im Pre-Commit-Hook** sowie
**43 fokussierte Qt6-Prüfungen** bestanden. Frühere Teilprüfungen bleiben mit
ihrem jeweiligen Stand dokumentiert. Es erfolgte keine praktische Material-,
Maschinen- oder Paketabnahme. Insbesondere garantiert die Ausrichtstrecke
keine gemessene Messerstellung; ihre Länge ist am konkreten Aufbau zu prüfen.

<a id="doc1-phase1"></a>

## DOC1 – Abgeschlossene Dokumentationsgrundlage und Phase 1

Aus der aktiven Todo übernommen am **02.11.2026**. Die folgenden Nachweise
sind historische Abschlüsse, keine neue Live- oder CI-Prüfung. Die noch offene
Inhaltsmigration und zusätzliche Abnahmen stehen ausschließlich in der
[aktiven Todo](toolpath-refactoring-completed.md#doc1-accepted). Der ausführliche
[Übergabebericht](../migration/zensical-prototype.md) bewahrt Herkunft,
Commitbezüge und Wiederaufnahmebefehle.

- [x] Technische Abnahme: Strict-Build, 167 lokale Verweise ohne Fehler,
  vier Sitemap-Adressen unter `/dxf2gcode/`, 18 Suchindexeinträge.

- [x] Visuelle Inhaltsabnahme der vier Seiten durch den Nutzer abgeschlossen.

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

- [x] [Migrationsmatrix für alle 15 Wiki-Seiten, Zielnavigation und priorisierte
  Arbeitspakete](../migration/wiki-migration-plan.md) vorhanden.

- [x] Neue Logos laut Nutzer selbst gestaltet, GPT-unterstützt, ohne fremde
  Gestaltungsbestandteile; öffentliche Projektverwendung beauftragt. Erklärung
  und Hashes in RIGHTS.md dokumentiert; keine pauschale Rechtegarantie oder
  neue allgemeine Asset-Lizenz daraus ableiten.

- [x] Pages-Ziel, Environment und ausdrückliche Deployment-Freigabe geklärt;
  `DOCS_PREVIEW_PUBLISH_APPROVED=true`. Änderungen an den Website-Dateien auf
  `develop` werden automatisch nach erfolgreichem Strict-Build veröffentlicht;
  der manuelle Workflow bleibt zusätzlich verfügbar.

- [x] Infofenster verlinkt die GitHub-Pages-Dokumentation ausdrücklich als
  Dokumentation im Aufbau; Deutsch, Französisch und Russisch sind gepflegt.

Die vier englischen Seiten sind weiterhin ein technischer Prototyp und keine
abgeschlossene vollständige Anwenderdokumentation. Rechte ungeklärter
Fremdinhalte und fehlende Medien bleiben eigenständige offene Themen.

<a id="gui-branding"></a>

## GUI-Branding und Infofenster (02.11.2026)

Das Windows-ICO enthält 15 native Größen von 16 bis 256 Pixeln. Fenster
verwenden den vollständigen `QIcon` statt eines einzelnen Rasterbildes;
der Windows-Start setzt eine stabile Anwendungskennung für die Taskleiste.
Fenstertitel und die Breite der Bearbeitungsüberschriften sind angepasst.

Die Wortmarke im Infofenster ist ein eigenes, zentriertes Bildelement mit
320 × 116 logischen Pixeln und Abstand zum Text. Qt zeichnet die vorhandene
1024-Pixel-Vorlage geglättet auf die jeweilige Bildschirmauflösung.
Der Hilfebereich verlinkt die GitHub-Pages-Dokumentation als „im Aufbau“.
Der HTML-Text und alle drei gepflegten Übersetzungen enthalten kein Logo mehr;
die kompilierten Kataloge enthalten den neuen Dokumentationslink.

Gezielte Qt5-/Qt6-Prüfungen bei 100 %, 125 % und 200 % kontrollieren Größe,
Zentrierung, Bildquelle und die drei geladenen Übersetzungen. Der ergänzte
Dokumentationslink wurde anschließend bei 125 % mit beiden Bindungen und
allen drei Sprachen geprüft. Die Darstellung
wurde anhand gerenderter Dialoge geprüft. Das sind lokale Quellprüfungen,
keine erneute Paket-/MSI- oder Maschinenabnahme.

<a id="configuration-restart"></a>

## Vorschau-Ebenen und Konfigurationsneustart (02.11.2026)

Die 2D-Szene zeichnet Lead-in, Lead-out, Überfahrt und Warnmarker nach allen
Konturbahnen im Vordergrund. Damit kann die blaue Bahn einer anderen Kontur
diese Details nicht mehr überdecken. Schleppmesser-Überfahrten verwenden
ebenfalls die Ausfahrtdarstellung. Auswahl und Sichtbarkeit bleiben maßgeblich;
Plan und G-Code werden durch die Darstellungsreihenfolge nicht verändert.

Maschinentyp und Importtoleranzen werden nach dem Übernehmen unmittelbar über
die vorhandenen Neuladeabläufe angewendet. Der Maschinenwechsel erhält die
Kontureinstellungen; geänderte Toleranzen lösen einen vollständigen Neuimport
aus. Bei gemeinsamer Änderung genügt ein vollständiges Neuladen. Unabhängige
Konfigurationsänderungen setzen keine im Optionen-Menü oder Projekt gewählten
Maschinentypen und Toleranzen zurück.

Änderungen an 2D/3D-Modus und Protokollierung zeigen nach dem Übernehmen einen
übersetzten Neustart-Hinweis. Erst nach dem
Schließen der Konfiguration wird ein neues Programm gestartet. Auf ausdrücklichen
Nutzerwunsch öffnet es ein leeres Fenster, ohne aktuelle Zeichnung oder
ungespeicherte Bearbeitungseinstellungen wiederherzustellen. Ein fehlgeschlagener
Prozessstart lässt das bisherige Fenster geöffnet. Zurückgenommene Änderungen
heben einen ausstehenden Neustart auf. Die unmittelbar umgerechnete
Konfigurationseinheit trägt keinen Neustart-Hinweis mehr.

Je **27 gezielte Tests unter Qt5 und Qt6 bestanden**. Sie prüfen echte Bildpixel bei überlappenden
Konturen, Sichtbarkeit, Warnmarker, Überfahrt, Bestätigung und Zeitpunkt des
Neustarts, fehlgeschlagenen Prozessstart, Quell-/Paketaufruf und Profilargumente.
Der Prozessstart wird im Test ersetzt; ein Paketneustart wurde nicht praktisch
ausgeführt. DE/FR/RU sind gepflegt und kompiliert; der deutsche Hinweis wurde
zusätzlich bei 125 % gerendert und geprüft.

Der ergänzte Hauptfenster-Test prüft Maschinenwechsel und Toleranzen ohne
Neustart, geänderte Vorschau und Menüanzeigen, erhaltene Konturtiefen und
genau einen Neuladevorgang bei gleichzeitigen Änderungen. Die Fast-Suite läuft
vor dem lokalen Commit `fa8335b` über den Pre-Commit-Hook: **189 Tests bestanden**.
Zusätzlich bestanden 43 fokussierte Qt6-Prüfungen.

<a id="k1"></a>

## K1 – Konfigurationsübersetzungen (02.11.2026)

Die ausgelagerten Widget-Texte sind durch `QT_TRANSLATE_NOOP` ausdrücklich
den Laufzeitkontexten `MyConfig` und `MyPostProConfig` zugeordnet. Damit
erkennen sowohl pylupdate5 als auch pylupdate6 die richtigen Kontexte.
Vorhandene Übersetzungen wurden aus den früheren Einträgen übernommen;
deutsche, französische und russische Kataloge sind gepflegt und kompiliert.

80 Schema-Hilfetexte sind im Präsentationsmodul `configuration_help.py`
extrahierbar. Die Übersetzung erfolgt erst für die Dialoganzeige; Profiltexte,
Schlüssel, G-Code und gespeicherte Werte bleiben unverändert. Anzeigen für
Maschinentyp, Einheit, Optimierungsmodus, Protokollstufe und Makrorückkehr
verwenden weiterhin die ursprünglichen internen Auswahlwerte.
„&Lathe“ ist im deutschen Maschinenmenü nun „&Drehmaschine“; die Maschinenmenüs
aller drei Sprachen wurden mit den tatsächlich verbundenen Aktionen geprüft.
Der Qt6-Extraktionsweg berücksichtigt jetzt auch die `.ui`-Datei.

Fokussierte Abnahme unter Qt5 und Qt6: aufgebaute und geöffnete Anwendungs- und
Postprozessor-Dialoge mit echten QM-Translatoren, Labels, Hilfe, Auswahlwerte,
unveränderte Konfigurationen, Menüaktionen und erneute Extraktion nach einem
Dateiumzug. Der Test prüft auch, dass neue Schema-Hilfetexte nicht unbemerkt
ohne extrahierbaren Quelleintrag bleiben. K2 wurde anschließend separat
abgeschlossen, siehe unten.

<a id="k2"></a>

## K2 – Profilwerte und Werkseinstellungen (02.11.2026)

Kurze Beschriftungen ersetzen den pauschalen Zusatz „(default)“. Die Felder
zeigen weiterhin die gespeicherten Werte des geladenen Profils. Tooltips
ermitteln die Vorgabe für neue Profile direkt aus dem Konfigurationsschema;
ein Hinweis erklärt, dass neue Profile Werkseinstellungen erhalten und das
aktive Profil nicht kopieren. Fachliche Vorgaben sind unverändert.

Die Hilfen unterscheiden Startzustand, aktuelle Menüauswahl und Vorgaben
für neu importierte Konturen. Die Optimierungsfreigabe gilt für neue Konturen;
bestehende Freigaben bleiben erhalten. Frühere Wiki-Verweise in den gepflegten
Konfigurationshilfen führen jetzt zur
[GitHub-Dokumentation](https://dxf2gcode.github.io/dxf2gcode/).
Ausführliche Erklärungen stehen beim Überfahren der Felder und Labels bereit.

Je **13 fokussierte Tests unter Qt5 und Qt6 bestanden**: neue temporäre
Profile über den Hauptfensterablauf, Speichern und erneutes Laden individueller
Werte, Startmenüs, Dialoganzeige, Konturvorgaben und Dokumentationsverweise.
DE/FR/RU-Kataloge sind gepflegt, kompiliert und mit echten Translatoren geprüft.
Die Prüfungen zeigten keinen zusätzlichen Fehler beim Anlegen oder Laden.
Dies ist keine Vollsuite- oder Paketabnahme.

<a id="p1-linuxcnc"></a>

## P1 – Manueller LinuxCNC-Ablauf (02.11.2026)

Der Nutzer hat LinuxCNC ohne ATC als Ziel benannt und den Abgleich mit
Standard-G-Code sowie Softwaretests beauftragt. Praktische Tests an den
jeweiligen Maschinen übernehmen die Anwender. Die vorher implementierte
Makro-Erweiterung wird für diesen vereinbarten Umfang durch einen
[offiziell belegten LinuxCNC-Abgleich](../linuxcnc-manual-tool-change.md) ergänzt.

Die optionale Makro-Erweiterung ist ebenfalls implementiert. Manueller Wechsel
und ATC verwenden weiterhin `Program.tool_change`; Wechselparameter,
erklärter Rückkehrzustand, H-Zuordnungen und G91-Wiederaufnahme sind verfügbar.
Alte Profile behalten ihre bisherige Ausgabe. Die
[Makro-Anleitung](../tool-change-macros.md) und der
[Werkzeugwechsel-Vorschlag](../tool-change-proposal.md) bewahren Einrichtung,
Herleitung und Grenzen. Der verwaltete Ablauf ist auf die dort beschriebenen
Fräsfälle begrenzt; Controller- und Maschinenabnahmen erfolgen beim Anwender.

Das separat ladbare `doc/examples/linuxcnc-manual.cfg.example` verwendet
manuelles M6 mit vorbereiteter Werkzeugtabelle, danach G43 ohne H=T-Annahme,
Z-Positionierung vor XY und einen erklärten Rückkehrzustand. Vollständige
Referenzausgaben mit zwei Werkzeugen und verschiedenen Rückzugshöhen prüfen
G90 und G91 einschließlich inkrementeller Wiederaufnahme. Bestehende
Standardprofile und deren Ausgabe ohne automatisch aktivierte Längenkorrektur
bleiben erhalten und sind gesondert geprüft.

53 fokussierte Tests pro Qt-Bindung bestanden: K1-Dialog-/Extraktionsprüfungen,
19 Werkzeugwechseltests, acht Profiltests, übersetzte Maschinenmenüs und
drei Versions-/Katalogprüfungen sowie MainWindow-Workflow und 18 bestehende
Leadmove-Goldens. Dies sind Code-/Ausgabeprüfungen, kein
LinuxCNC-Interpreterlauf oder Maschinenfreigaben. Keine Vollsuite, Debian-
Prüfung oder Paket-/MSI-Erstellung wurde damals gestartet. Der spätere
D1/D2-Abschluss ist oben separat dokumentiert.

<a id="r2"></a>

## Abgeschlossener Exportreihenfolgevertrag

### R2 – Sichtbare Reihenfolge als Exportvertrag festlegen

**Codebefund:** `TreeHandler.updateExportOrder` übernimmt die Layerreihenfolge
in `layers_list` und die Shape-Reihenfolge in `exp_order` beziehungsweise
`exp_order_complete`, auch beim manuellen Umordnen ohne Routen-Live-Update.
`MainWindow` bietet getrennte Aktionen
`exportShapes` und `optimizeAndExportShapes`. `application/optimization/routes.py`
optimiert pro Layer, berücksichtigt `send_to_TSP` und ruft anschließend
`LayerContent.optimize` auf; Letzteres verändert nur Startpunkte von zur
Optimierung freigegebenen Shapes. Eine
zusätzliche Exportoption ist daher nicht ungeprüft neu zu erfinden, sondern
zuerst gegen die vorhandenen Wege und Optimierungsmodi abzugleichen.

- [x] Die dargestellte Reihenfolge der Bearbeitungslayer strikt abarbeiten;
  eine Optimierung darf keine Layergrenze überspringen oder Layer vertauschen.
- [x] Manuelles Umordnen von Shapes im Treeview (Drag-and-drop oder
  Auf-/Ab-Schaltflächen) legt die neue Bearbeitungsreihenfolge innerhalb
  desselben Layers fest. Modell und Exportlisten übernehmen diese Reihenfolge
  auch bei ausgeschaltetem Routen-Live-Update; eingeschaltet zeigt die
  Routenanzeige sofort die neuen Verbindungen. Geometrie, Startpunkte,
  Werkzeugzuordnung und Optimierungsfreigabe bleiben dabei erhalten.
  Speichern/Laden und anschließender Export ohne Optimierung übernehmen
  die manuelle Reihenfolge einschließlich benutzerdefiniertem G-Code.
- [x] Innerhalb eines Layers die Shape-Reihenfolge beibehalten, außer für
  ausdrücklich zur Optimierung freigegebene Shapes bei bewusst gewählter
  Optimierung. Nutzerentscheidung vom 01.11.2026: Die bestehenden Modi
  bleiben erhalten; die relative Reihenfolge nicht freigegebener Shapes
  genügt. `CONSTRAIN_ORDER_ONLY` erhält diese relative Reihenfolge;
  `CONSTRAIN_PLACE_AFTER` stellt diese Shapes vor die freigegebenen Shapes.
- [x] „Ohne Optimierung exportieren“ muss als klar erkennbare Aktion verfügbar
  sein. Sie löst weder eine neue Sortierung noch eine automatische Änderung
  der festgelegten Startpunkte aus. Exportiert wird die aktuell sichtbare
  Reihenfolge, auch wenn diese zuvor bewusst optimiert wurde.
- [x] Routenanzeige/Live-Update von Optimierung unterscheiden. Anzeigen oder
  Exportieren allein darf die Bearbeitungsreihenfolge nicht verändern.
- [x] GUI, CLI, Projekt-Roundtrip und tatsächliche G-Code-Sequenz verwenden
  denselben expliziten Reihenfolgevertrag. Werkzeugwechsel innerhalb eines
  Layers dürfen keine versteckte Gruppierung nach Werkzeug auslösen.

**Abnahme und Tests:** Mindestens zwei Layer mit eindeutig unterscheidbaren
Shapes und unterschiedlichen Werkzeugen verwenden. Layer und Shapes innerhalb ihrer bestehenden Ebene
manuell umordnen und mit Optimierung aus/an exportieren. Layerwechsel erst
bei der späteren gemeinsamen Umsetzung von R1b/R3 ergänzen.
Gemischte Optimierungsfreigabe und benutzerdefinierten G-Code einbeziehen;
Shape-/Werkzeugsequenzen im ausgegebenen G-Code statt nur Baumzeilen prüfen.
`dxf2gcode_tsp_optimization_test.py`, Tree- und Workflowtests erweitern.
Die Reihenfolge-Anforderungen vor einer Änderung des Optimierers präzise
festschreiben; bestehende Golden-Fälle bleiben Regressionen.

**Abgeschlossen und lokal geprüft, 01.11.2026:** Manuelles Umordnen und
Routenanzeige synchronisieren die Exportlisten ohne Optimierung. Die normale
Exportaktion ist ausdrücklich als Export ohne Optimierung bezeichnet;
DE/FR/RU-Kataloge und QM-Dateien wurden aktualisiert und mit tatsächlich
geladenen Übersetzungen geprüft. CLI-Projektexport erhält benutzerdefinierten
G-Code an seiner Position. Der kombinierte Treeview-/Projekt-/Exporttest prüft
zwei Layer, manuelle Shape-/Layer-Umordnung, Werkzeugwechsel, Startpunkte und
die tatsächliche G-Code-Sequenz; deaktivierte Einträge werden ausgelassen.
Auch der echte MainWindow-Workflow prüft manuelle Umordnung vor dem Export.
Die neuen Regressionen weisen die jeweiligen Fehler am vorherigen Stand nach.

Gezielt bestanden: PyQt5 mit 52 Tests (TSP, Tree-Multiselect, Exportreihenfolge,
MainWindow-Workflow und Shape-Werkzeuge); PyQt6 mit 40 Tests (dieselben Module
ohne Shape-Werkzeuge). Keine Vollsuite, Debian-Prüfung oder Paketbuild ausgeführt.
Die bisherigen Treeview-Drag-and-drop-Tests wurden dabei nicht erneut ausgeführt;
die neue gemeinsame Exportprüfung verwendet die Auf-/Ab-Schaltflächen.

**Optimierungsvertrag:** Die bestehenden Modi bleiben gemäß Nutzerentscheidung
erhalten. Der gemeinsame Anwendungsablauf wendet sie vor Startpunktoptimierung
und Routenanzeige an, sodass GUI und CLI dieselbe Shape-/Werkzeugfolge ausgeben.
Benutzerdefinierter G-Code behält beim normalen Export seine sichtbare Position;
bei bewusster Optimierung gelten die bisherigen Treeview-Modi auch für den CLI:
`CONSTRAIN_ORDER_ONLY` hängt alle aktiven Shapes hinter die übrigen Baumzeilen,
`CONSTRAIN_PLACE_AFTER` nur die freigegebenen Shapes. Die übrigen Zeilen behalten
ihre relative Reihenfolge. Die ergänzten Tests vergleichen beide Modi mit zwei
Layern und gemischter Freigabe im tatsächlichen G-Code sowie den anschließenden
Export ohne Optimierung. Ein weiterer CLI-Fall verwendet den echten TSP-Optimierer
mit deaktivierten Shapes, deaktiviertem G-Code und leerem Bearbeitungslayer.

## Importreihenfolge zusammengesetzter Kurven

Korrigiert am **31.10.2026** anhand von `fräsen_test_02 2004.dxf` und
`ATT00079.dxf`. Bei rückwärts verwendeten DXF-Entitäten drehte
`BuildDrawingModel` jedes einzelne Linien-/Bogenstück um, ließ aber die
Reihenfolge der Stücke unverändert. Die ausgewählte Originalkontur verband
dadurch falsche Endpunkte mit roten Geraden. Die blaue Vorschau zeichnete
die Teilstücke einzeln und verdeckte diese Unterbrechungen. Die fehlerhafte
Geometriekette war auch für die Planung relevant, nicht nur für die Anzeige.

Beim Rückwärtsimport wird jetzt zuerst die Teilstückreihenfolge umgekehrt
und dann jedes kopierte Teilstück gedreht. Die importierten Quelldaten
bleiben unverändert. `dxf2gcode_import_chain_test.py` prüft für beide Dateien
alle Shape-Verbindungen einschließlich Konturschluss, mit und ohne optionale
Linienteilung, sowie die Anschlusspositionen innerhalb der G40-Planpässe.
Die Prüfungen bestehen unter Qt5 und Qt6; zusätzlich wurde die tatsächliche
2D-Darstellung über den Hauptfenster-Ladeweg geprüft. Keine Vollsuite oder
Debian-Prüfung ausgeführt.

<a id="b1-b2"></a>

## B1/B2: Bohren, Pocketing und Kompensation

Umgesetzt am **31.10.2026**. `domain/project/machining.py` enthält die reine
Zustandsregel; `application/shapes.py:SetMachiningMode` wendet eine gemeinsame
Zielaktion auf die gesamte Auswahl an. Die Qt-Aktionen delegieren dorthin.

- Bohren einschalten setzt `Drill=True`, `Pocket=False` und G40.
- Pocketing einschalten oder G40/G41/G42 ausdrücklich wählen schaltet Bohren
  aus. Pocketing bleibt mit allen drei Kompensationszuständen kombinierbar.
- Ausschalten stellt keine frühere Bearbeitungsart wieder her. Gemischte
  Mehrfachauswahlen erhalten einen einheitlichen Zielzustand. Menühaken,
  Parameteranzeige und Vorschau werden anschließend aktualisiert.
- Widersprüchliche Projektwerte bleiben beim Laden erhalten. Das Hauptfenster
  meldet die betroffenen Shape-Nummern und fordert zur Auswahl einer gültigen
  Bearbeitungsart im Kontextmenü auf. Keine stillschweigende Vorrangregel.
- Für solche Shapes wird keine Geometrie vorbereitet. Der Planer liefert
  `machining.conflict` ohne exportierbaren Plan; die 2D-Vorschau zeigt eine
  Warnung statt einer Bearbeitungsbahn. Andere gültige Shapes bleiben
  exportierbar. Nach ausdrücklicher Auflösung ist das Shape wieder nutzbar.
- Automatische Fräskompensation verändert Bohreinstellungen nicht und löst
  bestehende Konflikte ebenfalls nicht stillschweigend auf.
- B2: Eine zusätzliche Sperre für Bohren bei Maschinenkompensation ließ sich
  im aktuellen Stand nicht bestätigen. Die Menüprüfung verwendet jetzt echte
  Geschlossenheit für alle ausgewählten Shapes; der bisherige Vergleich
  `allClosed == False` hatte offene Geometrie nicht ausgeschlossen. Bohren
  bleibt für geschlossene Kreisgeometrie bei beiden Kompensationskonfigurationen
  verfügbar. Leere, offene und gemischte ungeeignete Auswahlen bieten Bohren
  nicht an. Die gesonderte Pocketing-Sperre bei Maschinenkompensation bleibt.

Gezielte Tests unter Qt5 und Qt6 prüfen Zustandsübergänge, gemischte Auswahl,
Menühaken und erneut geöffnetes Menü, beide Kompensationskonfigurationen,
Projekt-Roundtrip mit Konfliktmeldung, blockierte Planung/Ausgabe, Auflösung
und Vorschauwarnung. Ein gültiger Bohrfall liefert pro Konfiguration einen
Plan und G-Code ohne Taschenbewegungen und G41/G42. Die deutschen,
französischen und russischen Meldungen wurden ergänzt, QM-Dateien regeneriert
und alle neuen Übersetzungen geprüft. Zusätzlich bestanden unter Qt5 die
bestehenden Projekt-/Adapter- und Werkzeugweg-Falltests einschließlich Goldens.
Keine Vollsuite, Debian-Prüfung oder Paketabnahme ausgeführt.

## K3: Dezimalpräzision und Werterhaltung

Umgesetzt am **31.10.2026**. Der ursprüngliche Befund war ein tatsächlicher
Wertverlust: Tiefen wie 0,015 und 0,005 Zoll wurden in den Konfigurationsfeldern
mit Qt-Standardpräzision von zwei Stellen quantisiert.

- `CorrectedDoubleSpinBox` verwendet standardmäßig vier Nachkommastellen.
  Dies gilt auch für die Werkzeugtabelle, Tiefen, Start-/Rückzugskoordinaten
  und Leads; die Schleppmesser-Rampenlänge verwendet jetzt ebenfalls vier.
  Explizit abweichende Genauigkeiten etwa für Importtoleranzen bleiben erhalten.
- Vereinbarte Regel: Geladene Werte mit mehr Stellen werden für die Anzeige
  gerundet, intern aber unverändert zurückgegeben, bis der Benutzer den Wert
  bearbeitet oder die Pfeiltasten des Spinbox-Felds verwendet. Unverändertes
  Bestätigen des Dialogs quantisiert diese Werte nicht.
- Shape-/Layerfelder schreiben ihre gerundete Anzeige beim bloßen Verlassen
  oder Bestätigen nicht zurück. Bewusstes Bearbeiten übernimmt die Eingabe;
  Punkt und Komma werden als Dezimaltrenner akzeptiert.
- Negative Werkzeug-Zusatzversätze werden in der Tabelle erhalten und nicht
  mehr durch die bisherige Untergrenze null ersetzt.
- Die vorhandenen Postprocessorprofile bleiben unverändert. `post_decimals`
  bestimmt weiterhin die G-Code-Präzision: drei Stellen reichen für 0,015 und
  0,005, für **0,0005 Zoll mindestens vier Nachkommastellen im verwendeten
  Postprocessorprofil einstellen**.

Bereits gerundet gespeicherte Werte lassen sich nicht rekonstruieren. Nach
dem Update deshalb bestehende Tiefen, Werkzeugwerte und die Ausgabepräzision
des Profils prüfen und bei Bedarf aus den ursprünglichen Vorgaben korrigieren.

Fokussierte Regressionen in `tests/dxf2gcode_numeric_precision_test.py` prüfen
positive/negative 0,015, 0,005, 0,0005 und mm-Werte, echte Tastatureingaben mit
Punkt/Komma, Erhaltung genauer geladener Werte, unverändertes Dialogbestätigen,
Speichern/Neuladen, mm/in-Wechsel sowie Projektpersistenz und Schneid-/Schwenktiefe
im Schleppmesserplan und ausgegebenen Z-Code bei expliziter Profilpräzision.
`TestParameterEditing` sichert außerdem die unveränderte Shapeanzeige und eine
bewusst akzeptierte Rundung ab. Die neuen Präzisionstests und die sieben
Bearbeitungstests bestehen unter Qt5 und Qt6; zusätzlich bestehen unter Qt5
alle Parameterzustands- und Pocketing-Konfigurationstests (44 Tests).
Keine neue Vollsuite, Debian-Prüfung oder Paketabnahme ausgeführt.

## Abgeschlossenes Werkzeugweg-Refactoring

Die folgenden Etappennummern 1–6 und 5a stammen aus der früheren Todo.
Sie bezeichnen keine Prioritätsabschnitte der neu geordneten aktiven Todo.
Die nachfolgenden Beschreibungen und Prüfstände sind aus dem bisherigen
Arbeitsdokument übernommen.

### 1. Verhalten und Planvertrag vervollständigen

- [x] Die gültigen Fälle aus der Verhaltensmatrix des Zielplans den konkreten
  Tests und Golden-Dateien zuordnen; Lücken je Maschinenart und
  Kompensationsmodus festhalten.
- [x] Für `ToolpathPlan` die benötigten semantischen Aktionen festlegen:
  Zustellung, Rückzug, Eilfahrt, Schnittbewegung, Kompensationswechsel,
  Tab-/Break-Abschnitt, Bohren und Schleppmesser-Schwenken.
- [x] Den GUI-unabhängigen Diagnosevertrag mit
  ToolpathDiagnostic/ToolpathPlanningResult festlegen und im
  PlanToolpath-Anwendungsfall für bestehende Planer normalisieren.
- [x] Alle Legacy-Planer so umstellen, dass sie Diagnosen zurückgeben und
  keine GUI-Dialoge oder direkten Postprocessor-Fehlermeldungen auslösen.
- [x] Vertragstests ergänzen, die Planinhalt und bisheriges G-Code-Ergebnis
  für denselben Fall vergleichen.

#### Vorhandene Verhaltensabdeckung

| Fall | Vorhandene Regressionen | Golden-G-Code | Planvertrag-Lücke |
| --- | --- | --- | --- |
| Fräsen, Maschinenkompensation G41/G42, geschlossene Kontur | `dxf2gcode_leadmove_golden_test.py` | `g41_closed.gcode`, `g42_closed.gcode` | Native Aktionen vorhanden; gezielte Planprüfungen pro Profil erweitern |
| Fräsen, Maschinenkompensation, offene Kontur und Richtungswechsel | `dxf2gcode_leadmove_golden_test.py` | `g41_open.gcode`, `g41_lead_out_radius_open.gcode` | Pass-/Kompensationswechsel als Aktionen; weitere Kombinationen gezielt absichern |
| Fräsen, Softwarekompensation G40, offen/geschlossen | `dxf2gcode_leadmove_golden_test.py`, `dxf2gcode_pocket_compensation_test.py` | `software_closed.gcode`, `software_open.gcode` | Vorbereitete Offset-Geometrie wird eingefroren; Offset-Algorithmus selbst noch in StMove |
| Tiefenpässe und Export-/Vorschauübereinstimmung | `dxf2gcode_toolpath_depths_test.py`, `dxf2gcode_toolpath_contract_test.py`, `dxf2gcode_stmove_gcode_test.py` | nur über andere Fälle indirekt | Native Tiefenfolge, Richtungswechsel und unveränderte Eingaben geprüft; Sonderfälle erweitern |
| Leads und Overcut, beide Kompensationsarten | `dxf2gcode_leadmove_*_test.py` | `g41_lead_*`, `software_lead_in_radius.gcode`, `*_overcut.gcode` | Native Aktionen mit Lead-Rolle und Diagnosen; bisheriger Geometriealgorithmus über expliziten Port |
| Tabs/Breaks mit Passauswahl | `dxf2gcode_breaks_pass_test.py`, `dxf2gcode_toolpath_slices_test.py` | `slices_tabs_from_second_pass.gcode` | Native Aktionen und Projektion für automatische, ausgeschaltete und explizite Passauswahl geprüft |
| Pocketing, Kompensation und Richtungsmodi | `dxf2gcode_pocket*_test.py`, `dxf2gcode_toolpath_slices_test.py` | `slices_pocket_g40.gcode`, `slices_pocket_g41.gcode`, `slices_pocket_g42.gcode` | Native Bewegungen und Tiefen geprüft; vorbereitete Geometrie weiterhin aus bestehendem Algorithmus |
| Bohren/Hole-Geometrien | `dxf2gcode_toolpath_slices_test.py`, bestehende Hole-Vorschau/-Hit-Tests | `slices_drill.gcode`, `slices_drill_peck.gcode` | Kreis und HoleGeo mit einfacher/wiederholter Zustellung, Bohrposition und 2D-/3D-Projektion geprüft |
| Schleppmesser: offen/geschlossen, Overcut, Rampeneinfahrt | `dxf2gcode_leadmove_golden_test.py` | `drag_knife_*.gcode` | Eigene native Strategie mit Drag-/Rampenrollen; weitere Planinhaltstests ergänzen |
| Drehmaschine | `dxf2gcode_leadmove_function_test.py`, `dxf2gcode_toolpath_slices_test.py` | `slices_lathe_closed.gcode`, `slices_lathe_arc_open.gcode` | Bestehender Linien-/Bogenpfad, Passumkehr, Durchmesserformatierung und Lead-Einschränkungen geprüft; keine neuen Drehzyklen |
| Postprocessor-Bogenexport und Kompensationsregeln | `dxf2gcode_stmove_gcode_test.py`, Lead-Golden-Tests | Bogenverhalten nicht als eigene Golden-Matrix | Explizite MachineCapabilities; zusätzliche Profil-/Koordinatenkombinationen absichern |

Die Matrix dokumentiert bestehende Regressionen, nicht vollständige
Planabdeckung. Neue native Strategien benötigen für ihre vertikale Scheibe
gezielte Planinhaltstests und weiterhin bytegenaue G-Code-Vergleiche.
`dxf2gcode_toolpath_slices_test.py` ergänzt für Abschnitt 3 die gemeinsame
Plan-/Export-/Projektionsprüfung; weitere Profilkombinationen bleiben bei
konkretem Bedarf gezielt zu ergänzen.

Der Diagnosevertrag ist als ToolpathDiagnostic und ToolpathPlanningResult in
domain/toolpath/plan.py festgelegt. Der Anwendungsfall übergibt einen
unveränderlichen ToolpathRequest an den reinen Planer und erhält diesen
Ergebnisvertrag direkt zurück. Ungültige Start-/Exit-Leads
und fehlende Kompensationsanfahrten liefern keinen exportierbaren Plan;
Tiefenwarnungen begleiten den bisherigen Plan. Die Planung öffnet keine
Dialoge und verändert keine Diagnose-Sammlung des Postprocessors. Erst beim
Export übernimmt der Adapter die Meldungen in den vorhandenen Anzeige- und
Logging-Kanal für GUI und CLI.

### 2. Planer von der Shape-Exportlogik lösen

- [x] `ToolpathPlanner` aus `adapters/toolpath/simple_milling.py` in einen
  klar benannten Planer verschieben; keine Strategie darf als
  `ShapeToolpathCommandBuilder`-Fallback exportieren.
- [x] `ShapeToolpathCommandBuilder` schrittweise in reine Planungsstrategien
  überführen. Während der Migration die vorhandenen Geometriealgorithmen
  wiederverwenden, aber deren Ausgabe als semantische Pläne erfassen und nicht
  durch Aufruf des Postprocessors simulieren.
- [x] Für die Strategien explizite Eingaben übergeben: Shape-/Geometriedaten,
  aufgelöste Bearbeitungseinstellungen und Maschinen-/Steuerungsfähigkeiten.
- [x] Mutationen wie Umkehren offener Konturen oder Ändern von Pocket-Tiefen
  aus dem Projektmodell entfernen; Planung muss wiederholbar sein und darf
  Eingaben nicht verändern.
- [x] Den einfachen geschlossenen Fräsfall als erste vollständig native
  Strategie behalten und die Abdeckung mit den folgenden Fällen erweitern.

Die Orchestrierung liegt jetzt in domain/toolpath/planner.py mit separaten
Strategien für einfache Fräsfälle, Konturen und Schleppmesser. inputs.py
definiert unveränderliche Geometrie-, Bearbeitungs- und Fähigkeitswerte;
movements.py erzeugt semantische Aktionen einschließlich Tabs und
Pocket-Verbindungsbewegungen. adapters/toolpath/planning.py friert die
bestehenden Modelldaten ein und adaptiert die bisherigen Lead-/Overcut-
Geometriealgorithmen. Kein Planer führt einen Postprocessor aus oder verändert
das Projektmodell. Der G-Code-Adapter serialisiert ausschließlich Aktionen.

Die alten Module adapters/toolpath/simple_milling.py,
shape_plan_builder.py und geometry_gcode.py sind entfernt. Abschnitt 3
ergänzt die gezielte fachliche Plan- und Exportmatrix,
insbesondere für Bohren, Drehmaschine und weitere Kombinationen. Die
Weiterverwendung vorhandener StMove-/Offset-/Pocket-Geometriealgorithmen
bedeutet weiterhin keinen vollständigen Abschluss des gesamten Refactorings.

### 3. Fälle in kleinen vertikalen Scheiben migrieren

Jede Scheibe umfasst Planer, Export, Vorschauprojektionen und Regressionen.
Die Reihenfolge minimiert Abhängigkeiten zwischen den Fällen.

- [x] Geschlossene Kontur, Softwarekompensation, mehrere Tiefenpässe.
- [x] Offene Kontur mit alternierender Passrichtung und Softwarekompensation.
- [x] Maschinenkompensation G41/G42 einschließlich Ein-/Ausschalten und
  Richtungswechselregeln des Postprocessors.
- [x] Leads, Overcut und ungültige Lead-Geometrie mit Diagnosen.
- [x] Tabs/Breaks mit Auswahl der betroffenen Pässe.
- [x] Pocketmilling mit frei wählbarer Kompensationsrichtung G40/G41/G42.
- [x] Bohren und Hole-Geometrien.
- [x] Schleppmesser einschließlich Tipweg, Drag-Hops und Rampeneinfahrt.
- [x] Drehmaschine: vorhandene unterstützte Formen und Einschränkungen
  explizit abbilden.

**Umsetzung und Grenzen (30.10.2026):** Die nativen Strategien aus Abschnitt 2
werden weiterverwendet. `dxf2gcode_toolpath_slices_test.py` prüft für die
Fallgruppen wiederholbare Planung, unveränderte Projekteingaben und dieselbe
Ausgabe über direkten Planexport und den Shape-Exportadapter. Formatierte
XY-Endpunkte werden mit den Planaktionen verglichen. Vorhandene Golden-Fälle
bleiben unverändert; acht neue Referenzen sichern Tabs, Pocket G40/G41/G42,
einfaches/wiederholtes Bohren sowie Linien und offene Bögen der Drehmaschine.

- Offene Softwarekompensationsbahnen werden in 2D auch bei umgekehrter
  Passrichtung nur einmal gezeichnet. Getrennte XY-Abschnitte erhalten im
  echten `QPainterPath` eigene Teilpfade statt künstlicher Verbindungslinien.
- Der Plan hält den ersten Anfahrpunkt auch bei späteren Pocket-Eilwegen fest.
  Der eingefrorene Werkzeugradius ermöglicht Bohrmarkierungen in 2D; die
  Z-Aktionen desselben Plans liefern die Bohrbewegungen in 3D.
- Tabs sind für automatische/ausgeschaltete sowie erste/zweite Passauswahl
  geprüft. Die bestehende Schnittpunktberechnung verwendet unter Qt6
  `QLineF.intersects`; ältere Qt5-Versionen behalten ihren bisherigen Zugriff.
- Pocketing bleibt Softwarekompensation mit gewähltem G40/G41/G42; die
  vorhandene GUI-Sperre bei Maschinenkompensation wird nicht aufgehoben.
- Beim Schleppmesser bleiben vorbereiteter Halterversatz zur Messerspitze,
  Schwenkbögen, Hubtiefe und bestehende Rampenausgabe erhalten. D1/D2 werden
  dadurch nicht vorweggenommen; es wird kein neuer Messerablauf eingeführt.
- Die Drehmaschine verwendet weiterhin die vorhandene Konturstrategie für
  Linien/Bögen und Tiefenpässe. Leads und Overcut bleiben deaktiviert;
  der Postprocessor behält seine bestehende Durchmesserformatierung bei.
  Neue Drehzyklen oder zusätzliche Maschinenfreigaben sind nicht enthalten.

**Gezielte Prüfung:** 115 Tests unter Qt5 bestanden (Fallmatrix, Planvertrag,
StMove-Export, Tab-Pässe, 18 bestehende Golden-Fälle, Lead-Pass-/Exportvergleich
und Pocket-Kompensationsfälle). Nach der Qt-Kompatibilitätskorrektur bestehen
zusätzlich die 17 betroffenen Tab-Tests unter Qt5 und alle neun neuen
Fallmatrix-/Painter-Tests unter Qt6. Keine Vollsuite, Debian-/SSH-Läufe oder
Builds ausgeführt; kein manueller GUI-/OpenGL-Renderingnachweis.
Zum damaligen Prüfstand waren die Vorschau-/Geometriearbeiten aus den
Etappen 5/6 noch offen; ihre späteren Abschlüsse sind unten dokumentiert.

### 4. G-Code-Serialisierung auf semantische Bewegungen umstellen

- [x] `ToolpathGCodeExporter` serialisiert alle Planaktionen; er berechnet
  keine Konturen, Offsets, Passfolgen oder Pocket-Bahnen.
- [x] Postprocessor-Dialekte formatieren nur Bewegungs- und Steuerungsaktionen
  und verwalten ihren modalen Ausgabestatus.
- [x] Direkte Postprocessor-Aufrufe aus `ShapeToolpathCommandBuilder`,
  Geometrieklassen und Planungslogik entfernen.
- [x] Alle vorhandenen Golden-G-Code-Ausgaben bytegenau erhalten.

**Umsetzung (31.10.2026):** `adapters/postprocessor/dialect.py:ProfileDialect`
enthält die profilabhängige Bewegungs-/Steuerungsformatierung, Zahlenformate,
Template-Ersetzung, Zeilennummern und Zeilenenden. Der modale Ausgabezustand
für Vorschub und absolute/inkrementelle XY-/Z-Werte gehört ebenfalls dorthin.
Die Klasse erhält Profil, Startkoordinaten, Start-Z und Durchmesserfaktor
explizit; sie importiert weder Qt, globale Laufzeitwerte noch einen Planer.
Die vorhandenen Formatierungsalgorithmen und Profilvorlagen bleiben erhalten.

`MyPostProcessor` erbt diese Formatierungsoberfläche für bestehende Aufrufer.
Seine Exportinitialisierung übergibt die aufgelösten Startwerte und den
Drehmaschinenfaktor einmal an den Dialekt. Profilverwaltung, GUI-Anbindung,
Programmkopf mit Versionsmetadaten, Dateiausgabe, Layer-/Shape-Durchlauf und
Anschluss an den Planungsanwendungsfall bleiben in dieser Exportfassade.
Die Fassade ist damit weiterhin kein vollständig GUI-unabhängiger Dienst;
für reine Planserialisierung genügt dagegen `ProfileDialect` zusammen mit
`ToolpathGCodeExporter`. Weitere Entkopplung bleibt gesonderte Arbeit.

**Gezielte Prüfung:** 72 lokale Tests bestanden: alle 18 bisherigen
Lead-/Schleppmesser-Golden-Fälle, die neun vertikalen Fallmatrix-/Painter-Tests
mit acht weiteren Referenzdateien, die StMove-/Postprocessor-Regressionen,
drei eigenständige Dialekttests und ein Importgrenztest. Die Fallmatrix
vergleicht jetzt zusätzlich die Ausgabe des eigenständigen Dialekts mit der
bestehenden Exportfassade. Neue Tests prüfen fortlaufenden modalen Zustand
über mehrere Pläne, absolute/inkrementelle Koordinaten, getrennte Instanzen,
explizite Durchmesserskalierung von Bogenworten sowie geordnete Profil-,
Bohr-, Kompensations- und Literalaktionen. Keine Referenzdatei geändert;
keine Vollsuite, Debian-/SSH-Läufe oder Builds ausgeführt.

### 5. Vorschau und gemeinsame Planquelle abschließen

- [x] 2D-Projektion zeigt gleiche XY-Bahnen einmal und kennzeichnet Tabs,
  Leads, Eilwege sowie programmierte beziehungsweise kompensierte Bahn
  eindeutig.
- [x] 3D-Projektion übernimmt Z und Passfolge aus demselben Plan.
- [x] 2D/3D-Vorschau berechnet weder Passfolge noch Tabs, Leads oder
  Rückzüge unabhängig vom Export neu.
- [x] Änderungen an Werkzeug, Tiefe, Kompensation, Leads, Tabs und
  Pocket-Einstellungen invalidieren den Plan und beide Projektionen zusammen.

**Umsetzung (31.10.2026):** Beide Ansichten erhalten ihre Pläne über
`adapters/toolpath/preview.py` mit derselben Eingabeaufbereitung und demselben
Domain-Planer wie der Export. Verwendet werden das geladene Postprocessorprofil
beziehungsweise dessen Schema-Vorgaben, solange noch kein Profil geladen ist,
sowie die aktuellen Break-Layer. Vorschauplanung verändert den modalen
Ausgabezustand des Exporters nicht.

`plan_preview_segments` projiziert die geordneten Planaktionen einschließlich
Z, Leads, Tabs, Pocket-Bewegungen und Eilwegen. Die Zusatzdarstellung in 2D/3D
berechnet keine eigenen Leads oder Tab-Schnittpunkte mehr. Offene XY-Bahnen
werden auch bei umgekehrter Passrichtung dedupliziert; getrennte Abschnitte
bleiben getrennte Painter-Teilpfade. Die Bogenprojektion berücksichtigt auch
Profile, die ausschließlich Gegenuhrzeigersinn-Bögen ausgeben.

Programmiertes G41/G42 und Werkzeugmittelpunktbahnen mit G40 sind als
Kompensationsraum im Plan festgehalten und durch den 2D-Tooltip unterscheidbar.
Die vorhandenen Bahnfarben bleiben unabhängig davon erhalten. Die Beschreibungen sind in Deutsch,
Französisch und Russisch übersetzt; die QM-Dateien wurden neu erzeugt und
mit tatsächlich geladenen Translatoren geprüft. Tab- und Lead-Bewegungen
besitzen eigene Darstellungsrollen.

Es gibt keinen wiederverwendeten Plan-Cache: Bei einem erneuten Darstellen
oder Exportieren werden die aktuellen Werkzeug-, Tiefen-, Kompensations-,
Lead-, Tab- und Pocket-Werte neu eingefroren. Änderungen können deshalb keinen
alten Plan in einer der Projektionen weiterverwenden. Die vorhandenen
GUI-Änderungsaktionen lösen das erneute Darstellen aus. Die Originalgeometrie
ist die stets sichtbare Grunddarstellung und Auswahlfläche. Der gemeinsame
Plan bestimmt ausschließlich die bei Auswahl zusätzlich angezeigte
Werkzeugwegvorschau und den Export.

**Darstellungskorrektur nach Nutzertest (31.10.2026):** Die erste Umsetzung
hatte bei vorhandenem Plan die Grunddarstellung irrtümlich durch die geplante
Bahn ersetzt. In 2D verwendet `ShapeGUI.path` jetzt wieder die Originalkontur;
in 3D enthält `drawObject` ebenfalls die Originalgeometrie. Der planbasierte
Werkzeugweg liegt getrennt in der Auswahl-Zusatzdarstellung. Auswahl und
Abwahl blenden diese ein beziehungsweise aus, ohne die Originalkontur oder
deren Trefferfläche zu ersetzen. Werkzeugbahn, Pocket, Lead-in/Werkzeug,
Lead-out und Eilwege verwenden wieder die vorhandene Farbpalette; die
Zusatzbahn erhält keine neue Farbe abhängig vom Kompensationsraum.

Die zuvor irrtümlich auf die Grunddarstellung bezogenen Plan-Painter- und
3D-Passprüfungen wurden auf die Werkzeugweg-Zusatzdarstellung umgestellt.
Gezielte Prüfungen belegen Originalkontur und Trefferfläche, Ein-/Ausblenden
bei Auswahl/Abwahl, getrennte Teilpfade sowie Bahn-, Lead- und Werkzeugfarben:
**21 Tests jeweils unter Qt5 und Qt6 bestanden**. Keine erneute Vollsuite und
kein Debian-Lauf für diese Darstellungskorrektur; die OpenGL-Prüfungen
kontrollieren Aufrufe mit einem Mock, keinen echten GPU-Renderdurchlauf.

### 5a. Werkzeugänderung auf eine Shape begrenzen

- [x] In der GUI prüfen und korrigieren, dass ein Werkzeugwechsel für eine
  einzelne Shape nicht auf andere Shapes oder deren Layer-Einstellungen
  übertragen wird.
- [x] Den Anwendungsfall für eine Shape-Änderung klar von einer absichtlichen
  Layer-/Mehrfachauswahl-Änderung trennen; nur die betroffene Shape und ihr
  Werkzeugweg werden aktualisiert.
- [x] Regressionstest ergänzen: Bei mehreren Shapes ein Werkzeug an einer
  Shape wechseln und sicherstellen, dass Werkzeugnummer und Werkzeugwerte
  aller übrigen Shapes unverändert bleiben; Vorschau und Export der geänderten
  Shape verwenden das neue Werkzeug.
- [x] Bei unterschiedlichen Werkzeugen in der Auswahl „Verschiedene Werkzeuge“
  und „—“ für die Werkzeugwerte anzeigen; eine bewusste Werkzeugauswahl gilt
  weiterhin für alle ausgewählten Shapes.

Die optionale Shape-Werkzeugzuordnung wird zusätzlich in Projektdateien
gespeichert. Alte Projekte ohne diese Angabe übernehmen weiterhin das
Layer-Werkzeug. Vorschau, Kompensation und Export verwenden dieselben
effektiven Werkzeugwerte; der Export berücksichtigt Werkzeugwechsel innerhalb
eines Layers in der bestehenden Shape-Reihenfolge. Die Regressionen stehen
in tests/dxf2gcode_shape_tool_test.py.

### 6. Kopplungen und alte Pfade entfernen

- [x] `domain/toolpath` und `domain/geometry` benötigen weder Qt noch
  `bootstrap.runtime_state` oder Postprocessor-Module.
- [x] Globale Werte wie `g.config` und Maschinenart in der Planungslogik durch
  explizite Einstellungen und Fähigkeiten ersetzen.
- [x] GUI-spezifische Fehleranzeige aus Planern entfernen; GUI und CLI
  präsentieren dieselben Diagnosen jeweils passend.
- [x] Entfernen der alten Shape-basierten G-Code-Ausgabe und aller
  Übergangspfade erst nach Migration sämtlicher Aufrufer.

**Umsetzung nach Abschnitt 5 (31.10.2026):**

- `PreparationSettings` hält aufgelöste Maschinenart, Kompensationszuständigkeit,
  Werkzeugwerte, Lead-Modi, Überfahrt, Messerstartwinkel und Pocket-Freiraum
  als unveränderliche Werte. `adapters/toolpath/preparation.py` löst die
  Laufzeitwerte auf; die Geometrievorbereitung erhält sie explizit. GUI, CLI
  und Testfixtures wurden auf diese Grenze umgestellt.
- `Geos` und die gemeinsamen Kontur-Operationen liegen unter
  `domain/geometry/collections.py`. Der Offset-Algorithmus erbt von
  `ContourGeometry`, statt das Qt-/konfigurationsabhängige Projekt-Shape zu
  importieren. Das Projekt-Shape verwendet dieselben Geometrieoperationen.
  `ArcGeo` erhält die Toleranz für die Mittelpunktberechnung als Parameter.
- Domain-Meldungen tragen Quelltext, Kontext und Formatargumente ohne Qt.
  Beschriftungen und Übersetzung liegen im Qt-Adapter; bestehende
  Übersetzungskontexte bleiben erhalten.
- `PocketMill.generate()` liefert neue Geometrie zurück. Die Berechnung
  verändert weder die Eingabesammlung des Aufrufers noch das Projektmodell.
  Die Vorbereitung übernimmt das Ergebnis anschließend in ihren eigenen Weg.
- Die getrennte Vorschau-Berechnung von Exit-Leads, letzten Passrichtungen
  und Break-Schnittpunkten sowie die StMove-Zeichenroutine sind entfernt.
  Für bestehende Anzeigezugriffe bereitgestellte `exit_geos` sind nur noch
  aus den fertigen Planaktionen abgeleitete Werte, kein zweiter Planungsweg.
  Shape und Geometrieklassen erzeugen weiterhin keinen G-Code.

Ein Importgrenztest lädt sämtliche Module unter `domain/geometry` und
`domain/toolpath` in einem frischen Prozess und prüft das Ausbleiben von Qt-,
Presentation-, Postprocessor- und globalen Laufzeitimporten. Das ist die hier
abgeschlossene Grenze; Profilverwaltung und GUI-/Dateiorchestrierung der
Exportfassade sowie die übrigen Projektmodelle sind davon zu unterscheiden.

**Prüfstand der Refactoring-Etappe vor der nachfolgenden Darstellungskorrektur:**

- Windows, Python 3.11 / Qt5: vollständige Suite, **775 Tests bestanden**
  (`.tox/toolpath-full-windows-final.log`). Die neuen Vorschauprüfungen wurden
  zusätzlich gezielt unter Qt6 ausgeführt; keine vollständige Qt6-Suite.
- Debian auf `192.168.178.183`, Python 3.13.5 / Qt5: vollständige Suite,
  **775 Tests bestanden**, in einer neuen virtuellen Umgebung unter
  `/home/christian/dxf2gcode-test-work/runs/toolpath-full-20261031T065841Z-59bd6e20`.
  Verwendet wurden dieselben Runtime-Abhängigkeitsversionen wie in der
  vorhandenen Debian-Testinstallation. Diese Installation und ihre Samples
  wurden nicht verändert.
- Der erste Debian-Snapshot hatte versehentlich `source/tools/build`
  ausgelassen; dadurch scheiterte ausschließlich der Metadaten-Test
  `TestBuildProvenance.test_build_commands_prefer_source_to_older_installed_package`.
  Der korrigierte Snapshot enthält diese Dateien. Der bereits gestartete
  Wiederholungslauf war vor dem angeforderten Stop beendet; danach wurde
  auf Nutzerwunsch **nur dieser einzelne Test erneut ausgeführt und bestand**.
  Keine weiteren Tests gestartet.
- Debian-Snapshot SHA-256:
  `655764dedb20ba9fea6543a92600a6801dc42d3674950601c43fd55b0b1898b8`.
  Bericht und Protokoll sind lokal unter `.tox/toolpath-debian-report.json`
  und `.tox/toolpath-full-debian-final.log` gesichert. Fehlgeschlagene
  Debian-Läufe wurden zur Nachvollziehbarkeit beibehalten.
- Die vorhandenen Golden-G-Code-Referenzen bleiben unverändert. Es wurden
  keine Release-/MSI-Builds oder Systempaketinstallationen ausgeführt.
  OpenGL-Aufrufprüfungen verwenden weiterhin ein Mock; ein manueller
  GPU-Renderingnachweis ist damit nicht verbunden.

## Abgeschlossene Bedien- und Importaufgaben

### U1 – Werkzeugauswahl an der Durchmesserzeile ausrichten

**Ursprünglicher Befund:** In `presentation/qt/resources/dxf2gcode.ui` lag
`toolDiameterComboBox` neben dem gesamten mehrzeiligen Werkzeugwerteblock.
Das führte zur vertikalen Zentrierung. Die Auswahl liegt jetzt im gemeinsamen
`toolValuesGrid` in derselben Zeile wie der Durchmesser.

- [x] Die Auswahl oben auf Höhe der Durchmesserzeile anordnen. Die `.ui`
  bleibt die Quelle; generierte Dateien über den vorhandenen Buildweg erzeugen.
- [x] Leere und gemischte Auswahl, deaktivierte Anzeige sowie lange
  Werkzeugnamen bei schmalem Fenster und anderer Skalierung berücksichtigen.

**Abnahme und Tests:** Gezielte Sichtprüfung bei normaler und hoher
DPI-Skalierung; bestehende Auswahltests weiterverwenden. Kein zusätzlicher
Pixelvergleichstest nur für die Verschiebung des Widgets.

**Prüfung am 30.10.2026:** Offscreen-Ansichten bei 100 % (Qt5) und 150 %
(Qt6) mit leerer/deaktivierter Auswahl, längerer Werkzeugnummer und gemischter
Auswahl visuell geprüft. Dropdown und Durchmesser bleiben zeilengleich.
Die bestehenden zwölf Shape-Werkzeugtests bestehen mit beiden Qt-Versionen.
Keine neuen GUI-Texte; die Übersetzungskataloge bleiben unverändert.

### U2 – Baum-Buttons nur bei möglicher Zustandsänderung aktivieren

**Ursprünglicher Befund:** Die Buttons berücksichtigten den Baumzustand nicht.
Entities klappte nur bis Tiefe 0 zu. Jetzt meldet `TreeView` die verfügbaren
Aktionen über `expansionAvailabilityChanged`; `TreeHandler` verbindet beide
Buttonpaare einheitlich. Modellwechsel lösen alte Signalverbindungen und
registrieren Einfügen, Entfernen, Verschieben, Reset und Layoutänderung des
aktuellen Modells neu. Beide Zuklappaktionen verwenden `collapseAll`.

- [x] Für Layer und Entities denselben Vertrag umsetzen: vollständig
  zugeklappt → nur Ausklappen aktiv; vollständig aufgeklappt → nur Zuklappen
  aktiv; Zwischenstand → beide aktiv. Ohne aufklappbare Knoten sind beide
  deaktiviert. Blätter zählen nicht als zu-/aufklappbare Zweige.
- [x] Auch manuelles Klappen einzelner Zweige, Dateiladen, Modellwechsel und
  Verschieben müssen den Buttonzustand aktualisieren. Verdeckte Unterzweige
  dürfen den sichtbaren Zustand nicht falsch klassifizieren.
- [x] Entities ebenfalls vollständig zuklappen, einschließlich sichtbarer
  Wurzelknoten. Der bisherige Anfangszustand beim Laden (`expandToDepth(0)`)
  bleibt erhalten; die verfügbaren Buttons werden daraus abgeleitet.

**Abnahme und Tests:** Fokussierte Qt-Tests für beide Bäume mit leerem Baum,
Blättern, mehreren Hierarchiestufen, Zwischenständen und Modellneuladen.
Prüfen, dass jeder aktive Button tatsächlich eine Darstellung ändert und
die Bäume ihren Zustand unabhängig voneinander verwalten.

**Prüfung am 30.10.2026:** Acht neue Regressionen in
`dxf2gcode_treeview_test.py` prüfen leere Modelle/Blätter, manuelles und
vollständiges Klappen, verdeckte expandierte Unterzweige, Modellwechsel,
Einfügen/Entfernen/Umordnen, Signalblockierung und unabhängige Ansichten.
Der echte MainWindow-Workflow prüft beide Buttonpaare vor und nach DXF-Import
einschließlich des vollständigen Entities-Zuklappens. Qt5: 16 TreeView-,
ein MainWindow- und zwölf Werkzeugtests bestanden. Qt6: die acht neuen
Baumzustands-, ein MainWindow- und zwölf Werkzeugtests bestanden.

Im zusätzlichen Qt6-Lauf des gesamten TreeView-Testmoduls scheitern zwei
bestehende Drag-and-drop-Tests an alten Enum-Zugriffen; siehe R1. Das ist
keine grüne Gesamtfreigabe. UI-Dateien für Qt5/Qt6 sind neu erzeugt; Qt6
verwendet das vorhandene unveränderte Ressourcenmodul, da lokal `rcc` fehlt.
Keine Pakete installiert und keine Vollsuite, Release-/MSI-Builds oder
Debian-Läufe gestartet.

**Nachbesserung nach Hängermeldung (30.10.2026):** Nach manuellem Zuklappen
eines Asts reagierte das native Fenster beim anschließenden Ein-/Ausklappen
nicht mehr. Betroffene Datei: `Frontplatte_Texte_aufgebrochen.dxf`;
Programmstart direkt aus dem Projekt.

Der bisherige Signalpfad lief die Baumstruktur synchron aus Qt-Ein-/
Ausklappsignalen ab. `isExpanded()` kann dabei ein ausstehendes Qt-Layout
ausführen; die synchronen Buttonänderungen erzeugten außerdem unnötige
Rückkopplungen und mehrere Zwischenzustände pro Sammelaktion. Zwei gezielte
Regressionen belegten diese synchronen bzw. mehrfachen Benachrichtigungen
vor der Korrektur.

- [x] Einzelne Klapp-/Modellsignale über einen dem View gehörenden
  Single-Shot-Timer zusammenfassen und erst nach der Qt-Aktion auswerten.
- [x] Während `expandAll`, `collapseAll` und `expandToDepth` keine erneute
  Zustandsabfrage auslösen; am Ende einmal den abgeschlossenen Zustand melden.
- [x] Wiedereintritt absichern und unveränderte Buttonzustände nicht erneut
  veröffentlichen. Während einer laufenden Abfrage angeforderte Updates erst
  anschließend einplanen, statt eine verschachtelte Timer-Schleife zu starten.
- [x] Sichtbaren Baum und echtes Hauptfenster mit der betroffenen DXF im
  Offscreen-Modus prüfen: Astpfeile und Buttons per Mausklick, beide Tabs,
  wiederholtes Ein-/Ausklappen und gemischte Zustände. Separate Testprozesse
  haben Zeitlimits, damit ein Hänger nicht die ganze Testsuite blockiert.

Fokussierter Prüfstand nach der Nachbesserung: Qt5 mit 20 TreeView- und zwei
MainWindow-Tests; Qt6 mit zwölf Baumzustands- und zwei MainWindow-Tests.
Der vollständige native Windows-Hänger ließ sich im Offscreen-Test nicht
zuverlässig reproduzieren; eine Bestätigung im normalen Fenster steht noch
aus. Keine erneute Vollsuite, Debian-Prüfung oder Paketerstellung für diese
Nachbesserung; das vorhandene Wheel enthält sie noch nicht.

### U4 – Ticket #157: Startzustand des Layerbaums konfigurieren

**Quelle:** [SourceForge-Ticket #157 – Feature Request(s)](https://sourceforge.net/p/dxf2gcode/tickets/157/).
Das Ticket wünscht unter anderem zuklappte Layer als wählbaren Startzustand.
Die Nutzerfestlegung für diese Umsetzung lautet: **Standard weiterhin
aufgeklappt.** Der zusätzliche Importfilterwunsch I2 ist ebenfalls umgesetzt;
das Tastenkürzel U5 war zu diesem Prüfstand noch offen; der spätere
Abschluss ist im Abschnitt V1/U3/U5 dokumentiert.
Alphanumerische Sortierung (R4) und Segmentmarkierung (I1) sind nach
ausdrücklicher Nutzerfestlegung vom 30.10.2026 ausgeschlossen; sie sollen
nicht umgesetzt werden. U4 erledigt nicht die übrigen offenen Ticketwünsche.

- [x] Checkbox „Layer beim Laden einer Zeichnung ausklappen“ in der
  Anwendungskonfiguration unter General settings ergänzen.
- [x] `General.expand_layers_on_load` als persistierten booleschen Wert mit
  Standard `True` einführen. Abgewählt startet der Layerbaum zugeklappt;
  gewählt startet er vollständig aufgeklappt.
- [x] Die Einstellung beim Aufbau des Layerbaums auswerten, nicht bei jeder
  Auswahl-/Parameteränderung. Manuelles Klappen bleibt jederzeit möglich;
  die U2-Buttons zeigen den resultierenden Zustand an. Der Entities-Baum
  und fachliche Bearbeitungs-/Exportreihenfolgen bleiben unberührt.
- [x] Ältere unterstützte Profile ohne den Schlüssel erhalten `True`.
  Konfigurationsschema 9.15 ergänzt die Versionen 9.11–9.14 kompatibel;
  bestehende Werte gehen nicht verloren. Kein `.d2g`-Formatwechsel.
- [x] Neue Beschriftung in Deutsch, Französisch und Russisch pflegen und
  die QM-Dateien kompilieren. Expliziter Qt-Kontext `MyConfig` verhindert
  für diesen neuen Text den unter K1 beschriebenen Kontextfehler.

**Prüfung:** Vier fokussierte Konfigurationstests prüfen Standard, Laden aller
älteren unterstützten Versionen ohne Schlüssel, Speichern/Laden beider Werte
und die echte Checkbox mit geladenen DE-/FR-/RU-Übersetzungen. Der
MainWindow-Workflow prüft beide Startzustände einschließlich U2-Buttons,
unverändertem Entities-Baum, Shape-Parametern und Reihenfolge. Diese Prüfungen
bestehen unter Qt5 und Qt6. Lange Gesamt-/Debian-/Release-Prüfungen wurden
nicht ausgeführt.

### I2 – Layer 0 und IGNORE-Layer optional vom Import ausschließen

**Status: umgesetzt.** `BuildDrawingModel` filtert vor der Shape-Erzeugung,
sodass ausgeschlossene Layer und Shapes weder im Bearbeitungsmodell noch
im Entities-/Layerbaum, in Vorschau oder Export auftauchen. Die Rohdaten
werden weiterhin gelesen, etwa für Blockreferenzen; das ist kein zweites
Bearbeitungsmodell. Ohne aktivierte Filter bleibt das bisherige Verhalten
erhalten: IGNORE-Shapes werden importiert und standardmäßig deaktiviert.

- [x] Den ergänzenden Ticketwunsch „Do NOT import IGNORE ... Layers“ als
  eigene Konfigurationsoption „IGNORE-Layer nicht importieren“ umsetzen.
  Bei aktivem Filter sollen betroffene Layer und Shapes tatsächlich nicht
  ins importierte Bearbeitungsmodell aufgenommen werden; bloßes Deaktivieren
  oder Überspringen beim Export erfüllt die Anforderung nicht.
- [x] Die optionale Behandlung von Layer `0` davon unabhängig halten, damit
  beide Filter getrennt wählbar bleiben.
- [x] Gemäß Nutzerfestlegung beide Filter standardmäßig ausschalten:
  `Import_Parameters.exclude_ignore_layers=False` und
  `Import_Parameters.exclude_layer_zero=False`. Neue Konfigurationen und
  unterstützte ältere Profile ohne Schlüssel übernehmen diese Werte.
  Schema 9.16 bleibt mit 9.11–9.15 kompatibel.
- [x] Namensregel mit der bestehenden Deaktivierung gemeinsam verwenden:
  `IGNORE` plus konfiguriertes `id_float_separator`, normalerweise `IGNORE:`;
  Groß-/Kleinschreibung bleibt relevant. `IGNORED:` oder `ignore:` werden
  nicht zusätzlich ausgeschlossen. Layer `0` wird anhand seines Namens,
  nicht anhand seiner internen Nummer erkannt.
- [x] BLOCK/INSERT-Zuordnung berücksichtigen. Die vorhandene Option
  `insert_at_block_layer` entscheidet weiterhin über die Zuordnung von
  Blockinhalten. Ist sie aktiv, bleiben Inhalte auf Layer `0` in einem
  regulären INSERT erhalten; bei aktivem Layer-0-Filter erben auch verschachtelte
  INSERTs auf `0` die äußere Zuordnung. Ein INSERT auf einem ausgeschlossenen
  Layer wird mit seinem Inhalt ausgelassen; leere gefilterte Blockknoten
  werden nicht im Baum belassen.
- [x] Importdiagnosen, Geometriezuordnung, Projektladen und Filterwirkung
  abstimmen. Bestehende Projekte dürfen keine unbemerkten fehlenden
  Shape-Referenzen bekommen; Konfigurations-/GUI-Texte in allen Sprachen pflegen.

**Bedienung und Geltungsbereich:** Die Anwendungskonfiguration bietet
„IGNORE-Layer nicht importieren“ und „Layer 0 nicht importieren“. Die Optionen
wirken beim nächsten Aufbau aus der DXF-Datei, auch beim Projektladen,
und gelten für GUI und CLI. Sie gehören zum aktiven Konfigurationsprofil;
die `.d2g`-Version und das Speicherformat werden nicht geändert. Ausgeschlossene
Layernamen werden als strukturierte `DrawingModel.excluded_layers` und im
übersetzten Importprotokoll ausgegeben. Die verbleibenden Shapes erhalten
zusammenhängende Nummern und konsistente Layer-/Entity-Zuordnungen.

**Prüfung am 30.10.2026:** Zwölf Importfiltertests, sechs Konfigurations-/
Übersetzungstests und der erweiterte MainWindow-Workflow bestehen mit Qt5
und Qt6. Abgedeckt sind beide Filter unabhängig/an/aus, Namensregeln,
Blockzuordnung einschließlich verschachtelter INSERTs, Shape-Callbacks und
Nummerierung, echter DXF→G-Code-Export sowie Laden und erneutes Speichern von
Projekten 1.1–1.3 bei aktiven Filtern. Der GUI-Test prüft Layerbaum, Vorschau
und eine vollständig weggefilterte Zeichnung. DE-/FR-/RU-Texte und QM-Dateien
sind aktualisiert und mit echten Translatoren geprüft.

Dabei wurde eine fehlende Bounding-Box einfacher importierter Shapes sichtbar,
wenn die Vorschau direkt den semantischen Plan verwendet. Der Modellaufbau
berechnet die Bounding-Box jetzt unabhängig vom Zeichnen; die GUI-Regression
mit der realen Linien-DXF deckt diesen Fall ab.

Zusätzlich bestehen die fokussierten Import-, Projektadapter-, Projekt-Lead-,
Anwendungs-/Importgrenzen- und Workflowtests. Alle 18 bestehenden
Golden-G-Code-Fälle bleiben bytegleich. Keine Vollsuite, Release-/MSI-Builds
oder Debian-Läufe ausgeführt; keine Pakete installiert.

## Abgeschlossene Drag-and-drop-Stabilisierung

<a id="r1a"></a>

### R1a – Drag-and-drop stabilisieren

**Codebefund:** `TreeView.dropEvent` in `treeview.py` verschiebt Zeilen
innerhalb desselben Elternknotens. In einem Ablehnungszweig wird
`drop_item.parent().rowCount()` aufgerufen, obwohl ein fremder oberster
Layer keinen Parent hat. Damit ist ein plausibler `None`-Zugriff sichtbar;
der gemeldete Absturz ist ohne Reproduktion/Traceback noch nicht abschließend
diesem Pfad zugeordnet. Ein echter Wechsel der Layer-Zugehörigkeit wird durch
die bisherigen `takeRow`-/`insertRow`-Aufrufe nicht implementiert.

**Früherer Qt6-Befund bei U2:** Zwei bestehende Tests
(`test_drop_reorders_siblings_and_calls_export_callback` und
`test_drop_without_drag_or_onto_viewport_is_ignored`) scheitern an
`TreeView.BelowItem`/`TreeView.OnViewport`. Auch die vorhandenen Drop-Handler
verwenden flache `QTreeView`-Enum-Namen. Im aktiven Drop-Handler und den Tests
sind diese bei R1a durch Qt5-/Qt6-kompatible `DropIndicatorPosition`-Werte
ersetzt. Die ungenutzte historische Methode `dropEventOld` bleibt unverändert.

`TreeHandler.updateExportOrder` benötigt zugleich die Mitgliedschaft in
`real_layer.shapes`; eine rein optisch umgehängte Shape genügt deshalb nicht.
`domain/project/project.py` stellt Projekte nach DXF-Neuimport über Layernamen
und Shape-Zuordnungen wieder her. Deren Ladepfad muss einen Layerwechsel
ebenfalls nachvollziehen können.

- [x] **Teil R1a – Stabilität:** den gemeldeten Drop auf einen anderen Layer
  reproduzieren und den Fehlerpfad absichern. Unzulässige/abgebrochene Drops,
  ungültige Zielindizes und Drops auf leere Bereiche dürfen nicht abstürzen
  oder das Modell teilweise verändern. Qt5 und Qt6 gezielt berücksichtigen.

**Prüfstand R1a (30.10.2026):** Ein ergänzter Regressionstest mit echtem
`QStandardItemModel` und simuliertem Drop-Event reproduziert vor dem Fix den
`NoneType.rowCount`-Absturz beim Drop auf einen fremden obersten Layer.
Der Ablehnungszweig greift nun nicht mehr auf dessen fehlenden Parent zu.
Ungültige Quell-/Zielindizes und Drops auf fremde Zweige oder leere Bereiche
werden abgelehnt; der Drag-Zustand wird beendet. Der Test prüft unveränderte
Zeilen, Shape-Identität und ausbleibende Exportbenachrichtigungen.
Alle 21 Tests aus `dxf2gcode_treeview_test.py` bestehen jeweils unter Qt5 und
Qt6. Kein manueller GUI-Durchlauf, keine Vollsuite und keine Builds ausgeführt.

**Nachkorrektur R1a:** Beim manuellen Test trat unter Qt6 zusätzlich ein
`AttributeError` auf: echte `QDropEvent`-Objekte besitzen dort `position()`
statt `pos()`. Der aktive Handler verwendet nun den passenden Zugriff und
verzichtet auf die vorzeitige Positionsabfrage im Debug-Logging. Die vorhandenen
Tests für Umordnen und abgelehnte Drops verwenden jetzt echte `QDropEvent`-
Objekte statt eines simulierten Events; damit wurde der gemeldete Fehler vor
der Korrektur reproduziert. Erneut bestehen alle 21 TreeView-Tests jeweils
unter Qt5 und Qt6.

Zum damaligen Zeitpunkt blieb R1b zusammen mit R3 zurückgestellt;
[späterer Abschluss](#r3-r1b-complete).

## Versions- und Build-Metadaten

### Implementierung und Vertrag

Paketversion und Herkunft sind getrennte Angaben. Die Paketversion aus
`_version.py` ist eine bewusste Release-Entscheidung. Ein Commit aktualisiert
die Herkunftsanzeige beim nächsten Lesen, erhöht aber weder die Release-Version
noch erzeugt er ein neues Wheel oder eine neue EXE/MSI.

- [x] `bootstrap/version_metadata.py` ermittelt Paketversion, Revision,
  Quellbranch, Commit-Datum und lokale Änderungen. Die Anzeige kürzt die
  Revision und trennt Commit- und Build-Datum von Python-/Qt-Versionen.
- [x] Beim Quellstart nur den eindeutig erkannten Projekt-Checkout lesend
  abfragen. Git-Abfragen haben ein Zeitlimit, festes Arbeitsverzeichnis und
  verändern den Index nicht; fremde übergeordnete Repositorys werden nicht
  als Herkunft verwendet.
- [x] Nach Commit oder Branchwechsel die Herkunft beim nächsten Start bzw.
  Öffnen des Infofensters neu lesen. Detached HEAD gesondert darstellen;
  fehlende Herkunft ausdrücklich anzeigen, statt ein altes Datum als
  aktuellen Stand auszugeben. Bei lokalen Änderungen bleibt das Commit-Datum
  das Datum des letzten Commits; der Status kennzeichnet die Abweichung.
- [x] Installierte Pakete und eingefrorene Anwendungen lesen
  `dxf2gcode/_build_metadata.json` ohne Git. Deren Branch bezeichnet die
  Build-Quelle, keinen lokalen Branch auf dem Rechner des Endnutzers.
- [x] `tools/build/setuptools_commands.py` erzeugt die Metadatendatei nur
  im Build-Verzeichnis beziehungsweise Quellarchiv. Ein Wheel daraus
  übernimmt Revision, Branch, Status und Zeitstempel unverändert.
- [x] `tools/build/windows.py` bindet entsprechende Metadaten in EXE/MSI
  ein. Die Datei wird nicht in den Quellcheckout geschrieben oder als
  Quelländerung eingecheckt. `SOURCE_DATE_EPOCH` ermöglicht reproduzierbare
  Build-Zeitstempel.
- [x] Infofenster und G-Code-Kopf verwenden Paketversion und bekannte Herkunft.
  Die Bewegungsbefehle ändern sich durch die Herkunftsanzeige nicht.
  Beschriftungen in Deutsch, Französisch und Russisch sind implementiert.
- [x] Alte Perl-Keywordfilter, Attributzuordnung, Keyword-Anleitung und lokale
  Filterkonfiguration entfernen. Ein Commit-/Post-Commit-Hook ist für den
  neuen Ablauf nicht nötig; weder Push noch erneuter Checkout sind zur
  Aktualisierung der Herkunftsanzeige im Quellstart erforderlich.

Der Status wurde bei der Zusammenführung anhand des vorhandenen Providers,
der Build-Anbindungen und der fokussierten Tests abgeglichen. Er bedeutet
keine neue Abnahme eines vollständig gebauten oder auf Debian installierten
Pakets.

### Vorhandene fokussierte Prüfungen

`tests/dxf2gcode_version_metadata_test.py` deckt saubere/geänderte Checkouts,
neue Commits, Branchwechsel, Detached HEAD, fehlendes/fehlerhaftes Git,
ungültige oder zur Version unpassende Metadaten, Paketressourcen ohne Git
und die Übernahme aus Quellarchiven ab. Fremde umgebende Repositorys dürfen
keine Herkunft liefern. Ein frisch erzeugter Build-Baum darf den zuvor
erfassten Quellstatus nicht nachträglich als geändert markieren.

Die Setuptools-/MSI-Anbindung wird außerdem mit kleinen Build-Bäumen und
ersetztem Setup-Aufruf geprüft. Kompilierte Kataloge und das Infofenster
wurden fokussiert geprüft; Beschriftungen unterscheiden fehlende Herkunft
von fehlendem aktivem Branch und behandeln Anzeigenamen als Text.
Diese Angaben übernehmen den bisherigen dokumentierten Prüfstand; bei der
Dokumentzusammenführung wurden die Anwendungstests nicht neu ausgeführt.

Die Implementierung ist erledigt; die Abnahme fertiger Artefakte bleibt
als [M1 in der aktiven Todo](toolpath-refactoring-completed.md#m1-macos-dropped) offen.

## Abgeschlossene Bereinigung

**Abgeschlossene Bereinigung:** `.kilo/` und die erzeugte Datei `.coverage`
sind entfernt. Der frühere Plan bleibt unter
[archive/machine-comp-radius-leadin-plan.md](machine-comp-radius-leadin-plan.md)
als ausdrücklich historische Referenz erhalten. `.coverage` ist bereits
ignoriert und kann durch einen späteren Coverage-Lauf erneut entstehen.

## Bewusst verworfene Anforderungen

Diese Punkte wurden ausdrücklich abgewählt; sie sind weder implementiert
noch offene Aufgaben. Sie werden nur zur Abgrenzung aufbewahrt.

### I1 – Zu kurze Segmente in der Vorschau markieren

**Entfallen – ausdrücklich nicht gewünscht (30.10.2026).** Das Merkmal
„Too short segments highlighting“ aus dem Ticket wird nicht umgesetzt und
zählt nicht als offene Aufgabe. Bestehende Geometrievalidierung und andere
Diagnosen werden dadurch nicht entfernt oder geändert.

### R4 – Ticket #157: Layer alphanumerisch sortieren

**Entfallen – ausdrücklich nicht gewünscht (30.10.2026).** Keine
alphanumerische/natürliche Layersortierung aus diesem Ticket implementieren.
Der Eintrag bleibt nur zur Dokumentation der Abgrenzung erhalten und zählt
nicht als offene Aufgabe. Die manuelle Bearbeitungs-/Exportreihenfolge aus
R1/R2 bleibt davon unberührt.

## Einordnung der früheren Abnahmetore

Die früher durchgehend offenen Kontrollkästchen werden nicht als neun neue
Implementierungsaufgaben fortgeführt. Vorhandene Nachweise und verbleibende
Grenzen sind getrennt zu lesen:

| Kriterium der früheren Liste | Dokumentierter Stand / verbleibende Grenze |
| --- | --- |
| Planung, Geometrie, Vorschau und Formatierung getrennt testbar | Nachweise aus Etappen 1–6; keine G-Code-Ausgabe aus Geometrieklassen |
| Verhaltenstests und unveränderte Golden-Ausgaben je Scheibe | Repräsentative Fallmatrix, 18 bisherige und acht ergänzende Referenzen |
| Vollsuite nach Migration | 775 Tests unter Windows und Debian bestanden; spätere Darstellungskorrektur nur fokussiert geprüft |
| Gemeinsamer unveränderlicher Plan für GUI/CLI und Werkzeugwegvorschau | Gemeinsamer Planvertrag, Planer und Exportadapter; Originalgeometrie bleibt eine gesonderte Grunddarstellung |
| 2D-Deduplizierung und 3D-Tiefen | Projektionstests und fokussierte Darstellungskorrektur; kein manueller GPU-Nachweis |
| Software-/Maschinenkompensation unterscheidbar | Geometrie beziehungsweise explizite Zustandsaktionen und Tooltip; bestehende Bahnfarben erhalten |
| Unterstützte und nicht unterstützte Kombinationen vollständig erfasst | Repräsentative Fallmatrix sowie B1/B2 und Pocket-Gültigkeit geprüft; [A1-Abschluss](#a1-complete), keine universelle Maschinenfreigabe |
| Importfreiheit von Domain und Application | Alle Domain-/Application-Module ohne Qt, Runtime-Globals oder konkrete Adapter importiert; [A1-Abschluss](#a1-complete) |
| Alte Shape-Ausgabe und doppelte Werkzeugwegplanung entfernt | Etappen 2/4/6; für Anzeigezugriffe verbleiben lediglich aus Planaktionen abgeleitete Werte |

Fertige Pakete und ihre Herkunft werden erst mit
[M1](toolpath-refactoring-completed.md#m1-macos-dropped) abgenommen. Eine allgemeine
Release-Freigabe oder ein Nachweis physischer Bearbeitungsqualität folgt aus
den dokumentierten Tests nicht.

### Metadaten: früherer Keyword-Mechanismus

Vor der Umstellung am 30.10.2026 verwendete das Infofenster
`domain/constants.py`: `VERSION` enthielt nur Python/PyQt; `DATE`, `REVISION`
und `AUTHOR` kamen aus expandierten Git-Keywords. Die Paketversion fehlte
in dieser Anzeige. Deshalb konnte selbst ein Wheel mit Version `20261030`
noch den 11. Oktober als vermeintlich aktuellen Stand anzeigen.

Die damalige `.gitattributes` ordnete `*constants.py` dem lokalen
`rcs-keywords`-Filter zu. `clean` entfernte Expansionen beim Übernehmen in
den Index, etwa durch `git add`; `smudge` expandierte beim Schreiben aus Git
ins Arbeitsverzeichnis, etwa beim Checkout. Commit und Push aktualisierten
die expandierten Arbeitsdateien nicht automatisch. Der Filter las zudem
`HEAD` über `git log` und belegte damit keine unveränderliche Herkunft eines
später gebauten Pakets. Hintergrund:
[Git-Dokumentation zu Attributfiltern](https://git-scm.com/docs/gitattributes).
Dieser Abschnitt beschreibt den entfernten Mechanismus, keinen weiterhin
erforderlichen Einrichtungsschritt.

Der ursprüngliche Metadatenplan bestand aus Provider, gemeinsamer Herkunft
für Wheel/Quellarchiv/MSI, umgestellter und übersetzter Anzeige, Entfernung
der Keywords sowie Checkout-/Buildtests. Diese lokalen Schritte sind oben
als umgesetzt erfasst; seine abschließende Paket-/Debian-Prüfung bleibt [M1](toolpath-refactoring-completed.md#m1-macos-dropped).

## Historische Ausgangslage und ursprüngliche Etappen

Die folgenden Angaben bewahren den Kontext des ursprünglichen
Werkzeugwegplans. **Alte Pfade und Methoden sind keine aktuellen Zielpfade
und sollen nicht wiederhergestellt werden.** Der aktuelle Aufgabenstatus
steht in der [aktiven Todo](../todo.md). Die folgenden
Etappen- und Abschnittsnummern beziehen sich auf die frühere Todo-Struktur,
nicht auf die neue Prioritätsreihenfolge.

### Damalige Kopplungen

- `core/stmove.py` erzeugte Anfahr-/Offsetgeometrie und Pocket-Bahnen in
  derselben veränderlichen Sammlung und enthielt Vorschau-Zeichenlogik.
- `core/shape.py:Write_GCode()` wählte Software-/Maschinenkompensation,
  Tiefenpässe, Richtungsumkehr, Tabs, Leads und Rückzüge; Schleppmesser
  verwendeten einen eigenen Exportpfad.
- `core/linegeo.py` und `core/arcgeo.py` formatierten durch direkte
  Postprocessor-Aufrufe ihre Bewegungen selbst.
- `core/pocketmill.py` las StMove-Zustand und hängte Pocketgeometrie an
  dessen Liste. `postpro/postprocessor.py` orchestrierte Layer/Shapes und
  formatierte gleichzeitig Steuerungsbefehle.
- Maschinenart, Kompensationsverantwortung und G40-/G41-/G42-Richtung
  wirkten über mehrere dieser Module hinweg.
- Die Vorschau zeigte nur Teile des Weges. Export expandierte Tiefenpässe,
  kehrte offene Konturen um, wählte Tabs pro Pass und erzeugte eigene
  Zustellungen/Rückzüge. Diese Mehrfachberechnung motivierte die gemeinsame
  Planquelle und getrennte 2D-/3D-Projektionen.

### Zuordnung der früheren Etappen zur heutigen Liste

Die frühere Nummerierung wird hier ausschließlich erklärt; für neue Aufträge
gelten die Abschnittsnummern dieses Dokuments.

| Frühere Etappe | Inhalt und heutige Zuordnung |
| --- | --- |
| 0 – Verhaltensmatrix | Vor Änderungen gültige Maschinenarten, Software-/Maschinenkompensation, G40/G41/G42, offene/geschlossene Konturen, Tiefenpässe, Tabs, Leads, Überfahrt, Pocket-Richtung und Postprocessor-Regeln festhalten; heute Abschnitt 1 und die Fallmatrix in Abschnitt 3 |
| 1 – Plan-Datenmodell | Qt-/Postprocessor-freie Pässe/Aktionen zunächst aus bestehenden StMove-Geometrien gewinnen, ohne gleichzeitig Algorithmen umzuschreiben; heutiger Stand und Abschnitte 1/2 |
| 2 – Shape-Ausgabe entkoppeln | Orchestrierung aus `Shape.Write_GCode()` verlagern; mit einfachem Fräsen beginnen, dann Kompensation, Mehrfachpässe und offene Konturen; heute Abschnitte 2–4 |
| 3 – Vorschau anbinden | Gemeinsame Bewegungs-/Passdaten, 2D ohne Mehrfachlinien, 3D mit Z, keine eigene Tab-/Lead-out-Planung; heute Abschnitt 5 |
| 4 – Geometrie aus StMove lösen | Offset, Leads, Pocket und Messerspitzenweg in explizite Geometriefunktionen/Planer verschieben; StMove nur während der Migration adaptieren und erst nach Migration seiner Aufrufer entfernen/umbenennen; heute Abschnitte 3/5/6 |
| 5 – Strategien/Randfälle | Drehmaschine, Schleppmesser, Postprocessor-Fähigkeiten und gültige Pocket-/Kompensationsfälle vervollständigen; Gültigkeitsgrenzen zentral prüfen; heute Abschnitte 1/3/4/6 |
| 6 – Alte Kopplungen entfernen | Direkte Geometrieausgabe, doppelte Pass-/Tab-/Lead-Berechnung und globale Zustandszugriffe nach Umstellung der Aufrufer entfernen; heute Abschnitt 6 und Abnahmetore |

Als frühe Verhaltensbasis waren 644 Tests und 73 % Gesamtabdeckung
dokumentiert. Diese historischen Zahlen sind weder der aktuelle Stand noch
ein Ersatz für gezielte Verhaltenstests. Die späteren Ergebnisse nach
Abschnitt 2 sind separat unten erhalten. Die alte Arbeitsregel sah eine
Vollsuite nach jeder Etappe vor; gemäß der späteren Nutzerfestlegung gelten
jetzt fokussierte lokale Prüfungen und eine gesonderte Freigabe für lange
Läufe. Das abschließende Vollsuite-Abnahmetor bleibt bestehen.

## Prüfstand nach Abschnitt 2

Historischer Prüfstand des damaligen Abschnittsabschlusses; diese Läufe
wurden bei der Untersuchung vom 30.10.2026 nicht erneut ausgeführt.

- Gezielte Lead-, Diagnose-, Planvertrag- und Golden-G-Code-Regressionen: 151 Tests
  bestanden.
- Vollständige Suite über `python tests/run_tests.py full`: 706 Tests
  bestanden; alle 18 bestehenden Golden-G-Code-Fälle bestehen unverändert.
- Grenztests importieren den neuen Domain-Planer ohne Qt oder globale
  Laufzeitvariablen. Vertragstests prüfen wiederholbare Planung, unveränderte
  Eingaben und das Ausbleiben sämtlicher Postprocessor-Bewegungsaufrufe.
- Qt-Projektmetadaten enthalten die neuen Dateien und keine entfernten
  Module. Diagnoseübersetzungen sind in Deutsch, Französisch und Russisch
  vorhanden, kompiliert und geprüft.
- Abschnitt 1 (Verhalten und Planvertrag), Abschnitt 2 (reine
  Planungsstrategien) und Abschnitt 5a (Werkzeugänderung pro Shape) sind
  abgeschlossen. Die fachliche Fallmatrix in Abschnitt 3 und die weitere
  Geometrie-/Vorschauentkopplung waren zu diesem historischen Zeitpunkt noch offen.

## Architektur-Migrationsstand vom 29. Oktober 2026

Aus dem früheren Architekturbericht übernommen. Diese zeitgebundene
Bestandsaufnahme wird historisch bewahrt; sie ist keine aktuelle
Prüfung des Codes und kein zusätzlicher Umsetzungsauftrag. Für offene
Arbeiten gilt die [aktive Todo](../todo.md).

### Damals offene Architekturgrenzen

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

<a id="gui1-p1-p2"></a>

## GUI1 P1/P2 – gemeinsame Darstellung und optionaler VisPy-Prototyp

Stand: **15.11.2026**, Arbeitszweig `ribbon-2d-3d`. Lokal umgesetzt;
Nutzerprüfung bestätigt: „Ist geprüft und funktioniert soweit wie erwartet.“
Damit ist der vorgesehene Nutzerprüfpunkt für P1/P2 abgeschlossen. Die Rückmeldung
enthält keine separate Aufschlüsselung nach Dateien oder Einzelfällen und ist
keine zusätzliche Plattform-/Paketabnahme. Nicht nach `develop` übernommen und
nicht veröffentlicht; die Rendererentscheidung bleibt offen.

- `application/view_scene.py`: renderer-unabhängige IDs, Pfade, 2D-/3D-Projektion
  und Trefferprüfung; kein Qt-/VisPy-Import und keine separate Planung.
- Adapter aus bestehenden Projekt-/Planungsdaten, mit Originalkonturen,
  Operationen, Diagnosen und Stegregionen. Auswahländerungen nutzen denselben
  Snapshot; Tiefenänderungen aktualisieren ihn.
- Zusätzliche Ansichtsleiste und optionaler VisPy-Viewport: fester Draufblick,
  räumliche Kamera, Einpassen, bestehende Farben/Linienrollen, Beschriftungen,
  Start-/Endmarkierungen, Einzel-/Mehrfachauswahl und Baumkopplung. Mehrere
  Treffer verlangen eine ausdrückliche Auswahl. Der alte Canvas bleibt erhalten.
- PyQt6/VisPy erst bei Verwendung initialisieren; fehlende Abhängigkeiten
  deaktivieren die Aktionen. Erkannte Fehler führen zum bisherigen Canvas zurück.
  VisPy bleibt ein optionales Extra; CLI-/2D-Start importieren VisPy nicht.
- DE/FR/RU-Texte ergänzt; QM-Dateien kompiliert, ihre neuen Einträge geladen und
  gegen die TS-Texte geprüft. Bestehende unvollständige andere Katalogeinträge
  wurden nicht als Teil dieser Änderung überarbeitet.

**Gezielte Nachweise:**

- Neue `dxf2gcode_view_scene_test.py`: **4 Tests unter PyQt5 und PyQt6 bestanden**.
  Projektion ohne doppelte Tiefenpasslinien, räumliche Z-Werte, stabile getrennte
  Treffer-IDs, fehlender Renderer/Initialisierungsfehler mit nutzbarem 2D-Canvas,
  vollständige neue Übersetzungen einschließlich QM-Lookup.
- Vorhandene `dxf2gcode_machining_panel_test.py`: **2 Tests je Qt-Bindung bestanden**
  (bestehende reale Qt-Auswahl-/Projekt-/Bearbeitungsabläufe).
- Nativer Windows-Grafiklauf `--gpu-worker` mit PyQt **6.12.0**, VisPy **0.17.0**,
  NumPy **1.26.4**, OpenGL **4.6.0 Compatibility Profile Context 26.2.2.260218**.
  `BreakExample_Circle.dxf` plus zweite Bearbeitung derselben Originalkontur:
  reale Framebuffer-Ausgabe, räumlicher/Draufblick, Projektion für Treffer,
  Mehrfachauswahl, Stegregionen, Snapshot-Wiederverwendung und Tiefenänderung
  geprüft; Rückkehr zu 2D und unveränderte Projektdaten bestätigt.
  Screenshots unter `.tox/view-prototype-spatial.png` und
  `.tox/view-prototype.png` visuell geprüft (lokale, nicht versionierte Artefakte).

**Grenzen:** Keine Vollsuite, Paket-/MSI-/Releaseprüfung oder Debian-/SSH-/macOS-
Abnahme. Keine vergleichenden Geschwindigkeitsaussagen aus dem kleinen Grafiklauf.
Manuelles Zeichnen/Verschieben/Bemaßen von Stegen bleibt P5; produktive Ablösung
des bisherigen Canvas ist nicht freigegeben. Ein nativer Treiberabsturz ist kein
durch Python generell abfangbarer Initialisierungsfehler.

Weitere Etappen: [Vergleichsplan](../planning/gui1-renderer-comparison-plan.md).
Startweg und bekannte Einschränkungen: [Bediennotizen](../documentation-notes/view-renderer-comparison.md).

<a id="gui1-p3"></a>

## GUI1 P3 – Qt Quick 3D mit gemeinsamer Projektanbindung

Stand: **15.11.2026**, lokal auf `ribbon-2d-3d`. Keine Nutzerabnahme des neuen
Kandidaten, kein Commit/Push, kein Merge oder Release aus dieser Etappe.

- `quick3d_view.py` und `resources/view_comparison.qml`: native Qt-Quick-Ansicht
  mit orthografischer Draufsicht und frei drehbarer räumlicher Kamera, Zoom,
  Verschieben, Einpassen, Konturen, Operationen, Stegen und Beschriftungen.
- Derselbe Snapshot wie VisPy; gleiche stabile IDs und Projektbefehle.
  Gemeinsame Auswahl-/Trefferregeln und Stile nach `view_interaction.py`
  verlagert. Auswahl verändert keine Projektdaten und plant nicht erneut.
- Qt-Quick-Linien als kamerazugewandte Dreiecksbänder mit Vertexfarben und
  Bildschirmbreiten, gemeinsame Strichelung, QML-Auflage für Texte und S/E.
  Projektion entspricht `View3D.mapFrom3DScene`, ohne künstliche XY-Verschiebung.
- Native `QQuickView`-Einbettung statt gemeinsamem `QQuickWidget`-Compositor:
  VisPy/OpenGL und Qt Quick/Direct3D 11 im selben Hauptfenster geprüft.
  Fehler deaktivieren nur den betroffenen Kandidaten und führen zu 2D zurück.
- Erster nativer Frame vor Readback abwarten, QML-/Grafikfehler und Frame-Timeout
  behandeln. Ein zu früher Readback ließ die geprüfte Qt-6.12-/D3D11-Kombination
  leer bleiben; mit verzögerter Prüfung reale Geometrie sichtbar.
- Renderer beim Schließen explizit freigeben und den ursprünglichen Qt-Message-
  Handler nach VisPy-Initialisierung erhalten. Eine während der Erprobung
  beobachtete Ressourcen-/Loggingwarnung beim Beenden des Mischbetriebs trat in
  den abschließenden nativen Läufen beider Aktivierungsreihenfolgen nicht auf.
- QML in Paketdaten und Source-Manifest aufgenommen; optionales Extra
  `view-quick3d`. Drei neue UI-Texte DE/FR/RU übersetzt, QM-Dateien regeneriert.

**Gezielte Nachweise:**

- `dxf2gcode_view_scene_test.py`: **5 Tests unter PyQt6 bestanden**, unter
  PyQt5 **4 bestanden / 1 passend übersprungen**. Einschließlich Pixelbreite und
  unveränderter Mittellinie der Dreiecksgeometrie, Fehlerisolierung je Renderer
  sowie neuer TS-/QM-Übersetzungen.
- `dxf2gcode_machining_panel_test.py`: **2 Tests je Bindung bestanden**;
  vorhandene Auswahl-, Parameter-, Projekt- und History-Abläufe unverändert.
- Windows/PyQt **6.12.0**: native Worker `--quick-worker`, `--gpu-worker` und
  isoliert `--quick-only-worker` mit echten Framebuffer-Ausgaben. Qt Quick:
  **Direct3D11Rhi**; VisPy: **OpenGL 4.6 Compatibility Profile**.
  `BreakExample_Circle.dxf` plus zweiter Bearbeitung derselben Originalkontur:
  Bildinhalt, Start in Draufsicht, räumliche Ansicht, Qt-Projektionsvergleich
  mit weniger als einem Pixel Abweichung, echter QML-Mausklick, Kamera/Zoom,
  Mehrfachauswahl, Tiefenänderung, Snapshot-Wiederverwendung und Rückkehr zu 2D.
  Beide Aktivierungsreihenfolgen nutzten denselben Snapshot; Projektdaten nach
  Ansicht/Auswahl unverändert. Screenshots `.tox/quick3d-prototype*.png` lokal
  erzeugt; räumliche Ausgabe visuell geprüft.

**Grenzen:** Keine Vollsuite, MSI-/Paket-/Releaseprüfung oder Debian-/Linux-/macOS-
Abnahme; keine Aussage zur schnelleren Bibliothek. Vergleich großer Projekte,
Linienqualität und Bediengefühl bleiben P4, geometrische Stegbearbeitung P5.
Die produktive Ablösung des bisherigen Canvas ist nicht freigegeben.

Offene Schritte: [P4–P6](../planning/gui1-renderer-comparison-plan.md).
Bedienung und Quellen: [Renderer-Vergleich](../documentation-notes/view-renderer-comparison.md).

<a id="gui1-quick-navigation"></a>

## GUI1 – Qt-Quick-3D-Navigation ohne unnötigen Geometrieaufbau

Stand: **15.11.2026**, lokal auf `ribbon-2d-3d`. Nutzer meldete rucklige
Navigation; der vereinbarte begrenzte Optimierungsschritt ist umgesetzt.

- 16-ms-Aktualisierung ohne Neustart eines bereits laufenden Timers. Fortlaufende
  Mausereignisse verhindern damit nicht mehr die nächste Aktualisierung.
- Projektionen und vorbereitete Endpunkte/Grenzen wiederverwenden. Linienrollen
  und Strichelung werden bei reiner Rotation nicht erneut aufbereitet.
- Reines Verschieben aktualisiert nur Kamera und gegebenenfalls Beschriftungen;
  kein neuer Vertexpuffer. Rotation/Zoom aktualisieren die kamerazugewandten
  Bänder weiterhin, mit vereinfachter numerischer Aufbereitung statt vieler
  temporärer Qt-Vektoren und Grenzberechnungen je Dreiecksvertex.
- Kamera-/Beschriftungssignale getrennt; unveränderte Beschriftungen lösen kein
  erneutes Zeichnen der QML-Auflage aus. Farben, Auswahl und Projektbefehle
  bleiben erhalten; keine neuen GUI-Texte oder Übersetzungseinträge.

**Begrenzte Messung:** gleiche lokale Windows-/Python-3.11-/PyQt-6.12-/D3D11-
Umgebung, `BreakExample_Circle.dxf` mit zweiter Bearbeitung einer Originalkontur,
ausgewählte Operationen und sichtbare räumliche Ansicht. Median von je zwölf
direkt ausgeführten Python-`redraw()`-Aufrufen; keine GPU-/FPS-Messung und kein
Vergleich mit VisPy. Vorherige Implementierung vor dem Umbau lokal gesichert.

| Aktion | Vorher CPU ms | Nachher CPU ms |
| --- | ---: | ---: |
| Verschieben | 44,346 | 0,047 |
| Drehen | 47,405 | 13,854 |
| Zoomen | 40,566 | 19,032 |

Nachher: **0 Geometrieübertragungen bei zwölf Verschiebungen**, jeweils zwölf
bei Rotation und Zoom. Der Worker `--quick-benchmark` erzeugt die Messung aus dem
aktuellen Stand; frühere Implementierung ist nicht Teil des Produktcodes.

**Gezielte Prüfung:** `dxf2gcode_view_scene_test.py`: fünf Tests unter PyQt6
bestanden; unter PyQt5 vier bestanden, ein Qt-Quick-spezifischer Test passend
übersprungen. Nativer Direct3D11-Worker einschließlich Bildausgabe, QML-Klick,
Projektion, Kamera/Zoom, Auswahl, Tiefenänderung und Rückkehr zum bisherigen
Canvas bestanden. Zusätzliche native Regression: keine Geometrieübertragung
beim Verschieben, Übertragung beim Drehen, laufende Draw-Timer trotz eines
2-ms-Ereignisstroms. Bildschirmbreite/Mittellinie der Bänder weiter geprüft;
aktuelle räumliche Ausgabe lokal visuell kontrolliert.

**Grenzen:** keine Vollsuite, Paket-/Release- oder weitere Plattformabnahme.
Große Datenmengen können bei Rotation/Zoom weiterhin Aufwand verursachen.
Erneute Nutzerbeurteilung und vergleichende Bewertung bleiben
[P4](../planning/gui1-renderer-comparison-plan.md).

<a id="gui1-vispy-lines-benchmark"></a>
## GUI1 – GL-/AGG-Performance und RAM an Rippen-DXF (16.11.2026)

Auf ausdrücklichen Nutzerauftrag `AFluegel Rippen b2 0201.dxf` nativ unter
Windows/AMD RX 6700 XT geprüft: 63 Konturen, 63 Bearbeitungen, 21.647 projizierte
Segmente, Qt 6.12/VisPy 0.17. Separates Werkzeug
`tools/benchmark_vispy_lines.py` mit frischen Prozessen, temporärer Konfiguration,
einer Methode pro Adapter und unverändertem Projekt. Produktionsansicht und
Einstellungen nicht umgestellt.

Die einfache AGG-Variante hätte nach Einpassen 4.962 Visuals benötigt und wurde
an der Vorabgrenze von 1.500 gestoppt; keine tatsächliche Laufzeit-/RAM-Abnahme
für diesen Ansatz. GL und gebündeltes AGG wurden vollständig durchlaufen,
einschließlich Pan, Zoom, Einzel-/Mehrfachauswahl und Prozessspeicherzählern.
Das gebündelte Experiment verwendet VisPys privaten Strip-Baker; dessen
Produktivübernahme ist ausdrücklich nicht freigegeben.

Beispielmediane einschließlich GPU-Readback: Pan/Mehrfachauswahl mit Neuaufbau
124 ms GL / 317 ms AGG, Zoom 131 / 303 ms, Auswahlwechsel 427 / 630 ms.
Isolierter Kamera-Pan ohne Upload bei 24 ausgewählten Bearbeitungen dagegen
8,23 / 11,22 ms (je 30 Proben, keine Uploads beobachtet). Peak-Working-Set im
vollständigen Ablauf 448 / 497 MiB; Private-Commit-Spitze 830 / 884 MiB.
Keine VRAM-, Langzeit-Leck- oder Bildschirm-FPS-Messung.

Die zugrunde liegende Darstellungsleistung ist damit für weitere AGG-Erprobung
plausibel; vor einer Umstellung sind Bündelung und Cache für Navigation und
Auswahl nötig. Zoomen und Auswahl sind durch die Kamera-Gegenprobe nicht
optimiert. Die vollständigen Methoden, Hardware-/Skalierungsbedingungen,
Streuwerte, Schutzgrenzen und fünf JSON-Rohdaten stehen im
[Messbericht](../documentation-notes/vispy-line-benchmark.md).
Erzeugte AGG-Aufnahme visuell geprüft; CLI-Hilfe und Python-Syntax geprüft.
Keine Vollsuite, Debian-/3D-/Paket-/Releaseabnahme oder abschließende Rendererwahl.

<a id="gui1-vispy-gl-cache"></a>
## GUI1 – Einheitliche VisPy-GL-Linien und Cache (16.11.2026)

Nach ausdrücklicher Nutzerentscheidung für GL anstelle des 2D-beschränkten
AGG-LineVisual den VisPy-Prototyp für Modell-/Werkzeugweglinien in beiden
Ansichten auf `method='gl'` umgestellt. Kein AGG-Produktionspfad und keine
Übernahme seiner internen Muster. Die vorhandene Strich-/Punktaufteilung bleibt
als gebündelte GL-Segmentdarstellung erhalten; Qt-Auflagen für Stege/Maße bleiben.

Projektionen/semantische Arrays pro Snapshot und Ansicht speichern, Strichdaten
pro Maßstab zwischenspeichern und Gruppen nur bei tatsächlicher Änderung
hochladen. Pan lädt keine Linien, Zoom nur geänderte Strichgruppen; Auswahl
berechnet keine Planprojektionen. Veraltete Stilobjekte entfernen und vor dem
ersten Upload einpassen. Reine Auswahl baut den versteckten Legacy-Canvas bei
unverändertem Projekt/Transform/Konfiguration/Postprozessor nicht mehr auf;
Rückkehr und Grafikfehler aktualisieren ihn. Parameteränderungen und automatische
Exportreihenfolge behalten den vollständigen Aktualisierungspfad. Diagnosen
aller Operationen aus dem aktuellen Snapshot in den Baum übernehmen.

Exakt deckungsgleiche nicht ausgewählte Schnittsegmente in der Draufsicht unter
der Originalkontur aussparen, damit dünne AA-Ränder keine blauen Fragmente
erzeugen. Plan, Export und räumliche Bahnen bleiben erhalten. Alpha-Blending
explizit gesetzt; AGG-Breitenfaktor entfernt. GL-Strichstärken/Ecken bleiben
treiberabhängig und bedürfen optischer Nutzerprüfung.

**Prüfung:** sieben fokussierte Tests unter Qt6, sechs unter Qt5 und ein
Qt-Quick-Test übersprungen. Bestehende Bearbeitungs-/Übersetzungsprüfungen je
zweimal unter Qt5 und Qt6 bestanden. Native GPU- und Stegbearbeitungsworker
bestanden: Raum-/Draufsicht, Auswahl, Planänderung, transparente Körper,
Rückkehr zum alten Canvas, Maße/Zeichnen/Fang/Undo, Cache-Invalidierung,
ausbleibende Pan-Uploads, unveränderte Schnittarrays bei Zoom, begrenzte
Stilobjekte und Timer unter fortlaufenden Ereignissen. GL-Aufnahme visuell geprüft.

**Rippen-DXF nach Optimierung:** gleiche Umgebung/Größe wie im vorherigen
Vergleich, aktueller Produktionspfad über `--method current`. Mediane inklusive
Readback: Pan/Mehrfachauswahl 9,98 statt 123,84 ms, Zoom 20,99 statt 130,80 ms,
Mehrfachauswahlwechsel 26,21 statt 426,88 ms. Peak-Working-Set 356 statt 448 MiB,
Peak-Private-Commit 755 statt 830 MiB. Projektinhalt unverändert geprüft.
[Nachtrag und JSON-Rohdaten](../documentation-notes/vispy-line-benchmark.md#nachtrag-gl-optimierung).
Keine neue Debian-, Paket-, Vollsuite-, Release- oder physische Maschinenabnahme.

## GUI1 – Verzögerte Canvas-Auswahl durch Trefferprüfung (16.11.2026)

Auf Nutzerhinweis den zuvor nicht gemessenen Maus-/Picking-Pfad geprüft.
Die Rippen-DXF benötigte ca. 2,49 s pro Auswahlklick und 8,10 s für Auswahl
plus Leerraum-Abwahl: jede Segmentkoordinate wurde einzeln projiziert und bei
Leerraum zusätzlich die gesamte Originalgeometrie durchsucht. Die vorherigen
Auswahlmessungen begannen bei Baum-Auswahl und deckten diese Ursache nicht ab.

VisPy verwendet jetzt Snapshot-/Ansichtsdaten, eine gebündelte Transformation,
vektorisierte Abstände und einen invalidierbaren Bildschirmcache. Nearest-
Trefferliste, Toleranz und Mehrfachtreffer-Menü bleiben erhalten. Leerraum-
Abwahl wird als eine logische Auswahländerung statt mehrerer Repaints behandelt.

Echte Qt-Klickmessung mit gleichem Eingabepunkt, zwei Aufwärmabläufen und je drei
Proben: Auswahl ca. 71 ms, Auswahl plus Leerraum ca. 93 ms, jeweils inklusive
Bildabruf und automatischer erster Menüwahl bei Mehrfachtreffern. Prozess-
Working-Set-Spitze ca. 356 statt 350 MiB im kurzen Klicktest. Keine FPS- oder
Langzeit-/Leck-Aussage. [Rohdaten und Grenzen](../documentation-notes/vispy-line-benchmark.md#canvas-klickpfad).

Native Stegbearbeitungs-/Pickingprüfung bestanden: Trefferlisten stimmen in
geprüften Fällen mit der bisherigen Referenz überein, einschließlich Kamera-,
Ansichts- und Sichtbarkeitswechsel, Nullsegmenten und leerem Snapshot. Keine
per-Endpunkt-Projektion im neuen Picking; Cache-Wiederverwendung nachgewiesen.
Leerraum erzeugt einen Auswahlwechsel und leert den Kontext. Sieben Tests unter
Qt6, sechs unter Qt5 plus ein übersprungener Qt-Quick-Test bestanden. Nativer
Qt-Quick-/VisPy-Interoperabilitätsworker bestanden. Keine Vollsuite, Debian-,
Paket- oder Releaseprüfung; Nutzerprüfung am eigenen Klickablauf bleibt offen.

## GUI1 – GL-`connect='strip'` zum Vergleich (16.11.2026)

Auf ausdrücklichen Nutzerwunsch durchgezogene, zusammenhängende Pfadstücke
als native GL-Line-Strips umgesetzt. Unabhängige Stücke/Konturen/Rollen nicht
verbinden; Strich-/Punktlinien weiter als GL-Segmente bündeln. Der aktive
Prototyp-Schalter `VispyView.SOLID_CONNECT = 'strip'` kann für den bisherigen
Weg auf `'segments'` zurückgesetzt werden. Keine AGG-Rückkehr oder Exportänderung.
Strip-Objekte je Snapshot/Ansicht/Pfadstück wiederverwenden, statt bei jeder
Auswahl neue GL-Objekte zu erzeugen; neuen Snapshot mit leerem Pool beginnen.

Native Steg-/Cache-/Picking-/Lückenprüfungen und GPU-Worker bestanden.
Framebuffer-Zwischenräume getrennter Stücke bleiben weiß, Muster bleiben
unterbrochen, Rückwechsel funktioniert und Pool-Objekte werden wiederverwendet.
Sieben Tests unter Qt6, sechs unter Qt5 und ein übersprungener Qt-Quick-Test
bestanden. Strip-Aufnahme visuell geprüft; tatsächlicher Eckvorteil bedarf
Nutzerbeurteilung auf dem eigenen Grafiktreiber.

Rippen-DXF, gleiche Messbedingungen: 260–462 aktive LineVisuals statt 3–8.
Pan/Mehrfachauswahl ca. 88 statt 10 ms, Zoom ca. 104 statt 21 ms,
Baum-Mehrfachauswahlwechsel ca. 103 statt 26 ms. Peak-Working-Set ca. 447 statt
356 MiB. Der Versuch bleibt wie beauftragt aktiv, ist aber keine Performance-
Freigabe für die endgültige Ansicht. [Messung/Rohdaten](../documentation-notes/vispy-line-benchmark.md#strip-versuch).
Keine Vollsuite, neue Plattform-, Paket- oder Releaseabnahme.

## GUI1 – Strip-Versuch nach Nutzerprüfung zurückgenommen (16.11.2026)

Der Nutzer erkennt keinen optischen Vorteil und hat die Rückkehr zur vorherigen
Umsetzung beauftragt. Gebündelte GL-Segmente in Drauf- und Raumansicht wieder
hergestellt; Strip-Schalter, Strip-Objektpool und experimentelle Cache-Zweige
entfernt. Projektions-/Strich-/Upload-Caches, schnelle vektorisierte Trefferprüfung,
gesammelte Leerraum-Abwahl und verzögerte Aktualisierung des versteckten Canvas
bleiben erhalten. Keine Geometrie-/Planungs-/Exportänderung.

Native Cache-, Steg-, Picking-, Überlagerungs- und Segment-Lückenprüfungen
bestanden. Wenige nach Stil gebündelte Visuals, getrennte Konturen und
Strichlücken geprüft. Der historische Strip-Vergleich bleibt als Nachweis;
Entscheidung ist aus dem offenen Plan entfernt. Kein erneuter langer Benchmark
für die Rücknahme erforderlich; keine Paket-/Plattform-/Releaseabnahme.

## GUI1 – Standard-AGG-LineVisual: direkte XYZ-Daten geprüft (16.11.2026)

Auf Nachfrage die bisher zu pauschal formulierte 2D-Grenze präzisiert.
Öffentliche `scene.visuals.Line`-API, VisPy 0.17.0, `method='agg'`,
`connect='strip'`, native Turntable-Szene und synchroner Renderaufruf:
XY-Punktarray erfolgreich, XYZ-Punktarray scheitert mit
`ValueError: cannot reshape array of size 6 into shape (2,2)`.
Direkter Baker-Gegentest zeigt dasselbe Ergebnis. Bestätigt ist die Grenze
dieses Standardelements für direkte XYZ-Daten, keine allgemeine Unmöglichkeit
von AGG in 3D oder eines angepassten Adapters. Aktive GL-Implementierung nicht
geändert. [Präzisierung und externer Fehlerbericht](../documentation-notes/vispy-line-benchmark.md).

## GUI1 – VisPy-Originalfarben und Auswahlumfang (21.11.2026)

Auf Nutzerhinweis `1997.d2g` geprüft: rechte 7 besitzt zwei G42-Bearbeitungen
mit T5, eine mit 0,1 mm Aufmaß. Die frühere Originalfarbe wurde aus der aktiven
Legacy-Korrektur abgeleitet und war daher dunkelmagenta. VisPy verwendet für
nicht ausgewählte aktive Originalkonturen jetzt Schwarz unabhängig von G40/41/42.
Die bestehende Statuspalette für deaktivierte Geometrie bleibt erhalten.

Auswahlumfang bestimmt die Hervorhebung: vollständige Auswahl → Original rot
mit Stiftbreite 3, alle zugehörigen Bearbeitungen dünn 0,6; Teilauswahl → Original
rot gepunktet mit Breite 1, gewählte Schnittbahn 3, andere Bearbeitungen 0,6
gestrichelt. Semantische Farben/Muster bleiben erhalten; andere gewählte Rollen
bei Teilauswahl erhalten Basisbreite +1. Der aktive Parameterkontext hebt diese
Regel nicht auf. Bei genau einer zugehörigen Bearbeitung ist deren Auswahl
vollständig. Änderung auf VisPy beschränkt; keine Planungs-/Exportänderung.

**Prüfung:** acht fokussierte Tests unter Qt6, sieben unter Qt5 und ein
Qt-Quick-Test übersprungen. Unit-Nachweis für G40/G41/G42, keine/vollständige/
teilweise Auswahl sowie Einzelfall mit einer Verknüpfung. Nativer GPU- und
Steg-/Cache-/Picking-Worker bestanden; auch die selbst erzeugte Mehrfachbearbeitung
prüft jetzt beide Ansichten und unveränderten Projektinhalt.

Die vom Nutzer bereitgestellte lokale `dxf/1997.d2g` zusätzlich mit
`--appearance-project` nativ geladen: keine/alle/eine Bearbeitung der rechten 7
in Drauf- und Raumansicht geprüft, Projekt unverändert. Drei Draufsicht-Aufnahmen
`.tox/vispy-1997-plane-{none,all,partial}.png` visuell geprüft. Projektdatei nicht
verändert oder zum Commit hinzugefügt. Keine Vollsuite oder neue Plattform-/
Paket-/Releaseabnahme; optische Nutzerprüfung am eigenen Fenster bleibt offen.

<a id="gui1-shared-xyz"></a>
## GUI1 – Gemeinsame XYZ-Werkzeugwege im VisPy-Versuch (21.11.2026)

Drauf- und Raumansicht verwenden dieselben XYZ-Segmente, dieselben vorbereiteten
Positionsarrays und dieselben räumlichen Daten für die Trefferprüfung. Die
Bildschirmkoordinaten der Trefferprüfung hängen von der aktiven Kamera ab.
Die feste XY-Kamera bietet Verschieben und Zoomen. Die Raumkamera bleibt drehbar.
Zeichenreihenfolge und Stegauflage der Draufsicht bleiben für den Versuch erhalten.

Der lokale native OpenGL-Worker hat zwei deckungsgleiche Schnitte auf Z −1,5
und −3 mm samt Zustellung geprüft. Beide Durchgänge sind im gemeinsamen
Datenbestand vorhanden, werden von oben auf denselben Bildbereich projiziert
und sind in der Raumansicht getrennt. Trefferprüfung, Auswahl und Stegeditor
sind im selben Lauf geprüft. Optische Nutzerprüfung und Performancebewertung
in der üblichen Bedienung bleiben offen. Die Start- und Aufräumarbeiten stehen
im [Übernahmeplan](../planning/gui1-renderer-comparison-plan.md#p6--auswahl-und-übernahmeplan).

Nach Rückmeldung zum Zoomen die Strichmuster der Draufsicht korrigiert. Zuvor
lief die Strichfolge über die wiederholten XYZ-Segmente weiter, sodass derselbe
XY-Abschnitt pro Tiefe an einer anderen Stelle im Muster beginnen konnte.
Für Strichmuster werden deckungsgleiche XY-Segmente je Bearbeitung und Rolle
einmal berücksichtigt. Senkrechte Bewegungen zählen dabei nicht zur sichtbaren
Länge. Die XY-Abschnitte werden pro Szene gespeichert und beim Zoomen wird
das Muster in der passenden Bildschirmgröße erzeugt. Native Prüfung mit zwei
Tiefendurchgängen bei zwei Zoomstufen gegen den einzelnen XY-Durchgang bestanden.
In der Raumansicht verwenden deckungsgleiche horizontale Abschnitte derselben
Bewegungsart denselben Musterbeginn auf ihrer jeweiligen Tiefe, auch bei
umgekehrter Fahrtrichtung. Beide Tiefen sind bei zwei Zoomstufen geprüft.

Der VisPy-Draufsichtknopf animiert aus der Raumansicht in 400 ms Winkel,
Mittelpunkt und Zoom. Ziel ist der zuletzt verwendete Draufsicht-Ausschnitt
oder die eingepasste Zeichnung beim ersten Wechsel. Danach übernimmt die feste
XY-Kamera. Der vorherige räumliche Blick wird beim Zurückschalten wiederhergestellt.
Der native Test prüft einen Zwischenzustand, die Übereinstimmung der projizierten
Punkte beim Kamerahandoff, Rückkehr und Abbruch. Der Stegmodus schaltet sofort um.

<a id="gui1-shared-drawing"></a>
## GUI1 – Gemeinsame VisPy-Zeichenregeln nach Zwischencommit (21.11.2026)

Zwischenstand `e35c20f` sichert den Stand mit getrennten Zeichenregeln.
Der neue Versuch verwendet in beiden Kameras denselben Tiefentest und dieselbe
Linienbündelung und richtet wiederholte horizontale Strichmuster gleich aus.
Der gemeinsame Bildschirmmaßstab lässt beim Kamerahandoff die Puffer bestehen.
Die Sonderreihenfolge und der Überlagerungsfilter der Draufsicht entfallen.
Regionsumrisse werden im Stegmodus von der Qt-Bearbeitungsauflage gezeichnet.

Der native OpenGL-Test prüft dieselben GL-Objekte und Upload-Signaturen für
durchgezogene und gestrichelte Linien am Übergang. Eine Überlagerungsprobe
prüft die gleiche gerenderte Farbe vor und nach dem Wechsel. Die Prüfungen
für Auswahl, Stege und mehrere Tiefendurchgänge laufen im selben Worker.

Die Nachprüfung mit `1997.d2g` zeigte eine entgegengesetzte Z-Abbildung der
beiden Kameras, obwohl der Tiefentest und die Linienpuffer bereits gemeinsam
waren. Die feste `PanZoomCamera` verwendet jetzt `up='-z'`. Damit stimmen die
Z-Reihenfolge und die Abstände der projizierten Tiefen mit der senkrechten
Raumkamera überein. Der native Test prüft zusätzlich die Render-Tiefen für
Z = 0, −1,5 und −3 mm. In derselben Überlagerungsprobe mit `1997.d2g` ging die
Anzahl deutlich blauer Pixel in der festen Draufsicht von 6.815 auf 0 zurück
und entspricht damit der senkrechten Raumansicht bei gleichem Ausschnitt.

Der Nutzer bestätigte am 21.11.2026, dass der Versuch so bleiben kann.
Gegenüber `e35c20f` entfallen im VisPy-Renderer netto 37 Zeilen
(71 entfernt, 34 ergänzt). Mit der kurzen Anpassung der Stegauflage
in `tab_modifiers.py` sind es netto 34 Zeilen Anwendungscode.

<a id="gui1-vispy-adoption"></a>

## GUI1 P6 – VisPy in die Anwendung übernommen (21.11.2026)

- Die feste Draufsicht bietet Rechtsklickmenü mit Werkstücknullpunkt,
  Rechteckauswahl der Originalkonturen und Verschieben per Umschalt+Ziehen.
  Maßstab, Pfadrichtungen sowie Pfeile und Nummern der Exportreihenfolge sind
  in beiden VisPy-Kameramodi verfügbar. Die Exportreihenfolge stammt aus
  derselben Routenberechnung wie im 2D-Canvas.
- VisPy startet in der Raumansicht. Bei fehlendem PyQt6, VisPy oder nutzbarem
  OpenGL zeigt die Anwendung den 2D-Canvas und protokolliert den Grund.
  Das alte `mode3d` wird einmalig durch `use_vispy` mit VisPy-Präferenz ersetzt.
  Eine spätere bewusste 2D-Wahl bleibt nach dem Neustart erhalten.
- Das Ribbon bündelt die Symbolbuttons von links nach rechts unter
  **Programm**, **Zeichnung**, **Bearbeitung**, **Verlauf**, **Ausgabe** und
  **Ansicht**. **Bearbeitung** vereint Schritterstellung und Stegmodus.
  **Ausgabe** vereint Exportreihenfolge, Optimierung und Export. **Ansicht**
  vereint Kamerawahl und Darstellungsoptionen.
  Die Gruppenüberschriften stehen unten. **Öffnen**, **Erstellen …** und
  **G-Code exportieren** erscheinen als große beschriftete Buttons neben
  den zweizeilig angeordneten Nebenaktionen.
  Unter Windows mit Qt ab 6.9 und unterstützter erweiterter Titelleiste liegen
  Rückgängig und Wiederholen zwischen App-Symbol und Dateititel. Bei fehlender
  Unterstützung bleiben beide unter **Verlauf** im Ribbon. Normales und
  maximiertes Fenster sowie die 2D-Ausweichdarstellung sind lokal geprüft.
  Das native QWindow unterdrückt den zweiten Fenstertitel und erhält die
  Fensterbuttons. Nach dem Laden fordert DXF2GCODE einmal die Aktivierung des
  Hauptfensters an. Der normale Windows-Launcher mit `1997.DXF` bestätigte
  die Qt-Aktivierung und die Titelleisten-Flags. Die Win32-Abfrage des
  Vordergrundfensters war auf dem isolierten Testdesktop nicht verfügbar.
  **Programm**, **Zeichnung** und **Ausgabe** ergänzen die vorhandenen Menüaktionen
  zum Öffnen, Neuladen, Speichern unter, Beenden, Nullpunktsetzen, Skalieren,
  Drehen, Spiegeln, Optimieren und Exportieren. Die klassischen Menüs
  **Datei**, **Exportieren** und **Ansicht** wurden nach dem Abgleich entfernt.
  **Programm** enthält auch das vollständige Optionenmenü als Zahnrad-Dropdown.
  **Info** steht am rechten Rand und öffnet **Über DXF2GCODE** direkt.
  Die klassische Menüzeile entfällt vollständig.
  Die zugehörigen Tastenkürzel sind weiterhin am Hauptfenster registriert.
  Die Gruppen sind links
  gebündelt. Der Stegmodus mit Platzierungswahl und der Bearbeitungsverlauf
  verwenden dieselben Aktionen wie bisher in der Seitenleiste.
  VisPy bietet den animierten Wechsel zur Draufsicht und den Schalter für
  transparente Werkzeugzylinder.
- VisPy projiziert für die Pfadrichtungsanzeige nur Markierungen und die ersten
  beziehungsweise letzten in der Ansicht sichtbaren Bewegungssegmente, mit
  einer Kameratransformation pro Auflage. Auf `1997.d2g` mit sieben
  Bearbeitungen sank die Zahl der Projektionen einer Auflage von 5.074 auf 42.
  Median über zehn Drehwinkel auf dem lokalen Windows-Stand: 598,1 ms allein
  für die bisherige Segmentprojektion, 5,5 ms für die neue Auflage mit
  Bildabgriff. Der Schalter aktualisiert in VisPy nur die Auflage.
- Der Qt-Quick-3D-Adapter, die QML-Szene, der ältere OpenGL-Canvas und dessen
  separater Stegdialog sind entfernt. Die Windows-Paketierung verwendet
  PyQt6 und VisPy. Für das Python-Paket steht `view-vispy` zur Verfügung.
  DE, FR und RU sind aktualisiert und kompiliert.

**Lokal geprüft:** native Windows-/PyQt6-Worker für Standardstart,
Kamerawechsel, Rechteckauswahl, Kontextmenüposition, Maßstab, Exportreihenfolge,
Werkzeugkörper und Stegbearbeitung. Fokussierte Tests für Profilmigration,
2D-Rückfall, Übersetzungen und Exportreihenfolge sowie die Hauptfenster-Abläufe
unter PyQt5 und PyQt6. Der Paketumbau ist eingerichtet. Eine Abnahme von
Windows-ZIP/MSI und von weiteren Plattformen steht separat aus.

<a id="gui1-p5-vispy"></a>
## GUI1 P5 – VisPy-Stegbearbeitung (15.11.2026)

Nach dem Vergleich vorläufig VisPy bevorzugt und den Bearbeitungsnachweis
beauftragt; Qt Quick 3D bleibt erhalten. Die feste VisPy-Draufsicht nutzt nun
die vorhandenen `TabModifiers`: Projektion und inverse XY-Abbildung im Adapter,
Qt-Auflage für Regionen, Griffe und Maßfelder, native Qt-Ereignisse für Auswahl,
Verschieben, Zeichnen, Strg-Fang und Doppelklick. Die VisPy-Kamera erhält keine
vom Stegeditor verbrauchten Mausereignisse. NumPy-Koordinaten werden vor einer
Projektänderung in Python-`float` umgewandelt.

Projektbefehle, Undo/Redo, Zuordnung und automatische/manuelle Bemessung werden
vom bisherigen Canvas wiederverwendet. Bestätigte Maßeingabe behält den
Mittelpunkt bei und wechselt zur manuellen Bemessung; beim Ziehen werden keine
Maßfelder dargestellt. Aus der räumlichen VisPy-Ansicht schaltet der Stegmodus
zur Draufsicht; ein Wechsel zur räumlichen Ansicht beendet den Modus.

**Lokale Prüfung:** sechs Renderer-Vertragstests unter PyQt6 bestanden.
`--vispy-editing-worker` bestand im nativen Windows-/OpenGL-Fenster: inverse
Projektion bei gezoomter Ansicht, Auswahl, Verschieben mit einem Undo-Eintrag,
Undo/Redo einschließlich Projektvergleich, Maßfeld über der nativen Ansicht,
Mittelpunkt und automatisch/manuell, Strg-Aufruf des gemeinsamen Fangs,
Zeichnen bei weiterhin aktivem Modus und Doppelklick. Die erzeugte Aufnahme
`.tox/vispy-tab-editing.png` zeigt ausgerichtete Region, Griffe und beide Maße;
visuell geprüft. Je zwei Bearbeitungs-/Übersetzungstests unter PyQt5 und PyQt6
bestanden, einschließlich der bestehenden Canvas-Ereignistests.

Offen bleibt die Nutzerprüfung bei unterschiedlichen Zoomstufen im Vergleich
zum bisherigen Canvas. Keine neue Debian-, Paket-, Vollsuite- oder Releaseabnahme;
der zuvor bereitgestellte Debian-Teststand enthält diese Ergänzung noch nicht.
Keine vollständige Übernahme aller Canvas-Aktionen oder endgültige Rendererwahl.

**Korrektur nach Nutzerprüfung (15.11.2026):** Der Editor zeigte zuvor den
vollständigen Float-Wert, etwa `3.999999999…`; im schmalen Feld war nur das Ende
sichtbar. Er verwendet jetzt die konfigurierte Anzeigepräzision. Unverändertes
Bestätigen erhält den ungerundeten Wert, den automatischen Bemessungsmodus und
den Undo-Stand. Eigene Eingaben behalten ihre Eingabegenauigkeit. Der native
VisPy-Worker besteht mit gezielt erzeugter Float-Abweichung, formatiertem
Editorwert und unverändertem Projekt nach Enter; anschließendes Ändern und
Undo funktionieren weiterhin. Die je zwei bestehenden Bearbeitungs- und
Übersetzungstests bestanden unter Qt5 und Qt6; der Canvas-Test prüft nun
ebenfalls unverändertes Bestätigen und weiterhin präzise eigene Eingaben.

**Korrektur der VisPy-Draufsicht (15.11.2026):** Linientiefentest dort deaktiviert
und Zeichenreihenfolge nach Originalgeometrie, nicht ausgewählter und ausgewählter
Bearbeitung festgelegt. Die Batch-Schlüssel enthalten die Zeichenebene; gleiche
Farben/Breiten aus unterschiedlichen Ebenen werden nicht mehr zusammengefasst.
Auch wiederverwendete Linienobjekte erhalten beim Ansichtswechsel den passenden
Tiefentest. Räumliche Darstellung, bestehende Farben und Projekt-/Planungsdaten
bleiben erhalten. Der native Stegbearbeitungs-Worker bestand einschließlich
Framebuffer-Gegenprobe mit drei exakt deckungsgleichen Pfaden, Auswahlwechsel
und Draufsicht–Raumansicht–Draufsicht. Sechs Renderer-Vertragstests bestanden.
Nutzerprüfung des zuvor gezeigten Beispiels bleibt offen; keine neue
Plattform- oder Paketabnahme.

**Nachkorrektur nach Bildprüfung (15.11.2026):** Unverbundene GL-Einzelsegmente
ließen Ecken offen; nicht ausgewählte Bearbeitungen lagen weiterhin über der
Originalkontur. Durchgezogene Linien der VisPy-Draufsicht verwenden jetzt
verbundene AGG-Pfade mit Eckverbindungen, Endkappen und Kantenglättung.
Räumliche Linien und gestrichelte Pfade behalten ihre bisherige Methode.
Getrennte Stücke, Nullsegmente und Lücken werden nicht künstlich verbunden.
Die korrigierte Reihenfolge ist: nicht ausgewählte Bearbeitungen,
Originalgeometrie, ausgewählte Bearbeitungen. Der kosmetische Qt-Stift mit
Breite 0 wird als ein Pixel dargestellt.

Sieben fokussierte Renderer-Tests und der native Stegbearbeitungs-Worker
bestanden. Die erweiterte Framebuffer-Gegenprobe zeigt ein ausgewähltes Rechteck
mit geschlossenen Ecken und einen nicht ausgewählten schwarzen Kreis ohne
ausgeprägt blaue Pixel trotz deckungsgleicher Bearbeitung. Aufnahme
`.tox/vispy-line-joins.png` visuell geprüft; Auswahl- und Ansichtswechsel sowie
Stegbearbeitung bleiben im nativen Nachweis enthalten. Keine neue Plattform-,
Paket- oder Performanceabnahme; Nutzerprüfung des eigenen Beispiels bleibt offen.

**Strichstärke nach Nutzerprüfung (15.11.2026):** Die AGG-Hervorhebung in der
Draufsicht reduziert: normale Konturen weiterhin 1 Pixel, ausgewählte
durchgezogene Linien 1,5 statt 2 Pixel, aktive 2 statt 3 Pixel. Farben,
Eckverbindungen, gestrichelte und räumliche Linien bleiben erhalten.
Sieben Renderer-Tests und der native Stegbearbeitungs-/Framebuffer-Worker
bestanden; Sollbreiten im Worker geprüft, aktualisierte Aufnahme
`.tox/vispy-line-joins.png` visuell geprüft. Keine Behauptung einer pixelgenauen
Übereinstimmung unterschiedlicher Renderer; optische Nutzerabnahme bleibt offen.

## GUI1 P4 – isolierter Debian-Vergleich vorbereitet und technisch geprüft

Stand: **15.11.2026**, ausdrücklicher neuer Nutzerauftrag nach Rückmeldung:
„Beide laufen aktuell relativ flüssig“, Vergleich zusätzlich auf Debian gewünscht.
Keine daraus abgeleitete allgemeine Freigabe für spätere Debian-/Vollsuitenläufe.

- Debian-Test-VM: **Debian 13.7, Python 3.13.5, X11/Xfce**, eigene venv mit
  **PyQt6/Qt 6.12.0, VisPy 0.17.0, NumPy 2.5.4, PyOpenGL 3.1.10**.
- Uncommittierten Arbeitsstand als getrennten Snapshot übertragen, SHA256
  `a311d08854a71100c076e89703328adfd66943489bed3ab84c9696041c255f04`
  auf dem Ziel verifiziert. Archiv enthält den Quellstand mit generierten
  Qt-/Sprachressourcen, Vergleichsworker und zwei DXF-Beispielen, kein Releasepaket.
- Testbasis `~/dxf2gcode-test-work/runs/view-comparison-20261115/`, eigene
  HOME-/XDG-Verzeichnisse und Starter `start-view-comparison.sh`; zusätzlicher
  Desktop-Starter „DXF2GCODE Ansichtsvergleich“. Bestehende Anwendungseinstellungen
  und Installation unverändert. Fehlende XCB-Cursor-Bibliothek aus Debian-Quellen
  lokal entpackt und nur im Starter über `LD_LIBRARY_PATH` eingebunden.
- Echte vorhandene X11-Sitzung verwendet, kein Xvfb. Native Worker
  `--quick-worker` und `--gpu-worker` beide Status 0: Bildausgabe, Qt-Projektion,
  Auswahl, Kameras, Tiefenänderung, Snapshot-/Projektinvarianz, transparente
  Körper, Rückkehr zum bisherigen Canvas und beide Aktivierungsreihenfolgen.
  Qt Quick: **OpenGL**; VisPy: **OpenGL 4.5 Compatibility Profile**.
- Virtuelles Grafikgerät Virtio, tatsächlicher Renderer **llvmpipe / LLVM 19.1.7,
  Mesa 25.0.7**, `Accelerated: no`. Dies ist Software-Rendering auf der CPU,
  kein Nachweis beschleunigter Linux-Grafik oder deren Leistungsfähigkeit.
- Prüfprotokolle und Bilder auf der VM gespeichert; lokal `.tox/quick-smoke.log`,
  `.tox/vispy-smoke.log` sowie `.tox/debian-*-transparent-tools.png` gesichert.
  Beide Debian-Bilder visuell kontrolliert. Anwendung anschließend mit der
  Steg-Beispieldatei in der Benutzersitzung geöffnet; laufender Prozess und
  sichtbarer X11-Fenstertitel mit `BreakExample_Circle.dxf` bestätigt.

**Grenzen:** Manuelle Debian-Nutzerprüfung noch offen. Keine Vollsuite, keine
Debian-Paket-/Releaseabnahme, kein Performance-Benchmark oder Hardware-GPU-Test.
Die Anwendung bleibt für den Nutzer geöffnet. Kein Commit/Push oder Merge.

## GUI1 P4 – begrenzte CPU-Gegenprobe mit VisPy

Stand: **15.11.2026**, auf Nutzerfrage nach vergleichbaren VisPy-Messwerten.
Keine Änderung der Renderer; Mess-Worker für beide Kandidaten verwendbar gemacht.
`--vispy-benchmark` und `--quick-benchmark` liefen nacheinander auf derselben
lokalen Windows-/PyQt-6.12-Umgebung mit `BreakExample_Circle.dxf` und zusätzlicher
Bearbeitung derselben Originalkontur. Je Aktion zwölf Aktualisierungen,
ausgewählte Operationen, sichtbare räumliche Ansicht, gleiche Fensterumgebung.

Neben `redraw()` wird die gesamte synchrone CPU-Aktualisierung **einschließlich
Kamerazuweisung** erfasst: VisPy führt bereits im Kamera-Setter Arbeit aus,
während Qt Quick zunächst nur seinen Kamerazustand ändert.

| Aktion | VisPy CPU ms inkl. Kamera | Qt Quick 3D CPU ms inkl. Kamera |
| --- | ---: | ---: |
| Verschieben | 6,331 | 0,049 |
| Drehen | 6,133 | 21,061 |
| Zoomen | 7,118 | 25,710 |

Im selben Durchlauf reine `redraw()`-Mediane: VisPy 5,425 / 5,040 / 5,821 ms;
Qt Quick 0,047 / 21,058 / 25,708 ms. Vorangegangene kurze Läufe schwankten
(VisPy ca. 7 ms; Qt Quick Rotation ca. 13–14 ms, Zoom ca. 19–22 ms).
Diese kleinen Stichproben sind keine allgemeine Geschwindigkeitsrangliste.

VisPy setzt je Aktualisierung Daten von 13 Liniengruppen neu (156 `set_data`-
Aufrufe über zwölf Aktualisierungen); Qt Quick aktualisiert beim Verschieben
keine Geometrie, beim Drehen/Zoomen je einmal seine gemeinsame Bandgeometrie.
Das sind API-Aufrufe, keine gemessenen physischen GPU-Übertragungen oder Bytes.
Qt Quick erzeugt dafür Dreiecke für Bildschirmbreiten, VisPy nutzt native Linien;
Darstellungsqualität und Arbeitsumfang sind damit nicht pixelgenau gleichgesetzt.

Beide nativen Worker einschließlich Bild-/Auswahl-/Projektprüfungen bestanden.
Kein Warten auf GPU-Abschluss pro Messprobe, keine FPS-/Latenzmessung, keine
großen Projekte, weiteren Plattformen oder Releasebuilds geprüft. Die vollständige
vergleichende Bewertung und Rendererentscheidung bleiben [P4](../planning/gui1-renderer-comparison-plan.md).

## GUI1 P4 – zuschaltbare transparente Werkzeugkörper in beiden Prototypen

Stand: **15.11.2026**, lokal auf `ribbon-2d-3d`, vom Nutzer als Darstellungstest
beauftragt. Gemeinsamer Schalter **„Transparente Werkzeuge (Test)“**, anfangs aus.
Je ausgewählter aktivierter Bearbeitung mit gültigem Plan ein Zylinder am
Startpunkt; Radius aus dem Plan, Testlänge vier Durchmesser, Deckkraft 25 %.
Keine Projekt-/Exportänderung, Werkzeuganimation oder Kollisionsprüfung.

- Qt-freie gemeinsame Körperbeschreibung und Zylindernetz mit 48 Seiten,
  194 Vertices und 192 Dreiecken. Beide Renderer verwenden diese Tessellierung;
  Qt Quick nutzt explizite Normalen, VisPy seine Mesh-Normalen und Beleuchtung.
- VisPy: transparente Mesh-Objekte mit Transformationen und Alpha-Blending.
  Tiefenschreibmaske nach dem Zeichnen wiederherstellen: andernfalls unterblieb
  das Leeren des Tiefenpuffers im Folgeframe und Konturen verschwanden.
  Neue Snapshot-Daten entfernen veraltete Körperobjekte.
- Qt Quick: gemeinsames statisches `QQuick3DGeometry` mit Positionen/Normalen/
  Indizes; Modelle über `Repeater3D`, ohne Tiefenschreiben und ohne Picking.
  Kameraänderungen erzeugen die Zylindergeometrie nicht erneut.
- Auswahl, Parameteränderungen und Ansicht synchronisieren die Körper;
  Einpassen berücksichtigt deren Grenzen. Schalter-/Tooltiptexte DE/FR/RU
  übersetzt, QM-Dateien kompiliert und neue Einträge geladen/geprüft.

**Prüfung:** sechs fokussierte Tests unter PyQt6 bestanden; unter PyQt5 fünf
bestanden und ein Qt-Quick-Test übersprungen. Gemeinsamer Körperfilter,
Abmessungen und Mesh-Zahlen geprüft. Native Windows-Worker für Qt Quick/D3D11
und VisPy/OpenGL mit zwei Körpern bestanden, einschließlich unverändertem
Snapshot/Projekt, Ein-/Ausschalten und weiterhin sichtbaren Konturen im VisPy-
Folgeframe. Beide Bilder `.tox/quick3d-transparent-tools.png` und
`.tox/vispy-transparent-tools.png` visuell geprüft; gemeinsamer Rendererwechsel
abschließend nativ geprüft.

**Kurze Render-Gegenprobe:** Median aus sechs Rotationen nach je einer
Aufwärmprobe, einschließlich Render/Readback, zwei Körper, gleicher lokaler
Windows-/PyQt6-Stand und Beispiel wie zuvor. Qt Quick ca. 39,4 ms aus / 59,6 ms
ein (2846×1108 Pixel); VisPy ca. 37,2 ms aus / 29,9 ms ein (2846×1107 Pixel).
Dass VisPy hier mit zusätzlichen Körpern schneller gemessen wurde, zeigt die
Streuung/Anlauf- und Synchronisierungseinflüsse dieser kleinen Probe; daraus
keinen Vorteil durch Transparenz ableiten. Die Readback-APIs und Auflagen sind
verschieden. Dies ist keine FPS-Messung oder belastbare Bibliotheksrangliste.

Keine Vollsuite, Plattform-/Paket-/Releaseabnahme. Nutzerprüfung mit größerer
Auswahl und überlagerten transparenten Körpern bleibt Teil von
[P4](../planning/gui1-renderer-comparison-plan.md).
