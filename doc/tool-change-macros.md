# Werkzeugwechselmakros im Postprozessor

Implementiert am **01.11.2026**, Postprozessor-Konfigurationsversion **8.2**.
Die Versionen 8 und 8.1 bleiben lesbar. Alte Profile erhalten automatisch
`return_state = legacy` und behalten ihre bisherige Ausgabe.

## Einrichtung

In der Postprozessor-Konfiguration bleibt das Feld **Werkzeugwechsel** unter
den G-Code-Befehlen das eigentliche Makro: `Program.tool_change`. Es kann einen
manuellen Wechsel, einen automatischen Wechsler oder ein steuerungseigenes
Unterprogramm aufrufen. Es wird beim ersten Werkzeug und danach bei jeder
geänderten effektiven Werkzeugnummer ausgegeben, auch innerhalb eines Layers.
Gleiche aufeinanderfolgende Werkzeugnummern lösen keinen weiteren Wechsel aus.

Der neue Abschnitt **Werkzeugwechselmakro** enthält den Rückkehrvertrag:

```ini
[Tool_Change]
return_state = next_start_at_retract
end_distance_mode = G90
work_offset = G54
length_offset_mode = tool_number
length_offset_mapping = ""
```

`next_start_at_retract` ist eine Zusicherung des Profils: Das Makro endet mit
der neuen Werkzeugspitze am nächsten XY-Anfahrpunkt und auf der zugehörigen
Rückzugshöhe. Einheit und Werkstückbezug passen zum Export, Werkzeugradius-
kompensation ist ausgeschaltet (G40), und benötigte Werkzeuglängenkorrektur
ist wirksam. Die Software wertet keinen beliebigen Makro-G-Code aus, um diese
Zusicherung zu beweisen.

`end_distance_mode` bezeichnet den tatsächlichen Modus **am Ende des Makros**.
Falls er vom Exportmodus abweicht, gibt der Adapter anschließend G90 oder G91
aus. Die interne Position wird auf die zugesicherten absoluten Zielkoordinaten
gesetzt, sodass anschließende G91-Differenzen von dort ausgehen. Der nächste
geplante Vorschub wird nach dem Wechsel ausdrücklich erneut ausgegeben.

`work_offset` unterstützt G54 bis G59 und G59.1 bis G59.3. Das Makro muss diesen
Werkstückbezug selbst erhalten oder herstellen. `legacy` aktiviert keinen
solchen Vertrag und lässt die bestehende Ausgabe einschließlich initialer
Z-Bewegung unverändert.

## Makroparameter

| Platzhalter | Wert |
| --- | --- |
| `%tool_nr` | Neue Werkzeugnummer |
| `%speed` | Drehzahl für das neue Werkzeug |
| `%nl` | Zeilenumbruch, auch unmittelbar vor einem Befehl: `%nlG90` |
| `%next_start_x`, `%next_start_y` | Erster tatsächlicher XY-Anfahrpunkt des Plans, einschließlich Lead-in/Pocket-Einstieg |
| `%retract_z` | Rückzugshöhe des nächsten Plans im Werkstückbezug |
| `%initial_retract_z` | Gesonderte globale initiale Rückzugshöhe |
| `%length_offset_nr` | Werkzeuglängenkorrektur gemäß ausdrücklich gewählter Zuordnungsregel |
| `%units_code` | G21 bei Millimetern, G20 bei Zoll |
| `%distance_mode` | Konfigurierter Exportmodus, G90 oder G91 |
| `%work_offset` | Vereinbarter Werkstückbezug aus `Tool_Change.work_offset` |
| `%previous_tool_nr` | Vorherige Werkzeugnummer; beim ersten Wechsel nicht verfügbar |

Die Zielkoordinaten sind immer absolute Werte in der Exporteinheit. Die
Längenformatierung übernimmt das Zahlenformat des Postprozessors.
Bestehende bewegungsabhängige Werte wie `%ZE` sind im verwalteten Wechselmakro
bewusst nicht verfügbar: Hier sollen keine zufälligen Werte der vorherigen
Formatierungsaktion als Wechselziel dienen. In Legacy-Profilen bleiben die
vorhandenen Platzhalter unverändert nutzbar.

Direkte skalare Profilwerte können über `${post.Abschnitt.Parameter}` verwendet
werden, etwa `${post.Number_Format.post_decimals}` oder
`${post.Tool_Change.work_offset}`. Ganzzahlen und Gleitkommazahlen werden nach
dem Profil formatiert, boolesche Werte als 0/1 ausgegeben. Verschachtelte
`${...}`-Referenzen und Zugriffe auf ganze Abschnitte sind nicht zulässig.
Das ist eine Platzhalterexpansion, keine Python-Ausführung.

Vorhandene benannte Einträge aus `Custom_GCode` können weiterhin als Makrobausteine
eingebunden werden; deren Wechselparameter werden anschließend expandiert.
Zyklische Verweise werden zurückgewiesen.

## Werkzeuglängen und Wechselablauf

- `length_offset_mode = none`: kein H-Wert bereitgestellt. Passend für ein
  eingerichtetes Makro, das die Werkzeuglänge selbst vollständig behandelt.
- `tool_number`: H-Nummer entspricht ausdrücklich der Werkzeugnummer.
- `mapping`: `length_offset_mapping = "1:4,2:9"` ordnet Werkzeug 1 dem Register
  H4 und Werkzeug 2 dem Register H9 zu. Fehlende oder doppelte Zuordnungen
  werden zurückgewiesen.

Beispiel eines **anzupassenden ATC-Makrotexts** nach dem Forumsablauf:

```text
G91 G28 Z0%nlT%tool_nr M6%nlG90 %units_code %work_offset%nlG0 X%next_start_x Y%next_start_y%nlG0 G43 H%length_offset_nr Z%retract_z%nlS%speed%nl
```

Voraussetzungen dieses Beispiels sind eine passende gespeicherte G28-Position,
ein eingerichtetes M6-Verfahren und gültige Werkzeuglängenregister. Die
Reihenfolge XY vor Z muss zur konkreten Maschine und Aufspannung passen.
Dies ist kein freigegebenes Universalprofil.

Beim manuellen Wechsel kann derselbe Makrotext ein eingerichtetes manuelles
M6-Verfahren aufrufen. Alternativ darf das Makro einen steuerungsspezifischen
Halt und Vermessungsablauf enthalten; ein M0 allein aktualisiert keine
Werkzeuglängentabelle. Auch dann muss am Ende der Rückkehrvertrag erfüllt sein.
Spindel-/Kühlmittelstart kann wie bisher in `Program.pre_shape_cut` bleiben.

## Grenzen und Fehlerbehandlung

Die erste Version des verwalteten Ablaufs unterstützt Fräs-G-Code. Freie
`CustomGCode`-Zeilen im Bearbeitungsbaum werden in diesem Modus zurückgewiesen:
Sie könnten Position oder Modalzustand außerhalb des Rückkehrvertrags verändern.
Benannte Makrobausteine **im Wechselmakro** sind dagegen möglich. Andere
Maschinenmodi und freie Baumzeilen funktionieren weiterhin mit Legacy-Profilen.

Der nächste Plan wird einmal erzeugt und sowohl für die Wechselparameter als
auch für die eigentliche Bearbeitung verwendet. Ungültige Planeingaben, leere
Wechselmakros im verwalteten Modus, unbekannte Parameter und fehlende
Zuordnungen brechen den Export vor dem Schreiben ab. Eine vorhandene Zieldatei
bleibt erhalten. Die GUI zeigt die Diagnose; der CLI-Export meldet einen Fehler.
Ein leerer Auftrag erzeugt im verwalteten Modus keine Wechsel- oder
Positionierbewegung.

Die beiden vollständigen Testausgaben stehen unter
`tests/golden/tool_change_atc.ngc` und
`tests/golden/tool_change_manual_incremental.ngc`. Sie sind synthetische
Regressionen, keine Maschinenfreigaben. Die Recherche und fachliche Herleitung
stehen im [Strukturvorschlag](tool-change-proposal.md).

## Lokale Prüfung

Unter PyQt5 und PyQt6 bestehen jeweils die 16 neuen Werkzeugwechseltests,
acht Profil-/Migrationstests, drei Dialekttests und 18 bestehende Leadmove-
Goldens. Zusätzlich wurden Shape-Werkzeuge, Exportreihenfolge und der
MainWindow-Workflow gezielt geprüft. Ein direkter Vergleich mit dem vorherigen
Export bestätigt unveränderte Legacy-Ausgabe für G90/G91 und normales/leeres
Wechseltemplate in vier Fällen. Keine Vollsuite, Debian-Prüfung oder Paketbuild.
