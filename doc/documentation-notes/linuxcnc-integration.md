# LC1: LinuxCNC-Dateifilter – Bestandsaufnahme

Stand: **05.11.2026**. Die folgende Bestandsaufnahme beschreibt Quellbasis
`7864ba2` vor der Korrektur. Statische Code-/Historienprüfung und Abgleich mit
offiziellen Quellen im Windows-Checkout. Die anschließend beauftragte lokale
Umsetzung mit Prozessregressionen ist [unten](#lokal-umgesetzter-gui-filter)
dokumentiert. Die spätere reale Debian-/AXIS-Abnahme ist im letzten Abschnitt
ergänzt; sie umfasst keinen Maschinenlauf.

## Historischer und heutiger Ablauf

Die [historische Installationsanleitung](https://sourceforge.net/p/dxf2gcode/wiki/Installation/)
beschreibt unter „Integration in EMC 2.2 and Axis“ einen DXF-Dateifilter:
AXIS startet dxf2gcode mit dem Dateinamen; der Anwender bearbeitet die Zeichnung
in der GUI und exportiert G-Code auf stdout. Die Git-Historie bestätigt diesen
Vertrag, etwa `c43e586` (12.07.2014, Argumentparser für EMC2) und `4525a34`
(06.01.2015, Logging für EMC2).

Das passt weiterhin zum offiziellen
[LinuxCNC-2.9-FILTER-Vertrag](https://linuxcnc.org/docs/2.9/html/config/ini-config.html#_filter_section):
AXIS und GMOCCAPY können nach Dateiendung einen externen Filter aufrufen.
Dieser erhält den Eingabepfad und schreibt G-Code auf stdout. Der
[AXIS-2.9-Quellcode](https://github.com/LinuxCNC/linuxcnc/blob/2.9/src/emc/usr_intf/axis/scripts/axis.py)
(`filter_program`, `open_file_guts`) zeigt die Umleitung in eine temporäre
Datei sowie Fehlerbehandlung anhand eines von null verschiedenen Exitstatus.
stderr wird getrennt erfasst; optional sind `FILTER_PROGRESS`-Meldungen möglich.
Dies ist ein Datei-/Prozessvertrag, keine direkte Maschinensteuerung oder
gemeinsame Python-Laufzeit mit LinuxCNC.

Im aktuellen dxf2gcode-Code bestehen die zentralen Teile noch:

- [GUI und Startlogik](../../source/dxf2gcode/presentation/qt/application.py):
  positionales `filename`, Konfigurationsprofil über `--cfg`; bei
  `General.write_to_stdout` überspringt `exportShapes` den Speicherdialog und
  schließt nach dem Export das Fenster.
- [Postprozessor](../../source/dxf2gcode/adapters/postprocessor/postprocessor.py):
  baut den Programmtext auf und gibt ihn mit `print(exstr)` auf stdout aus.
- [Logging](../../source/dxf2gcode/bootstrap/logging.py): Konsolenmeldungen gehen
  an stderr, nicht in den G-Code-Kanal.
- Keine spezielle LinuxCNC-Python-API oder `axis-remote`-Anbindung im untersuchten
  aktuellen Anwendungscode gefunden. G-Code-Dateiexport und die M6-Beispiele
  belegen diesen interaktiven Filterablauf nicht.

## Befunde und Grenzen

1. **Postprozessorauswahl:** Im GUI-stdout-Zweig wird Index 0 fest vorgegeben;
   `--postpro` wird dort nicht ausgewertet. Vorhandene Profil-Dateien werden
   normalerweise alphabetisch geladen. Ein zusätzliches Profil kann somit
   ändern, welcher Postprozessor zuerst steht. Das ist keine belastbare
   Auswahl eines LinuxCNC-Profils.
2. **Abbruch und Fehlerstatus:** `closeEvent` unterscheidet Schließen ohne
   Export nicht von erfolgreichem Export. `exportShapes` zeigt gesammelte
   Exportfehler an und schließt im stdout-Modus trotzdem. Ein eigener
   Filter-Erfolgs-/Fehlerstatus fehlt dort; der Startpfad gibt den Qt-Eventloop-
   Status zurück. Daraus folgt ein Risiko leerer oder fehlerhafter Rückgaben
   bei Status 0, kein durch einen Lauf bestätigter LinuxCNC-Defekt.
3. **Automatischer CLI-Filter:** Der vorhandene Headless-Pfad benötigt
   `--quiet`, Eingabe und `--export FILE`. Es gibt keinen ausdrücklichen
   CLI-stdout-Schalter; stdout ist eine Profileinstellung. `--quiet input.dxf`
   allein ist daher kein geeigneter automatischer Filteraufruf. Ein
   Dateiexport-Argument mit aktiviertem stdout wäre nur ein Umweg.
4. **Veraltete Einrichtung:** Die historische Anleitung nennt
   `[Export Parameters]`; aktuell gehört `write_to_stdout` unter `[General]`.
   Ein fester `/usr/bin`-Ort ist laut heutiger LinuxCNC-Anleitung nicht nötig:
   absoluter Programmpfad oder PATH genügt. Der installierte Konsoleneinstieg
   heißt inzwischen `dxf2gcode`.
5. **Bestehende Abdeckung:**
   [test_stdout_export_prints_the_completed_program](../../tests/dxf2gcode_stmove_gcode_test.py)
   prüft einen gemockten `print`-Aufruf mit leerer Layerliste. Das belegt weder
   einen kompletten Filterprozess noch GUI-Abbruch, Exitstatus oder AXIS-Laden.
   Diese vorhandene Prüfung wurde hier nur gelesen, nicht erneut ausgeführt.

## Nutzen und Empfehlung

**Beibehalten und gezielt modernisieren.** Im Hobby-/Werkstattablauf kann der
Anwender eine DXF direkt in AXIS öffnen, Bearbeitungswerte und Konturauswahl
anpassen und mit Export unmittelbar zur LinuxCNC-Vorschau zurückkehren.
Bei bereits gespeicherten CAM-Projekten, wiederholbaren Stapelabläufen oder
bewusst getrennten Arbeitsplätzen bleibt eigenständiger GUI-/CLI-Dateiexport
mit anschließendem Laden einfacher und transparenter.

Vor einer Änderung ausdrücklich abstimmen: zunächst nur den interaktiven
GUI-Filter erhalten oder zusätzlich einen automatischen CLI-Filter anbieten;
Postprozessor explizit wählen und Fehler/Abbruch von erfolgreichem Export
unterscheiden. Keine Entfernung oder Implementierung durch diese Empfehlung.

## Ursprünglicher Vorschlag für die fokussierten Prüfungen

Nach Freigabe zunächst fokussierte lokale Prozess-/GUI-Regressionen entwerfen
und ausführen, jeweils mit isoliertem Profil, 2D-Modus und der eigenen
[20×10-mm-DXF](../../docs/assets/examples/first-dxf/rectangle-20x10-mm.dxf):

- Dateiname mit Leerzeichen, korrektes Laden und erfolgreicher Export;
  stdout enthält ausschließlich ein vollständiges Programm, Meldungen stderr.
- Zwei Postprozessoren mit unterscheidbaren Kopfzeilen; angefordertes Profil
  wird unabhängig von der Dateireihenfolge benutzt, unbekanntes Profil scheitert.
- Schließen ohne Export, fehlende/ungültige DXF und blockierender Planungsfehler:
  kein erfolgreich gemeldeter G-Code, eindeutiger Fehler-/Abbruchstatus.
- PyQt5 und PyQt6 getrennt prüfen; vorhandenen normalen Dateiexport erhalten.

Danach gesondert eine LinuxCNC-2.9-AXIS-Simulation unter Linux vereinbaren:
DXF über `[FILTER]` öffnen, GUI-Export und Rückkehr zur Vorschau sowie Abbruch
und Fehler prüfen, ohne ein Programm zu starten. Linux-Distribution,
LinuxCNC-Version, Python-/Qt-Version und Installationsart vorher festlegen.
Das aktuelle Paket verlangt Python >=3.9 und PyQt5 >=5.15; PyQt6 ist optional
und wird, wenn installiert, standardmäßig bevorzugt (`DXF2GCODE_QT=5` erzwingt
Qt5). Ein separater Filterprozess kann einen eigenen Interpreter verwenden.

Erst nach Auswahl und Prüfung eine reproduzierbare Anwenderanleitung mit
explizitem ausführbarem Pfad, festem `--cfg`-Profil, `[FILTER]`-DXF-Zuordnung
und aktueller stdout-Einstellung veröffentlichen. Paketinstallation, X11/
Wayland-Fensterverhalten und GMOCCAPY sind damit noch nicht abgenommen.

## Lokal umgesetzter GUI-Filter

Die gezielte GUI-Filterkorrektur wurde anschließend vom Nutzer freigegeben und
umgesetzt. `--postpro` akzeptiert die Beschreibung oder den vollständigen
Filtertext (z. B. `G-CODE for LinuxCNC (*.ngc)`). Genau ein Treffer ist nötig;
bei unbekannten oder mehrdeutigen Beschreibungen erfolgt keine Ausgabe.
Ohne Angabe bleibt aus Kompatibilitätsgründen Index 0 der Standard; für eine
feste Integration ausdrücklich `--postpro` angeben.

| Prozessstatus | Bedeutung im GUI-stdout-Modus |
| --- | --- |
| `0` | Fehlerfreier Export; vollständiger G-Code auf stdout |
| `1` | Fenster ohne Export geschlossen; keine Programmausgabe |
| `2` | Behandelter Import-/Exportfehler; keine Programmausgabe |

Exportfehler einschließlich gesammelter Planungsfehler verwerfen die während
des Exports gepufferte Ausgabe. Meldungen bleiben auf stderr. Fehlende
Eingabedateien führen zum Fehler statt zu einem Ersatz-Dateidialog.
Der normale GUI-/CLI-Dateiexport behält seinen bisherigen Ablauf.

Nach Vorbereitung eines eigenen Profils mit `[General] write_to_stdout = True`
ist der interaktive Aufruf beispielsweise:

```sh
/absoluter/pfad/zur/venv/bin/dxf2gcode --cfg linuxcnc --postpro "G-CODE for LinuxCNC" "/pfad/zeichnung.dxf"
```

Das Profil liegt unter `~/.config/dxf2gcode.linuxcnc`, die Einstellung in
`config/config.cfg`. Für die spätere LinuxCNC-Einrichtung käme die Zuordnung
unter `[FILTER]` infrage:

```ini
PROGRAM_EXTENSION = .dxf DXF drawing
dxf = /absoluter/pfad/zur/venv/bin/dxf2gcode --cfg linuxcnc --postpro "G-CODE for LinuxCNC"
```

Die DXF wird von LinuxCNC angehängt. Diese INI-Zuordnung ist noch nicht in AXIS
ausgeführt; sie ist ein Einrichtungsvorschlag, keine geprüfte Linux-Anleitung.
Der Anwender bearbeitet die DXF in der GUI und wählt anschließend Export.
Ein eigenständiger automatischer CLI-stdout-Filter wurde nicht ergänzt;
die oben beschriebenen Headless-Grenzen gelten weiterhin.

[Lokale Prozessregressionen](../../tests/dxf2gcode_linuxcnc_filter_test.py):
12 Tests je Qt-Bindung bestanden, plus je zwei vorhandene GUI-/CLI-Dateiexport-
Regressionen. Tests erzeugen ein temporäres Profil und eine Kopie der eigenen
Rechteck-DXF, liefern die Nutzeraktion per Qt-Timer und prüfen die Ausgabe und
den Status des tatsächlichen Startprozesses. Nur die Exportexception wird
gezielt injiziert; der Drill-/Pocket-Konflikt läuft durch den echten Export.
Zum Zeitpunkt dieser lokalen Prüfung blieben LinuxCNC-Simulation, reale
Paketinstallation und Plattformfensterverhalten separat offen.
[Lokaler Abschlussnachweis](../archive/toolpath-refactoring-completed.md#lc1-filter).

## Reale Debian-/AXIS-Abnahme

Anschließend nach Nutzerauftrag mit LinuxCNC 2.9.4, Python 3.13.5 und
PyQt5 5.15.11 / Qt 5.15.15 auf Debian 13 durchgeführt. Der Nutzer installierte
die benötigten Debian-Pakete. Eigene Simulationskopie, getrenntes HOME und
Xvfb-Anzeige; kein Programmstart oder Bewegungsbefehl.

Der erste AXIS-Lauf zeigte verschachtelte Klammern im Versionskommentar.
Nach Umstellung der darin eingebetteten Runtime-Angabe auf eckige Klammern
lud AXIS denselben G-Code mit sichtbarer Rechteck-Werkzeugbahn fehlerfrei.
Fensterabbruch, unbekannter Postprozessor und ungültige DXF ergaben die
erwarteten Status 1/2/2, leeres stdout und AXIS-Fehlerdialoge; das gültige
Programm blieb geladen. ESTOP/IDLE und Nullpositionen blieben erhalten.
Die Testprozesse wurden beendet, Nachweise lokal gesichert.

[Vollständiger Abschlussnachweis](../archive/toolpath-refactoring-completed.md#lc1-axis)
und [Anwenderanleitung](../../docs/user-guide/linuxcnc-axis.md). Keine Aussage
über Maschinenbetrieb, paketierte Installation, GMOCCAPY, Wayland oder
Linux/PyQt6. Der automatische CLI-Filter bleibt optional und unbeauftragt.
