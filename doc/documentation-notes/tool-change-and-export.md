# Redaktionsnotizen: Werkzeugwechsel und Exportreihenfolge

Zuordnung: **WP4 sowie WP8–WP10**. Stand: **02.11.2026**.

## Exportreihenfolge und Optimierung

Die sichtbare Reihenfolge innerhalb eines Layers bestimmt den Export ohne
Optimierung, einschließlich benutzerdefiniertem G-Code. Manuelles Umordnen
erhält Startpunkte, Werkzeuge und Optimierungsfreigaben. Ein ausgeschaltetes
Routen-Live-Update setzt diesen Vertrag nicht außer Kraft.

Export ohne Optimierung, ausdrücklich optimierter Export und sichtbare
Routenanzeige getrennt erklären. Bestehende Optimierungsmodi erhalten die
vereinbarte relative Reihenfolge nicht freigegebener Konturen; keine festen
Platznummern oder Layerwechsel als bereits implementiert beschreiben. GUI und
CLI verwenden denselben Optimierungsmodus.

## Werkzeugwechsel und LinuxCNC

Als aktuelle Grundlagen dienen die [Makro-Anleitung](../tool-change-macros.md),
der [Werkzeugwechsel-Vorschlag](../tool-change-proposal.md) und der
[LinuxCNC-Abgleich](../linuxcnc-manual-tool-change.md). Das ladbare
[manuelle Profil](../examples/linuxcnc-manual.cfg.example) ist ein erklärtes
Beispiel, kein universelles Maschinenprofil.

- Programmstart, Freifahren vor einem Wechsel und Positionieren nach dem
  Wechsel getrennt darstellen. Rückzugshöhe ist keine Maschinen-Home-Position.
- Werkzeugwechsel zwischen Layern und durch Werkzeugoverride einer Kontur
  berücksichtigen. Dieselbe Werkzeugnummer löst keinen zusätzlichen Wechsel aus.
- Der vereinbarte LinuxCNC-Ablauf verwendet manuelles M6, vorbereitete
  Werkzeugtabelle und G43 ohne pauschale Zuordnung H = T. Absolute und
  inkrementelle Wiederaufnahme werden in den Referenzausgaben unterschieden.
- Optionale verwaltete Makros benötigen einen erklärten Rückkehrzustand und
  eindeutige Positions-/Modalwerte. Beliebigen Makro-G-Code nicht als allgemein
  analysierbar oder für jede ATC-Konfiguration freigegeben darstellen.
- Bestehende Standardprofile aktivieren nicht automatisch eine neue
  Werkzeuglängenkorrektur. Unterstützte Ausgabe- und Modusgrenzen sowie das
  dann aktuelle Postprozessorschema vor Veröffentlichung erneut abgleichen.

Für eine Anleitung eine vollständige Sequenz mit zwei Werkzeugen zeigen, nicht
nur einzelne M6-/G43-Zeilen. Konkrete Controller-Version, HAL/INI-Einstellungen,
Werkzeuglängen, Bezug und freie Wechselwege bleiben am jeweiligen Aufbau zu
prüfen. Die in [completed](../archive/toolpath-refactoring-completed.md#p1-linuxcnc)
verzeichneten Softwaretests sind keine Maschinenfreigaben.
