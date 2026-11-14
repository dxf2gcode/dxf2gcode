# Abschluss von maschining-project und nächster Develop-Release

Stand: **14.11.2026**. Schritte 1–3 abgeschlossen: Integrationsbasis, IGNORE,
Anleitung/Bilder und Kandidaten-Paketabnahme. PR #5 ist gepusht und geprüft;
noch kein Merge nach `develop` oder Release. Nutzersichtprüfung folgt am Schluss.

## 1. Bestätigte Entscheidungen

- R3/R1b einschließlich P8 ist vom Nutzer fachlich abgenommen.
- Der aktuelle Stegumfang ist ausreichend. Eine zusätzliche selbsttätige
  Verteilung von Stegen wird nicht weiter geplant; Fang, Größenautomatik und
  manuelle Regionen bleiben wie abgenommen.
- Historische Fremdinhalte werden nicht übernommen; die Rechteklärung entfällt.
- Teilkonturen bleiben offen. Weitere optionale Funktionen gehören nicht zu
  diesem Integrationsabschluss.
- Vor dem nächsten Entwicklungsschritt soll der Featurestand nach `develop`
  integriert und ein weiterer Develop-Prerelease veröffentlicht werden.
- Anleitung, Bilder und Releasebeschreibung müssen zum integrierten Stand passen.

Die bestätigten Abschlüsse werden in der Todo entfernt und im
[Abschlussnachweis](../archive/toolpath-refactoring-completed.md) festgehalten.
Paket-/Installationsnachweise werden dadurch nicht vorweggenommen.

## 2. Ausgangslage und Integrationsweg

Lokaler Stand bei der Planung: `maschining-project` endet auf `69f9767` und enthält
einen noch nicht gepushten Commit. `develop` enthält mit `8aeef7f` einen eigenen
Fix für kompatible Fehlerdialog-Symbole, der im Featurezweig fehlt. Remote-Stände
vor tatsächlicher Integration aktualisieren; die lokalen Trackingangaben sind
keine Live-Aussage über GitHub.

Empfehlung: isolierte Integrationsarbeitskopie auf Basis von `develop`, den
Featurezweig dort zusammenführen und Ergänzungen als getrennte Commits erstellen.
So bleibt der derzeitige Develop-Stand bis zur geprüften Zusammenführung erhalten.
Den Symbolfix bewahren; Konflikte fachlich auflösen und keine Seite pauschal
überschreiben. Sobald Code und Dokumentation fertig sind, PR nach `develop`
bereitstellen; dessen CI liefert die Kandidatenartefakte für Etappe C.
Den Featurezweig bis zur erfolgreichen Veröffentlichung erhalten.

<a id="ignore"></a>

## 3. Etappe A – IGNORE begrenzt korrigieren

**Aktuelle Nutzerpräzisierung vom 14.11.2026; ersetzt die erste Sonderfall-Korrektur:**

- `Ignoriert` nicht mehr als frei anlegbare Art normaler Bearbeitungsschritte
  anbieten. Normales vorübergehendes Ausschließen bleibt die Exportcheckbox.
- `IGNORE:`-Konturen beim Import als nicht zugeordnete Originalgeometrie laden.
  Spätere normale Zuordnung muss möglich sein und Export/Parameter aktivieren.
- Keine Altprojekt-Sonderbehandlung für interne `ignored`-Schritte: Der Nutzer
  bestätigt, dass solche Altprojekte nicht benötigt werden. Den internen Typ
  samt Sperren/Ausnahmen entfernen; allgemeine alte Projektformate bleiben erhalten.
- DE/FR/RU samt QM aktualisieren. Import, Zuordnung/Undo, Projekt-Roundtrip und
  Exportfreigabe fokussiert prüfen; beim nächsten Quellcodecommit Fast-Hook.

**Ergebnis:** kleiner Funktionscommit, ohne Änderung der eigentlichen
Werkzeugwegplanung. Kein größeres Refactoring als Teil dieses Zwischenreleases.

**Umgesetzt:** isolierter Zweig `integration/maschining-project-release`, Basis
`develop` samt Fehlerdialog-Fix `8aeef7f`, Feature einschließlich Planungscommit
`3e05281` mit Mergecommit `f696631` integriert. Konflikt im Abschlussarchiv unter
Erhalt beider Nachweise gelöst; Programmcode automatisch zusammengeführt.
Neue Schritt-/Zuordnungsdialoge bieten nur normale Bearbeitungsarten an.
Die erste IGNORE-Fassung in `2ccebe5` ist durch die anschließende Nutzerpräzisierung
ersetzt: IGNORE-Geometrie wird unzugeordnet importiert und ist normal zuweisbar;
interne Sonderart/Kompatibilitätscode sind entfernt. Die Vergleichs-DXF unter
`docs/assets/examples/ignored-layers/` dient der eigenen Nutzerprüfung.
Je 71 fokussierte Qt5-/Qt6-Prüfungen bestanden; Details im Abschlussarchiv.
Diese nachträgliche Präzisierung ist noch nicht committed oder gepusht.
IGNORE ist vom Nutzer nach eigener Prüfung ausdrücklich abgenommen. DOC1
ist redaktionell umgesetzt; die Sichtprüfung übernimmt der Nutzer am Schluss.

<a id="doc1"></a>

## 4. Etappe B – DOC1 und Bilder zum aktuellen Produktstand

Die gesamte veröffentlichte Anleitung auf betroffene Bedienwege prüfen, nicht
nur das neue Bearbeitungskapitel. Fachlich stabile, unbetroffene Grundlagen
beibehalten. Abgleich insbesondere für:

- DXF-Import, Geometrie-/Bearbeitungstab, Werkzeugtabelle/Projektabweichungen;
- Schritt- und Konturwerte, Herkunftssymbole, Mehrfachauswahl und Werkzeugwechsel;
- Verschieben/Kopieren, Reihenfolge, Undo/Redo und Exportaktivierung;
- Stegmodus: Zielauswahl, Aufziehen, Fang/Manuell, Erstklick/Ziehen, Doppelklick,
  Maße nur bei ruhender Auswahl und automatische Größenfolge bei Werkzeugwechsel;
- .d2g 2.1, unterstützte Altformate, Exportdiagnosen und Installationsanleitung.

Veraltete Beschreibungen entfernen, etwa Erstellung eines Stegs per bloßem
Konturklick, verpflichtender Erstellungsdialog oder Live-Maße während des Ziehens.

**Bilder:** echte Aufnahmen des integrierten Programms mit reproduzierbaren
Beispielzeichnungen und einem konsistenten Profil. Sprache, Einheiten und Werte
an das jeweilige Kapitel anpassen. Geplanter Satz:

1. Geometrieansicht mit Entities, Layers und Stegregionen.
2. Bearbeitungsbaum mit Mehrfachbearbeitung und aktuellen Parametergruppen.
3. Gemeinsamer Zuordnungsdialog mit vorhandenem/neuem Ziel.
4. Stegmodus samt Fang/Manuell und ausgewählter Region mit Kantenmaßen.
5. Ziehzustand ohne Maßfelder und Doppelklick-Dialog einer Region.
6. Relevante Konfigurations-/Werkzeugansichten, wo bisherige Bilder veraltet sind.

Vorhandene Screenshots in allen Kapiteln inventarisieren und bei veralteter
Oberfläche ersetzen. Bilder samt erläuternden Texten im Repository ablegen;
Navigation, Links, Bildunterschriften und Release-Highlights aktualisieren.
Die spätere Pages-Vorschau muss denselben integrierten Stand zeigen.

**Prüfung:** strenger Dokumentationsbuild, Link-/Bildprüfung und Sichtprüfung
der betroffenen Seiten. Keine neue pauschale P8-Funktionsabnahme verlangen.
Konkrete redaktionelle Restfragen einzeln vorlegen. DOC1 nach diesen Ergebnissen
abschließen; keine dauerhafte Sammelaufgabe für hypothetische Rückmeldungen.

<a id="installation"></a>

**Stand Schritt 2:** betroffene Kapitel, Releasebeschreibung und Bilder sind
aktualisiert; 16 echte Qt6-Aufnahmen aus isoliertem englischem Demoprofil.
Strenger Zensical-Build bestanden, Tutorial-Dateiexport geprüft. Die Browser-
Sichtprüfung konnte nicht durchgeführt werden; der Nutzer übernimmt sie auf
eigenen Wunsch am Schluss und beauftragt ausdrücklich Schritt 3. Keine
behauptete Sichtabnahme oder Veröffentlichung.

## 5. Etappe C – Installationsnachweis am Releasekandidaten

**Vom Nutzer bestätigter Umfang: Windows, Ubuntu und Debian; macOS separat.**

Code-/Dokumentationsstand als PR nach `develop` bereitstellen und die vorhandene
CI laufen lassen. Deren Kandidatenartefakte und Herkunft für die folgenden
Prüfungen verwenden. Der vorhandene wegwerfbare Windows-Runner kann die
ZIP-/MSI-Abnahme abdecken; keine identische zweite Installation nur zur Wiederholung.

| Ziel | Prüfung | Nachweisgrenze |
| --- | --- | --- |
| Windows x64 | ZIP entpacken/starten und MSI in einer wegwerfbaren Windows-Umgebung installieren, starten und entfernen | Keine Installation über die aktive Arbeitsumgebung; Umgebung/Artefakt festhalten |
| Ubuntu / Qt5 und Qt6 | Frische Wheel-Umgebungen und Paketprüfungen des vorhandenen GitHub-Workflows verwenden | CLI und Offscreen-GUI sind kein Nachweis eines realen Desktop-/GPU-Aufbaus |
| Debian | Konkretes Kandidaten-Wheel in isolierter Umgebung des vorhandenen Debian-Systems installieren und starten | Frische Python-Umgebung auf vorhandenem System, kein behaupteter neuer OS-Aufbau |
| macOS | Separat zurückstellen, solange keine konkrete geprüfte Zielumgebung verfügbar ist | Keine macOS-Freigabe ableiten |

Kurzer gemeinsamer Ablauf: Paketversion/Commit prüfen, Beispiel-DXF öffnen,
Werkzeug/Bearbeitung und Steg bedienen, Projekt speichern/wiederladen und G-Code
exportieren. Quellarchiv, Wheel und Windows-Artefakte müssen dieselbe Herkunft
tragen; vorhandene Paketprüfungen wiederverwenden. Keine realen Maschinenbewegungen.
Die fachlich bereits akzeptierte P8-Abnahme wird nicht vollständig wiederholt.

Zuerst PR-Kandidatenartefakte prüfen. Nach Veröffentlichung die endgültigen
Download-Artefakte gegen Herkunft/Hashes abgleichen und deren Start bestätigen;
ein anderer Build ist nicht allein durch Tests des Kandidaten abgenommen.
M1 nur im tatsächlich nachgewiesenen Umfang abschließen. Ungeprüfte Plattformen
als konkrete Restpunkte erhalten, statt die gesamte Installationsaufgabe offen
oder unbelegt als erledigt zu lassen.

**Schritt 3 abgeschlossen:** PR #5, Head `a4849c8`, getesteter PR-Merge
`88aec3d`, CI `43606276059` vollständig erfolgreich. Vier Vollsuiten mit je
1040 Tests, frische Ubuntu Qt5/Qt6-Wheels, Windows-ZIP/MSI auf wegwerfbarem
Runner und exaktes Kandidaten-Wheel auf Debian einschließlich X11/Xvfb geprüft.
Kandidatenversion `2.0.0.dev22`, keine Veröffentlichung. Herkunft/Prüfsummen und
Abnahmegrenzen im [Nachweis](../archive/toolpath-refactoring-completed.md#pr5-installation).
Endgültige Release-Artefakte bleiben Etappe D; macOS separat.

## 6. Etappe D – Merge und Develop-Veröffentlichung

1. Sauberen, unveränderten Integrationsstand und nachvollziehbare Commits im PR
   bereithalten; seine Kandidatenprüfung wurde in Etappe C durchgeführt.
2. Prüfen, dass CI-Ergebnisse und Installationsnachweise genau diesem Stand
   entsprechen. Keine zusätzliche lokale Vollsuite allein zur Wiederholung starten.
3. Nach erfolgreichen Prüfungen nach `develop` zusammenführen und pushen.
   Den normalen Develop-Prüflauf und die Development-Dokumentationsvorschau prüfen.
4. `doc/release-notes/2.0.0.md` enthält vorher die aktuellen Feature-Highlights,
   Formatkompatibilität und Bedienänderungen. Keine alte Oberfläche in Releasebildern.
5. Den separaten Workflow `publish-release.yml` auf `develop` starten. Er prüft
   und baut gemäß bestehender Pipeline erneut und veröffentlicht erst bei Erfolg.
   Die nächste `2.0.0.devN`-Nummer ermittelt die Pipeline; keine Nummer vorwegnehmen.
6. Release-Downloads, Manifest, Prüfsummen, Anleitung und Bilder abgleichen;
   endgültige Artefakte gemäß Etappe C bestätigen und Ergebnis dokumentieren.

Dies ist ein **Develop-Prerelease**, kein stabiler `v2.0.0`-Tag. Der bestehende
[Releasevertrag](../release-pipeline.md) und die stabile Freigabegrenze bleiben
erhalten. Ein echter PR-Paketlauf kann den entsprechenden Teil von CI1 schließen;
erster stabiler Release und spätere Codesignierung bleiben getrennt.

## 7. Empfohlene Aufteilung und noch benötigte Entscheidungen

Nicht alles in einem großen Änderungsblock: zuerst IGNORE entscheiden und ggf.
korrigieren, dann Anleitung/Bilder, danach Kandidaten-/Installationsprüfung und
zuletzt Merge/Veröffentlichung. Funktionskorrekturen bei der Abnahme als konkrete
kleine Folgeänderungen behandeln; keine neuen Features vor diesem Zwischenrelease.

IGNORE-Korrektur ist umgesetzt; Matrix Windows/Ubuntu/Debian ist ausdrücklich bestätigt.
DOC1 wird als Abgleich der Anleitung samt echten Bildern und Sicht-/Buildprüfung
vorgeschlagen. Die Etappen nacheinander ausführen, statt einen großen Quellcode-,
Dokumentations- und Releaseblock zu vermischen. Der Planungsauftrag hat noch
keine Paket-/Installationsprüfung, SSH-Abnahme oder Veröffentlichung gestartet.
Nach dem anschließenden Auftrag für Schritt 1 ist die begrenzte IGNORE-Korrektur
auf der isolierten Integrationsbasis umgesetzt und vom Nutzer abgenommen.
Schritt 2 ist redaktionell abgeschlossen; die Sichtprüfung bleibt beim Nutzer.
Schritt 3 ist nun ausdrücklich beauftragt: Kandidaten-PR, Windows-/Ubuntu-CI und
Debian-Wheel-Abnahme. Merge nach develop und Veröffentlichung bleiben Etappe D.
