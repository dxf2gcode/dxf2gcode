# Offene Aufgaben – Details

Stand: **15.11.2026**. Nur die noch offenen Themen der
[Kurzliste](../todo.md). Status und Priorität werden dort geführt; diese Datei
beschreibt denselben Umfang genauer. Abgeschlossene Funktionen, Abnahmen und
frühere Umsetzungsetappen stehen nicht mehr in beiden Aufgabenlisten.
Kein Eintrag erteilt von sich aus einen Implementierungs-, Build- oder Testauftrag.

## Verbleibende Abnahmen

<a id="ci1"></a>

### CI1 – Erster stabiler Release und Codesignierung

- [ ] Den ersten ausdrücklich freigegebenen stabilen Tag `v2.0.0` einschließlich
  dauerhafter Downloads und „Latest“ tatsächlich nachvollziehen. Freigabe erst
  nach der vereinbarten Todo-Regel; keinen Stable-Tag nur zu Prüfzwecken setzen.
- [ ] Windows-Codesignierung nach Bereitstellung eines Zertifikats gesondert
  umsetzen; EXE/DLL und MSI sowie Signaturprüfung im Releaseablauf berücksichtigen.

Versions-, Herkunfts- und Veröffentlichungsvertrag:
[Release-Pipeline](../release-pipeline.md).

## Zurückgestellte oder optionale Erweiterungen

<a id="teilkonturen"></a>

### Teilkonturen – getrennte Ergebnisse einer Operation

Zurückgestellt; auf dem integrierten Bearbeitungsmodell aufbauen. Gemeint sind
getrennte resultierende Konturen/Inseln derselben Operation, keine Tiefenpässe.

- [ ] Lead-in, Lead-out und Overcut je resultierender Teilkontur unabhängig planen.
- [ ] Startpunkte je Teilkontur in der GUI auswählen und festlegen können.
- [ ] Identitäten und Zuordnung der Einstellungen bei Neuberechnung sowie
  Projekt-Speichern/Laden stabil erhalten; Speicherverfahren vorher ausarbeiten.
- [ ] Vorschau und Export aus denselben Teilkonturen ableiten; Tiefenpässe und
  Verbindungsbewegungen dürfen deren Zuordnungen nicht vermischen.

Originalgeometrie, Operation, resultierende Teilkontur und Tiefenpass bleiben
unterscheidbar. Modell und Bedienung werden erst beim Aufgreifen entschieden.

<a id="pp1"></a>

### PP1 – Separater Drehzahlblock

- [ ] Auslösebedingungen und Postprozessorvertrag für geänderte Drehzahl bei
  gleicher Werkzeugnummer abstimmen, einschließlich Maschinenarten und Altprofilen.
- [ ] Einen eigenen konfigurierbaren Block vorsehen, statt dafür den normalen
  Werkzeugwechselblock einschließlich T/M6 erneut auszugeben.

Der bisherige Werkzeugwechsel bleibt an eine andere Nummer gebunden
([Entscheidung D21](../archive/planning/r3-r1b-implementation-plan.md)).
Noch kein Implementierungsauftrag.

<a id="q1"></a>

### Q1 – Zusätzliche Qt-Bindung PySide6

Optional und zurückgestellt. PyQt5/PyQt6 beibehalten; vorhandene generierte
PySide-Dateien sind kein Nachweis einer unterstützten Anwendung.

- [ ] Explizite Bindungsauswahl ergänzen und Qt-Version von der Python-Bindung trennen.
- [ ] Signale, Slots, Properties, Varianten und Shape-Referenzen zentral kapseln;
  innerhalb eines Prozesses nur eine Bindung verwenden.
- [ ] UI-/Ressourcenerzeugung, Übersetzungswerkzeuge und optionale Paketabhängigkeiten
  erweitern; die passenden generierten Module laden.
- [ ] Hauptfenster, Baum/Drag-and-drop, Auswahl, Vorschau, Übersetzungen und Export
  gezielt prüfen; 3D/OpenGL sowie längere Paketläufe gesondert vereinbaren.

Bedarf und dauerhaften zusätzlichen Prüfaufwand vor Umsetzung entscheiden.

<a id="gui1"></a>

### GUI1 – Ribbon und integrierte 2D-/3D-Ansichten

**Nutzerziel vom 15.11.2026:** Den geprüften 2D-Canvas erhalten und eine
integrierte räumliche Ansicht entwickeln, die langfristig auch die präzise
Bearbeitung übernehmen kann. Zunächst nur ein kleines Ansichts-Menüband;
weitere Ribbon-Themen und die vollständige Ribbon-Bibliothekswahl später.

**Arbeitszweig:** `ribbon-2d-3d`, aus dem bereinigten `develop`-Stand `3da5a15`
angelegt. Bis zur stabilen, fachlich abgenommenen Lösung bleiben diese
Änderungen auf dem eigenen Zweig; erst danach nach `develop` übernehmen.

VisPy startet standardmäßig in der Raumansicht. Draufsicht und Raumansicht
teilen die Zeichenregeln. Der 2D-Canvas ist in der Konfiguration wählbar und
dient als automatischer Rückfall. Qt Quick 3D und der ältere 3D-Canvas wurden
bei der Übernahme entfernt; der historische Vergleich bleibt dokumentiert.
SARibbon bleibt ein späterer Kandidat für das vollständige Menüband.

Offen bleiben die Nutzerprüfung der integrierten Ansicht und des Rückfalls,
die gesondert zu vereinbarenden Paket-/Plattformprüfungen und der Merge.
[Abarbeitungsplan](gui1-renderer-comparison-plan.md#p6--auswahl-und-übernahmeplan) ·
[Abschlussnachweis](../archive/toolpath-refactoring-completed.md#gui1-vispy-adoption).

<a id="maschinenabnahme"></a>

### Optionale Simulations-/Maschinenprüfung

- [ ] Später [CAMotics](https://camotics.org/) als ersten Simulationsschritt
  für exportierten 3-Achs-Fräs-G-Code prüfen. Vorher die Eignung für die
  verwendeten Postprozessorbefehle und den gewünschten Prüfumfang klären.
  CAMotics beschreibt 3-Achs-Materialabtrag und Werkzeugwegdarstellung;
  eine Drehmaschinen-Simulation ist dort ausdrücklich nicht enthalten.
- [ ] Bei Bedarf die Grbl-1.1-Laser- und LinuxCNC-2.9-Heißdraht-/Drehbeispiele
  auf einen ausdrücklich benannten realen Aufbau anpassen und dort abnehmen.
- [ ] Controller-Version, Profil, Schalt-/Werkzeugwechselablauf und tatsächlich
  geprüfte Bewegungen dokumentieren. Weitere CNC-/ATC-Abnahmen bei konkretem
  Bedarf separat vereinbaren.

CAMotics bleibt eine spätere Prüfoption, kein jetziger Ausführungsauftrag.
Laser, Heißdraht und Drehen sind damit nicht pauschal abgedeckt.

Geladene Demoprofile, synthetische Ausgabe, Simulatoren und Xvfb sind keine
Controller-/Material-/Maschinenfreigabe. Vor physischen Versuchen Auftrag klären.

Abgeschlossene Planungen: [Archiv](../archive/planning/README.md).
Wiederverwendbare Fachinformationen: [Dokumentationsnotizen](../documentation-notes/README.md).
