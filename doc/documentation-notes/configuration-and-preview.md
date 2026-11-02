# Redaktionsnotizen: Konfiguration und Vorschau

Zuordnung: **WP3 sowie WP8–WP10**. Stand: **02.11.2026**.

## Profile und Parameternamen

Ein neues Profil beginnt mit den Werkseinstellungen und kopiert nicht das aktive
Profil. Dialogfelder zeigen die geladenen Werte; Tooltips nennen die Vorgabe für
neue Profile. Eine veränderte Menüauswahl oder ein geladenes Projekt kann für die
aktuelle Zeichnung andere Werte verwenden. Unabhängige Konfigurationsänderungen
setzen diese Auswahl nicht zurück.

Für Beispiele folgende Vorgaben des dokumentierten Stands berücksichtigen:

| Einstellung | Neues Profil |
| --- | --- |
| Deaktivierte Konturen anzeigen | Ein |
| Exportroute live aktualisieren | Aus |
| Importierte Liniensegmente teilen | Aus |
| Automatische Fräsradienkompensation | Aus |
| Maschinentyp | Fräsen (`milling`) |

Die Seite **Parameternamen** definiert die zulässigen Bezeichner in DXF-Layern.
Mehrere Namen pro Parameter werden durch Kommas getrennt. Die kurzen Feldtexte
werden durch Tooltips ergänzt; Beschreibungen zu veralteten Bezeichnern und
numerischen Lead-Modi beim Überfahren der Felder erläutern. Nicht die frühere
Seitenbezeichnung „Automatische Werkzeugkonfiguration“ als aktuelle UI zeigen.

## Übernehmen und Neustart

- Maschinentyp: wird auf die aktuelle Zeichnung angewendet und für neue
  Sitzungen gespeichert. Der vorhandene Maschinenwechsel baut die Darstellung
  neu auf und erhält Kontureinstellungen.
- Importtoleranzen: wirken über vollständiges Neuladen der Zeichnung. Werden
  Maschinentyp und Toleranzen gemeinsam geändert, genügt ein vollständiger Lauf.
- Einheiten: werden unmittelbar umgerechnet; dafür ist kein Neustart nötig.
- 2D/3D-Modus und Protokollierung: nach Übernehmen erscheint ein Hinweis.
  Nach Bestätigung und Schließen der Konfiguration startet das Programm mit
  leerem Fenster neu. Zeichnung und ungespeicherte Bearbeitungswerte werden
  ausdrücklich nicht wiederhergestellt. Ein fehlgeschlagener Prozessstart lässt
  das aktuelle Fenster geöffnet; zurückgenommene Änderungen heben den Neustart auf.
- Konfigurationsprofile werden vollständig beim Programmstart geladen. Den
  separaten Profilwechsel-Hinweis nicht mit sofort wirksamen Einstellungen
  innerhalb des aktiven Profils verwechseln.

## Darstellung für Abbildungen

Die Originalkontur bleibt Geometrie- und Auswahlgrundlage. Die Werkzeugwegvorschau
verwendet den gemeinsamen Plan mit dem Export; 2D fasst deckungsgleiche Tiefenwege
zusammen, während 3D die Tiefenbewegungen erhält. Lead-in, Lead-out und Überfahrt
werden in 2D über den Konturbahnen gezeichnet. Eine manuell angezeigte Exportroute
ist eine eigene Aktion und wird nicht durch eine Vorschau-Neuberechnung aktiviert.

Die noch offene Aufgabe **V1** (Werkzeugkreis unabhängig vom Lead-in) nicht als
vorhandene Anzeigeoption dokumentieren. Vor Screenshots die aktuelle Bedienung
und Begriffe in den gepflegten Sprachen abgleichen. Prüfnachweise stehen in
[completed](../archive/toolpath-refactoring-completed.md#configuration-restart).
