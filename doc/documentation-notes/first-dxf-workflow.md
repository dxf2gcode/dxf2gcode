# WP1 – Erste DXF bis zum G-Code

Stand: **03.11.2026**. Grundlage für WP2–WP7 und spätere Überarbeitungen.

Das neue englische Kapitel liegt unter
`docs/getting-started/first-dxf-to-gcode.md`. Beispiel, Rechte, Screenshot-
Umgebung und Exportnachweis sind in
[README.txt](../../docs/assets/examples/first-dxf/README.txt) festgehalten.
Alle Inhalte und Medien sind neu für das Projekt erstellt, keine Übernahme
aus dem alten Wiki. Der Entwurf liegt auf `docs/wiki-migration`.

## Begriffe und Zusammenhänge beibehalten

- Auswahl dient der Bearbeitung; Enable-Checkboxen bestimmen den Export.
  Die leeren Felder im unselektierten Importbild sind beabsichtigt.
- Anwendungsprofil `wp1-demo` und Postprozessor `postpro_config.cfg` sind
  unterschiedliche Dinge. Das neu erzeugte Anwendungsprofil startet mit
  Standardwerten, nicht als Kopie einer vorhandenen Maschinenkonfiguration.
- G40 fährt die Werkzeugmitte auf der Zeichnung; das 20 × 10-mm-Rechteck
  verspricht deshalb kein entsprechendes Fertigmaß nach Fräserradius.
- Infeed −0,5 mm und Endtiefe −1 mm erzeugen zwei Tiefenumläufe. Die 2D-
  Darstellung legt deren XY-Bahnen übereinander; der Werkzeugkreis ist nur
  eine Eintrittsanzeige, keine zusätzliche Kreisbewegung.
- Rückzug und Sicherheitsabstand gelten am Layer; Schnitttiefen und Vorschübe
  können je Kontur eingestellt werden. Im Beispiel stehen Rückzug und
  Sicherheitsabstand auf den Standardwerten 15 mm und 3 mm.
- Normaler Export folgt den aktivierten Konturen in Baumreihenfolge. Die
  Optimierung und Routenanzeige sind getrennte Bedienhandlungen.
- Das Default-Format „G-CODE for LinuxCNC“ enthält auch T1/M6, Spindel- und
  Kühlmittelbefehle. Keine allgemeine Steuerungs- oder Maschinenfreigabe
  aus der Darstellung oder aus dem erfolgreichen Dateiexport ableiten.

Der finale GUI-Dateiexport wurde im isolierten Profil verfolgt; die
Bewegungswerte passen zum Kapitel. Das ist keine Paket- oder Maschinenabnahme.
Installation bleibt im eigenen Kapitel; fortgeschrittene Kompensation,
Taschenfräsen, Schleppmesser und Werkzeugwechsel bleiben spätere Arbeitspakete.
