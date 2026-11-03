# Reihenfolge, Bearbeitung und Vorschau (WP3–WP5)

Stand: **03.11.2026**. Englische Kapitel im [User Guide](../../docs/user-guide/shapes-layers-and-order.md).
Anwendungsbasis `6c4bcc9`; keine Quellcodeänderungen. Neue eigene Zeichnung
und zwei Widget-Aufnahmen: [Herkunft und Werte](../../docs/assets/examples/machining-basics/README.txt).

## WP3: maßgebliche Verträge

- [TreeHandler](../../source/dxf2gcode/presentation/qt/treehandling.py):
  `updateExportOrder`, `updateTreeViewOrder`, `prepareExportOrderUpdate`.
  Baumfolge gilt auch bei deaktivierter Live-Routenanzeige.
- [Routenanwendung](../../source/dxf2gcode/application/optimization/routes.py):
  ORDER_ONLY verschiebt alle gerouteten Konturen ans Ende in Routenfolge;
  PLACE_AFTER verschiebt nur freigegebene Konturen. Andere Zeilen behalten
  relative Ordnung. Keine festen absoluten Plätze zusagen.
- [Exportordnungs-Verträge](../../tests/dxf2gcode_export_order_test.py):
  normale/optimierte GUI- und CLI-Folge, Custom-G-Code und deaktivierte Zeilen.
  Die Buchstaben-Tabelle nimmt B,A,C als vorgeschlagene Route an und zeigt
  deren deterministische Anwendung; sie ist kein aufgezeichneter TSP-Lauf.

## WP4: maßgebliche Verträge

- [Anwendungsaktionen](../../source/dxf2gcode/application/shapes.py) und
  [Werkzeuge](../../source/dxf2gcode/domain/project/tool_settings.py):
  ganze Layer neu zuweisen löscht Kontur-Werkzeugoverrides; gleiche Toolnummer
  an einer einzelnen Kontur ist kein allgemeiner Reset. Numerische graue
  Standardwerte nicht mit dynamischer Vererbung gleichsetzen.
- [Modusregeln](../../source/dxf2gcode/domain/project/machining.py),
  [Kontextmenü](../../source/dxf2gcode/presentation/qt/canvas.py) und
  [Modustests](../../tests/dxf2gcode_machining_modes_test.py): Tasche nur bei
  geschlossener Auswahl/Softwarekompensation; Bohren bei geschlossenen
  Arc-Konturen. Konflikte erhalten und gezielt auflösen.
- [Tiefen](../../source/dxf2gcode/domain/toolpath/depths.py) und
  [Konturstrategie](../../source/dxf2gcode/domain/toolpath/strategies/contour.py):
  letzte Zustellung begrenzen; Bohrwiederholung bleibt profilabhängig.
- [Parameterzustände](../../tests/dxf2gcode_parameter_state_test.py):
  Different/Unavailable, graue editierbare Vorgaben und gemischte Auswahl.

## WP5: maßgebliche Verträge

- [Lead-Geometrie](../../source/dxf2gcode/domain/toolpath/leadmove.py),
  [Vorbereitung](../../source/dxf2gcode/domain/toolpath/stmove.py),
  [Planer](../../source/dxf2gcode/domain/toolpath/planner.py) und
  [Diagnosen](../../source/dxf2gcode/domain/toolpath/diagnostics.py).
  G41/G42 als Software-Seitenwahl führt zur geometrischen Kompensation in G40;
  Maschinenkompensation benötigt Einfahrbewegung. Arc-Radius am Werkstück
  von Mittelpunktbahn unterscheiden; Überfahrt läuft auf geschlossener Kontur.
- [2D-Projektion](../../source/dxf2gcode/presentation/qt/canvas2d.py),
  [Vorschauadapter](../../source/dxf2gcode/adapters/toolpath/preview.py) und
  [Vorschau-Verträge](../../tests/dxf2gcode_toolpath_preview_test.py):
  gleicher Planvertrag, aber abhängig vom tatsächlich verwendeten Profil.
  Orange Eintritt, magenta Austritt, blaue Bahn; nicht auf 3D-Farben übertragen.
- [Offsetstatus](../../tests/dxf2gcode_offset_status_test.py): erwartetes
  Verschwinden von Rechenfehlern/unklarem Ergebnis unterscheiden.

Für WP6 Schleppmesser und Haltestege vertiefen; für WP8/WP9 konkrete
Konfigurations- und Profilfelder erläutern. Keine Maschinenverträglichkeit
oder Materialparameter aus den Illustrationswerten ableiten.
