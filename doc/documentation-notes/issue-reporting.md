# Issue-Formulare und relevante Anhänge

Stand: **03.11.2026**. Redaktionsmaterial für Support sowie WP8–WP12.

Die Vorlagen unter `.github/ISSUE_TEMPLATE/` enthalten englische Formulare
für Bug report, Feature request und Documentation issue. Alle erlauben
ausdrücklich Beschreibungen auf Englisch oder Deutsch. Die Auswahl verweist
für Nutzungsfragen ins bestehende Forum und für Fehler des Linux-Installers
in dessen Issue-Tracker. Freie Issues sind für normale Nutzer deaktiviert;
Nutzer mit Schreibrechten können sie als „Maintainers only“ weiterhin anlegen.
Labels verwenden die
vorhandenen Namen `bug`, `enhancement` und `documentation`.

Das Fehlerformular fragt zusätzlich nach Installationsweg und betroffenem
Bereich. Maschinenmodus, Steuerung, aktives Konfigurationsprofil und der
verwendete Postprozessor sind optionale Angaben für relevante Fälle. Anhänge
sind nicht generell verpflichtend: kleine DXF/D2G-Beispiele, relevante
Konfiguration, Postprozessor, Screenshots, Logs und G-Code nach Bedarf.
Bei D2G-Projekten die zugehörige Zeichnung mitgeben; unbekannte Dateiendungen
und zusammengehörige Beispiele vorzugsweise als ZIP anhängen.

## Verifizierte Dateipfade

Aktuelle Versionen verwenden `os.path.expanduser("~")/.config/dxf2gcode`
auf beiden Plattformen. **Windows verwendet hier nicht AppData.**

| Datei | Linux | Windows |
| --- | --- | --- |
| Anwendung | `~/.config/dxf2gcode/config/config.cfg` | `%USERPROFILE%\.config\dxf2gcode\config\config.cfg` |
| Postprozessor | `~/.config/dxf2gcode/postpro_config/<Datei>.cfg` | `%USERPROFILE%\.config\dxf2gcode\postpro_config\<Datei>.cfg` |

Bei benannten Profilen `dxf2gcode` durch `dxf2gcode.<Name>` ersetzen, etwa
`dxf2gcode.laser`. Die untere Meldungsleiste zeigt beim Start unter
„For Configuration files refer to folder:“ den aktiven Profilordner als Link.
Dieser Laufzeitpfad ist gerade bei älteren Versionen maßgeblich.

Bei Exportproblemen die tatsächlich verwendete Postprozessor-Datei anhängen,
nicht beliebig die Standarddatei `postpro_config.cfg`. Die Datei kann einen
anderen Namen haben. Konfigurationen nur bei Relevanz anfordern; persönliche
Inhalte und nicht freigegebene Zeichnungen vor Veröffentlichung entfernen.

Quellen: `source/dxf2gcode/domain/constants.py`, `adapters/config/runtime_config.py`,
`adapters/postprocessor/postprocessorconfig.py` und
`presentation/qt/messagebox.py` innerhalb des Anwendungspakets.
Die Dateipfade und Profilnamensbildung wurden gegen diese Implementierung
geprüft. GitHub-Vorlagen werden erst nach Commit auf dem Standardbranch aktiv.
