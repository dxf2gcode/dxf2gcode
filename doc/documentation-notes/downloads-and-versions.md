# Downloads und Versionen – Redaktionsmaterial

Stand: **02.11.2026**, CI1, nächste stabile Zielversion **2.0.0**.

Für Installation und Developer Guide (WP2 / WP11–WP12) die
[Release-Pipeline](../release-pipeline.md) als technische Grundlage verwenden.
Die Anwenderanleitung soll vor allem diese Entscheidungen erklären:

- Stabile GitHub-Releases und ausdrücklich gekennzeichnete Develop-Previews
  unterscheiden. `2.0.0.devN` ist eine Entwicklerversion, kein fertiges 2.0.0.
- Develop-Releases werden bewusst manuell über **Actions → Full regression
  tests → Run workflow → develop** gestartet. Normale Pushes und PRs prüfen
  weiterhin automatisch, veröffentlichen aber kein Release. Stabile Releases
  bleiben an passende Versionstags gebunden.
- Release-Beschreibungen enthalten eine kurze Zusammenfassung der jeweiligen
  Versionslinie statt einer Commitliste. Die gepflegten Texte unter
  `doc/release-notes/` vor künftigen Veröffentlichungen aktualisieren.
  Für 2.0 umfasst die Zusammenfassung die Arbeiten seit dem SourceForge-Merge
  `f5520a8` vom 11.10.2026, nicht nur seit dem letzten Develop-Paket.
- 2.0 als neue Entwicklungslinie erklären: getrennte Code-Verantwortlichkeiten,
  gemeinsamer Werkzeugwegplan, erweiterte Bearbeitung und geänderte Parameter-
  bedeutungen mit Migration. Der GitHub-Umzug ergänzt dies durch neue
  Entwicklungs-, Prüf-, Download- und Dokumentationsabläufe. Ein Hostingwechsel
  allein ist kein technischer Grund für einen Major-Sprung. Alte interne
  Importpfade sind entfernt; daraus keine pauschale Unverträglichkeit alter
  Zeichnungen oder Projekte ableiten.
- Beim portablen Windows-Paket das gesamte ZIP entpacken. Der MSI installiert
  für den aktuellen Benutzer; Develop und Stable verwenden getrennte Ordner.
- Die ersten Windows-x64-Pakete verwenden Python 3.11 / PyQt5 und sind
  unsigniert. Eine Anleitung darf keine vorhandene Signatur behaupten.
- Wheel-Datei und virtuelle Umgebung verwenden. Ältere Datumsversionen
  sortieren höher als 2.0.0; für den Umstieg eine frische Umgebung oder eine
  ausdrücklich gewählte Wheel-Datei vorsehen.
- Download-Herkunft anhand `release-manifest.json`, Dateiname und Infofenster
  erklären; `SHA256SUMS` dient zur Kontrolle der übertragenen Dateien.
- Develop behält zehn erfolgreiche Stände, PR-Testpakete sieben Tage;
  stabile Releases bleiben erhalten. Links aus dem README übernehmen.

CI-Prüfungen ersetzen weder die gesonderte Debian-/Zielrechner-Abnahme M1
noch eine physische Maschinenabnahme. Screenshots und Installationsschritte
bei der späteren Dokumenterstellung am dann aktuellen Paket überprüfen.
