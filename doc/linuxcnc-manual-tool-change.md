# P1: LinuxCNC mit manuellem Werkzeugwechsel

Stand: **02.11.2026**. Abgleich mit der offiziellen stabilen LinuxCNC-
Dokumentation; kein Lauf auf einer Maschine oder in einem LinuxCNC-Interpreter.
Der Nutzer verwendet LinuxCNC ohne automatischen Werkzeugwechsler. Die genaue
Steuerungsversion, HAL-/INI-Konfiguration und Werkzeuglängen sind nicht bekannt.
Die Softwareprüfung verwendet deshalb einen ausdrücklich beschriebenen Ablauf;
die Anwender prüfen anschließend ihre eigene Maschine.

## Ergebnis des Standard-Abgleichs

- `Tn M6` wählt und wechselt das Werkzeug. Bei eingerichtetem
  `hal_manualtoolchange` stoppt LinuxCNC die Spindel und fordert den manuellen
  Wechsel an. Das ist kein automatischer Werkzeugwechsler.
- `M6` aktiviert nicht selbst die neue Werkzeuglängenkorrektur. `G43` ohne
  H-Wort verwendet das zuletzt mit `Tn M6` geladene Werkzeug. `G43` allein
  bewegt keine Achse; erst die nächste Bewegung verwendet die Korrektur.
- `M0` ist kein gleichwertiger Ersatz für den manuellen M6-Dialog: LinuxCNC
  bleibt dabei im Automatikmodus; MDI und manuelle Bedienaktionen sind nicht
  freigegeben.

Quellen: [LinuxCNC M6 und M0](https://linuxcnc.org/docs/stable/html/gcode/m-code.html),
[G43](https://linuxcnc.org/docs/stable/html/gcode/g-code.html#gcode:g43),
[hal_manualtoolchange](https://linuxcnc.org/docs/stable/html/man/man1/hal_manualtoolchange.1.html).

Das bestehende DXF2GCODE-Standardprofil gibt weiterhin `T%tool_nr M6` und
die Drehzahl aus. Es ist ein Legacy-Profil **ohne automatisch aktivierte
Werkzeuglängenkorrektur**. Der Programmstart enthält G49. Bestehende Profile
werden nicht stillschweigend auf Werkzeugtabellen oder ein neues
Koordinatensystem umgestellt. Ein eigener Mess-/Antastablauf ist nicht Teil
dieses Standardprofils.

## Ladbares Beispielprofil mit vorbereiteter Werkzeugtabelle

[linuxcnc-manual.cfg.example](examples/linuxcnc-manual.cfg.example) nutzt den
vorhandenen verwalteten Wechselablauf. Die übrigen Felder ergänzt das
Konfigurationsschema beim Laden mit seinen Vorgaben. Der Test lädt genau
diese Datei über `MyPostProConfig`, nicht eine nachgebildete Makrozeichenkette.

1. Die Datei als `linuxcnc-manual.cfg` in das eigene `postpro_config`-
   Verzeichnis kopieren und dieses Profil beim Export auswählen.
2. Alle Werkzeuge vorher in der LinuxCNC-Werkzeugtabelle vermessen.
   Das Beispiel tastet nicht an und schreibt weder Tabelle noch Nullpunkt um.
3. Den manuellen M6-Dialog einrichten und prüfen. Eine Bestätigung ohne
   tatsächlich passenden Werkzeugwechsel erfüllt den Profilvertrag nicht.
4. `Tool_Change.work_offset` (Beispiel: G54), Einheiten, globale initiale
   Rückzugshöhe und Rückzugshöhen der Bearbeitungspläne passend einstellen.
   Die globale Höhe muss vor jedem Wechsel eine freie Z-Bewegung erlauben,
   beim ersten Wechsel auch aus dem Startzustand mit G49. Dies lässt sich
   offline nicht aus dem DXF feststellen.

Der Makroablauf ist:

```text
G90 <Einheit> <Werkstückkoordinatensystem>
G0 Z<globale initiale Rückzugshöhe>
M5
M9
T<Werkzeugnummer> M6
G90 <Einheit> <Werkstückkoordinatensystem>
G43
G0 Z<Rückzugshöhe des nächsten Plans>
G0 X<tatsächlicher Anfahrpunkt X> Y<tatsächlicher Anfahrpunkt Y>
S<Drehzahl>
```

Keine G28-/G30-/G53-Wechselposition, H=T-Zuordnung oder Antastbefehle werden
vorgegeben. Die LinuxCNC-Konfiguration kann eigene Wechselbewegungen enthalten;
siehe [INI-Werkzeugwechseloptionen](https://linuxcnc.org/docs/stable/html/config/ini-config.html).
Die erste Z-Bewegung nach dem Wechsel verwendet G43 und erfolgt vor XY.
Das Makro erklärt `next_start_at_retract`, `end_distance_mode=G90`.
Bei inkrementellem Export stellt DXF2GCODE danach G91 wieder her und berechnet
die nächsten Differenzen aus der erklärten neuen Position. Spindel und
Kühlmittel werden vom normalen Bearbeitungsablauf wieder eingeschaltet.

## Softwareabnahme und verbleibende Praxisprüfung

Zwei vollständige Referenzausgaben enthalten zwei Werkzeuge mit verschiedenen
Rückzugshöhen:

- `tests/golden/tool_change_linuxcnc_manual_absolute.ngc`
- `tests/golden/tool_change_linuxcnc_manual_incremental.ngc`

Die Tests prüfen das geladene Beispielprofil, M5/M9 vor M6, G43 vor Z,
Z vor XY, die Rückzugshöhen und die G91-Wiederaufnahme. Zusätzliche Prüfungen
sichern den bisherigen Standard ohne G43 ab. Vorhandene Tests decken A–B–A,
Shape-Overrides, unveränderte Werkzeuge, leere Aufträge, Lead-Einstieg,
Zuordnungsfehler und unbeschädigte Zieldateien ab.

Die Anwender prüfen insbesondere Werkzeuglängen, Koordinatensystem, freie
Wechsel-/Rückzugswege, M6-Bestätigung, Spindel/Kühlmittel und die erste Bewegung
nach dem Wechsel. Das Beispiel gilt für Fräs-G-Code ohne freie Custom-G-Code-
Zeilen im Bearbeitungsbaum. Andere Maschinen und Messverfahren verwenden
eigene Makros gemäß der [Makro-Anleitung](tool-change-macros.md).
