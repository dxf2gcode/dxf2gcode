# Redaktionsnotizen: Schleppmesser

Zuordnung: **WP6 – Tabs and Machine Modes**. Stand: **02.11.2026**.

Die aktuelle Bedienungsgrundlage steht in [drag-knife-usage.md](../drag-knife-usage.md).
Der [abgestimmte D1/D2-Plan](../drag-knife-plan.md) enthält Entscheidungen,
Geometrieanforderungen und historische Prüfstände. Diese Texte als Grundlage
verwenden, statt aus alten Screenshots eine zweite Anleitung abzuleiten.

## In der Anleitung erklären und bebildern

- Einheitlicher Ablauf ohne Freischalter „Geplante Messerschnitte“.
  Lead-in/Lead-out „Keine“ und ausgeschaltete Überfahrt lassen diese Zusatzwege weg.
- Endtiefe und Slice-Tiefe wiederverwenden: Oberfläche 0, Zustellung −0,1 mm
  und Endtiefe −0,3 mm ergeben drei Tiefenschnitte. Schwenk-Kontakthöhe Z ist
  davon getrennt und darf nie tiefer als der aktuelle Schnitt liegen.
- Globale Schwenkhöhe und eigener Konturwert unterscheiden. Ein leeres
  Konturfeld verwendet wieder die Konfigurationsvorgabe.
- Senkrechtes Eintauchen gegenüber XYZ-Rampe erklären. Automatischer
  Rampenausgleich, Überfahrt und optional ein zusätzlicher vollständiger
  Endtiefenschnitt sind unterschiedliche Funktionen.
- Geschlossene Umläufe laufen kontinuierlich; offene Konturen können mit
  Rückkehr oder externer Umkehr über gerade Leads bearbeitet werden.
- Lead-Auswahl, Werkzeug-Lead-Länge, separate Messer-Auslauflänge und
  Lead-Radius zusammen zeigen. Originalkontur, Messerspitzenbahn und
  Werkzeughalterbahn unterscheiden; der Offset ist kein Fräserradius.
- Messerstellung „Startwinkel“, „letzten Winkel beibehalten“ und „unbekannt“
  gegenüberstellen. Die externe Ausrichtstrecke ist keine Winkelmessung und
  benötigt eine am Messer und Material geprüfte Länge und freien Anfahrraum.
- Konfiguration 9.18 / Projektformat 1.5: frühere Slice-Schwenktiefen werden
  migriert; unterschiedliche Konturwerte bleiben erhalten. Bereits aktive
  D1/D2-Einstellungen aus den Vorgängerversionen behalten ihre Bedeutung.

## Quellen und Beispielmaterial

- Erich Styger, [Optimized Vinyl Cutting G-Code Tool Path with DXF2GCODE](https://mcuoneclipse.com/2021/07/06/optimized-g-code-tool-path-for-vinyl-cutting-with-dxf2gcode/),
  MCU on Eclipse, 06.07.2021. Als weiterführenden Link und fachliche Referenz
  verwenden. Alte UI-Anweisungen und Durchmesser-/Offsetkonvention abgleichen;
  Shapeoko-/Carbide-Motion-Anpassungen nicht als allgemeine Vorgaben darstellen.
- [Dragknife issue, Mai 2022](https://www.ltspiceusers.ch/threads/dragknife-issue.1126/):
  historische Referenz für Entlastung vor dem abschließenden Messerschwenk.
  Die lokale [Test-DXF](../../dxf/drag_knive_test.dxf) stammt aus dem verlinkten
  Commit `0178408`; sie ist nicht mit der heutigen `dxf/test.dxf` gleichzusetzen.
- [Forumsbericht zum Konturschluss](https://www.ltspiceusers.ch/threads/overcut-with-drag-knife-vinyl-cutter.2247/):
  Hintergrund für D1. Einen gemeldeten Reststeg nicht ungeprüft als heutigen
  Softwarefehler oder als Beleg einer bestimmten Ursache beschreiben.

Für die Dokumentation ein eigenes kleines Beispiel mit einer offenen und einer
geschlossenen Kontur erstellen. Artikeltexte, Bilder und fremde DXFs benötigen
vor Übernahme eine Rechteprüfung. Softwaretests ersetzen keinen Materialversuch.
