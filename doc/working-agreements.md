# Arbeits- und Prüfregeln

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

## Prüfstrategie

Die Beschränkung umfangreicher Prüfläufe betrifft die lokale Arbeit von Codex.
Auf GitHub läuft die Vollsuite automatisch bei Push auf `develop` und Pull
Requests nach `develop`; ein manueller Start bleibt möglich. Bei lokalen
Commits mit Quellcode-, Test- oder ausführbaren Werkzeugänderungen führt der
Pre-Commit-Hook die Fast-Suite aus. Reine Dokumentationscommits einschließlich
Bildern, Beispielzeichnungen und Navigation benötigen nur passende
Dokumentationsprüfungen. Nach Kontrolle der gestagten Pfade darf der derzeit
pauschale Hook dafür ausschließlich im einzelnen Commit-Aufruf deaktiviert
werden; die persistente Hook-Konfiguration bleibt erhalten. Ein bestandener
Fast-Hook wird nicht zusätzlich manuell wiederholt.

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

## Vor jeder Umsetzung

Nur den gewählten, überschaubaren Teilbereich bearbeiten. Offene fachliche
Entscheidungen vorher klären. Vorhandene Tests verwenden und nur echte
Verhaltenslücken ergänzen. Nach bestandenen passenden Prüfungen keine
weiteren Abschlussrunden ohne konkreten Anlass anhängen. Frühere Freigaben
für Vollsuite, Debian oder Builds gelten nicht als dauerhafte Freigabe.
Bei GUI-Textänderungen alle gepflegten TS-Kataloge (Deutsch, Französisch,
Russisch) im selben Schritt aktualisieren, die zugehörigen QM-Dateien
erzeugen und die geänderten Übersetzungen prüfen. Kein Commit ohne Auftrag.

Die verbindlichen Repository-Anweisungen stehen in [AGENTS.md](../AGENTS.md).
Für die laufende Aufgabenpflege gilt: nur offene Themen in der Todo,
Abschlüsse nach completed und spätere Anleitungshinweise in die
[Dokumentationsnotizen](documentation-notes/README.md).
