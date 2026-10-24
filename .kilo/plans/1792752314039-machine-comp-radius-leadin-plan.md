# Plan: Kreis-/Startmove-Einfahrt bei Maschinenkompensation korrigieren

## Ziel
Maschinenkompensation (`cut_cor in (41,42)`, `done_by_machine=True`), Einfahrt **Kreis**
(`LEAD_RADIUS`) bzw. **Startmove** (`LEAD_STARTMOVE`):
- **G40-Abschnitt:** Werkzeugmittelpunkt liegt bereits korrekt um `r` (=Werkzeugradius) neben der
  nominalen Einfahrtslinie. Eintauchpunkt ist dieser versetzte Punkt.
- **Danach G41/G42**, danach der **nominale** Lead-in (Linie + Bogen), den die Maschine kompensiert.
- Die Linie ist tangential zum Bogen; der Bogen tangiert die Kontur.

Zielsequenz (Beispiel Quadrat, G41, `R_w=20`, `r=5`, Start `S=(0,0)`, Tangente +X):
```
G0 X -15.000 Y  40.000     ; dive = versetzter Linienanfang + normal*L
G1 X -15.000 Y  35.000     ; G40-Gerade (tool-center, parallel zur nominalen Linie, +r versetzt)
G1 Z  -2.000               ; Eintauchen am versetzten Start (G40)
G41                        ; Kompensation EIN
G1 X -20.000 Y  20.000     ; nominale Linie nach A (Maschine kompensiert -> Werkzeug (-15,35)->(-15,20))
G3 X   0.000 Y   0.000 I 20.000 J 0.000   ; nominaler 90°-Bogen (kompensiert -> (-15,20)->(0,5))
G1 X 100.000 Y   0.000     ; nominale Kontur (kompensiert -> y=5)
```
**Einfahrt „Gerade" bleibt unverändert** (`g41_lead_in_straight.gcode`) – laut Rückmeldung korrekt.
**Software-Kompensation bleibt unverändert.**

## Ist-Zustand / Defekt
Aktuell (`tests/golden/g41_lead_in_radius.gcode`) lautet der Kreis-Lead-in:
`G0 (-20,35) -> Eintauchen (G40) -> G41 -> G1 (-20,20) -> G3 (0,0)`.
Der Dive liegt **auf** der nominalen Linie (nicht um `r` versetzt), daher sitzt der
Werkzeugmittelpunkt unter G40 auf der falschen Bahn und die Maschine rampt ihn seitlich
(`(-20,35) -> (-15,20)`). Genau das soll weg.

## Geometrie (allgemein)
Gegeben: Konturstart `S`, Startrichtung `angle`, `side = +1 (G41) / -1 (G42)`,
`tangent = _direction(angle, side) = (cos,sin)`, `normal = _normal(angle, side) = (-sin*side, cos*side)`,
`r` = Werkzeugradius, `R_w` = Werkstückradius.

- Nominale Einfahrtslinie (bestehend, `build_lead_in`/`build_start_move`, `SPACE_NOMINAL`):
  Bogenzentrum `C = S + normal*R_w`, Bogenstart `A = C - tangent*R_w`,
  Linie `Q -> A` mit `Q = A + normal*build_up` (radial; Richtung `d = (A-Q)/|A-Q| = -normal`),
  Bogen `A -> S` (Radius `R_w`, Richtung `1 if side>0 else 0`).
  `build_up` = `R_w - r` (Radius) bzw. `common length` (Startmove) – unverändert lassen.
- **Versatz** des Werkzeugmittelpunkts zur Linie (Kompressionsrichtung der Maschine = links/rechts
  der Linienfahrtrichtung): `offset_dir = rotate(d, side*90°)`
  (für `side=+1`: `offset_dir = (-d.y, d.x)`).
  Im Quadrat-Spiel: `d=(0,-1)` -> `offset_dir=(1,0)=tangent` -> versetzt um `+r` in `+X`.
- **G40-Gerade:** von `dive` nach `P = Q + offset_dir*r`, Richtung `d`, Länge `L`:
  `dive = P - d*L = P + normal*L` (Quadrat: `(-15, 35+L) -> (-15,35)`).
- Der kompensierte Werkzeugmittelpunkt folgt damit stetig: `dive -> P` (G40), dann
  `P -> A + offset_dir*r` (Maschinenkompensation der nominalen Linie), dann
  `A + offset_dir*r -> S + normal*r` (kompensierter Bogen, Radius `R_w - r`), dann die Kontur –
  **kein Sprung**, da `offset_dir*r` für Linie und Bogen identisch ist (`= tangent*r`).

## Offener Detailpunkt (mit Empfehlung, klein)
Länge `L` der G40-Geraden. **Empfehlung:** `L = lead_length` (common length), konsistent zur
Gerade-Einfahrt. Beim Implementieren mit Vorschau/G-Code verifizieren.

## Änderungen

1. `core/leadmove.py`
   - Kleine Hilfsfunktion zum Versetzen der **ersten** Einfahrts-Linie um den Werkzeugradius:
     Eingabe: die nominalen Lead-in-Geos (Linie+…), `side`, `r`; Ausgabe: die G40-Gerade
     `LineGeo(dive, P)` (siehe Geometrie). Keine Änderung an den nominalen Lead-in-Geos selbst.
   - Alternativ: die Versatz-/Dive-Berechnung direkt in `stmove` (siehe 2.), `leadmove` bleibt dann
     unverändert.
2. `core/stmove.py` (Zweig `cut_cor in (41,42)`)
   - **Kreis/Startmove:** nominalen Lead-in wie jetzt (`SPACE_NOMINAL`, `start`,`angle`) bauen;
     zusätzlich die **G40-Gerade** (versetzt) erzeugen.
     - `self.lead_in_geos` = `[*G40-Gerade, *nominale_Geos]` (zusammenhängend, für die Vorschau).
     - Neu: `self.lead_in_nominal_index` = `len(G40-Gerade)` (Split für den G-Code).
   - **Gerade:** unverändert (`SPACE_TOOL_CENTER`, offset-tangentiale Linie); `lead_in_nominal_index`
     = `len(lead_in_geos)` (kein nominaler Teil).
   - `self.geos` (Vorschau-Toolpath) weiterhin `[RapidPos(dive), *G40-Gerade]`.
3. `core/shape.py` (`Write_GCode`, Maschinenkompensation, `not Drill`)
   - `g40_geos = lead_in_geos[:lead_in_nominal_index]`, `nominal_geos = lead_in_geos[lead_in_nominal_index:]`.
   - **G40-Abschnitt (`g40_geos`) vor/nach dem Eintauchen** schreiben wie heute für die Gerade
     (`cc_outside_the_piece`: `True` -> vor dem Eintauchen „in der Luft", `False` -> nach dem
     Eintauchen).
   - Danach `set_cut_cor(self.cut_cor)`.
   - Danach – **nur für Kreis/Startmove** – die **nominalen** Geos (`nominal_geos`) schreiben, dann die Kontur.
   - Gerade: `nominal_geos` ist leer -> nach `set_cut_cor` direkt die Kontur (unverändert).
   - Prüfen, dass `nominal_geos` **nicht** zusätzlich in `new_geos`/`pass_geos` landen
     (keine doppelte Kompensation).
4. `gui/canvas2d.py`
   - Keine Strukturänderung nötig: `_lead_in_path` wird aus `geos[1:1+len(lead_in_geos)]` gebaut und
     enthält damit G40-Gerade **und** nominale Geos. Werkzeugkreis am Eintauchpunkt
     (`_lead_in_path.elementAt(0)`), Farbe/Breite/Strich unverändert.
5. Tests/Goldens
   - Goldens `g41_lead_in_radius`, `g41_lead_in_straight`(kontrollieren, darf sich nicht ändern),
     `g42_closed` sowie betroffene `g41_*` regenerieren und inhaltlich prüfen.
   - Tests anpassen/ergänzen: `dxf2gcode_leadmove_modes_test.py`, `_function_test.py`,
     `_startpoint_test.py`.

## Regressionstests (neu/erweitert) – mit geometrischen Asserts
Für Kreis-Lead-in, je Fall:
- **G41 und G42**; **offene und geschlossene** Kontur; **beide Konturseiten** (Konturrichtung/CW-CCW);
- verschiedene **Werkzeugradien** `r` und **Lead-in-Radien** `R_w`; beide `cc_outside_the_piece`.
Prüfen:
- Eintauchpunkt `dive` = `Q + offset_dir*r + normal*L` (Versatz = `r` neben der nominalen Linie);
- seitlicher Versatz des Dives zur nominalen Linie == `r`;
- G40/G41/G42-Umschaltpunkt = `P = Q + offset_dir*r`, G41 steht **nach** dem Eintauchen und **vor**
  der nominalen Linie; G40-Abschnitt steht **vor** G41;
- Bogen: Radius `R_w` **im G-Code** (nominal), Mittelpunkt `C`, kompensiert `R_w - r` um `C`;
- Tangentialität: nominale Linie tangential am Bogen (`d == arc tangent at A`), Bogen tangential an
  der Kontur bei `S`;
- Werkzeugmittelpunktbahn unter G40 = Gerade `dive->P` (parallel/versetzt zur nominalen Linie);
  nominale Bahn nach G41 = Linie+nominaler Bogen.
- **Gerade-Einfahrt unverändert**: Golden `g41_lead_in_straight` byte-gleich; vorhandene
  Straight-/Software-Tests grün.

## Validierung
- G-Code-Inspektion wie oben (Quadrat G41/G42) – Reihenfolge, Versatz, Bogenradius, kein Sprung.
- Vorschau rendern und mit dem Referenzbild vergleichen (Kreis = versetzte Linie + nominaler Bogen).
- Volle Testsuite: `python -m unittest discover -s tests -t tests -p "dxf2gcode_*test.py"` grün.

## Randbedingungen / Hinweise
- Keine doppelte Radiuskorrektur: unter G40 rechnet dxf2gcode den Versatz, unter G41/G42 liefert es
  die nominale Geometrie.
- Der Übergang Eintauchen -> G41 -> nominale Linie muss der Steuerung genug Bewegung zum Aufbau geben
  (die nominale Linie dient als Aufbauzug).
- Umsetzung erfordert Quellcode-Edits: dafür in einen implementationsfähigen Agent wechseln.
