# Builds und Downloads (CI1)

Zielversion ist **2.0.0**. Entwicklerversionen folgen PEP 440:
`2.0.0.dev<GitHub-Runnummer>`. Ein bewusst gesetzter Tag `v2.0.0` erstellt
die stabile Version `2.0.0`; der Tag muss zur Basisversion in
`source/dxf2gcode/_version.py` passen. Anschließend die Basisversion vor
weiteren Entwicklerversionen erhöhen. Es gibt keine automatische stabile
Veröffentlichung aus einem Develop-Push.

## Ablauf

`.github/workflows/full-tests.yml` führt die bestehende Vollsuite mit Python
3.11/3.12/3.13 und PyQt5 sowie Python 3.11 und PyQt6 aus. Danach entstehen aus
demselben Commit Quellarchiv und Wheel. Die Quellen werden außerhalb des
Checkouts bereitgestellt; nur dort wird die Paketversion eingesetzt. Das
Wheel entsteht aus dem Quellarchiv ohne Git und wird in frischen Qt5- und
Qt6-Umgebungen einschließlich DXF-Export geprüft.

Windows x64 verwendet Python 3.11, PyQt5 und cx_Freeze. Die fixierte
Build-Basis steht in `requirements-release.txt` und dem Workflow. Das geprüfte
Quellarchiv liefert die EXE samt Laufzeitdateien als ZIP sowie einen
benutzerbezogenen MSI-Installer. Der Windows-Runner prüft Herkunft,
Übersetzungen, Plattform-Plugin, einen echten GUI-Start und DXF-Export sowohl
aus dem ZIP als auch nach einer MSI-Installation. Die Testinstallation wird
anschließend entfernt. Diese Prüfung gehört ausschließlich auf einen
wegwerfbaren Runner; `tests/verify_windows.py` installiert Software.

PRs liefern ausschließlich Actions-Artefakte für sieben Tage. Bei Push auf
`develop` veröffentlicht der abschließende Job ein Prerelease, wenn alle
Prüfungen erfolgreich waren und `CI_RELEASES_ENABLED=true` gesetzt ist.
`workflow_dispatch` veröffentlicht nichts. Veröffentlichungsrechte bestehen
nur im abschließenden Job und nur im Hauptrepository. Ein bereits überholter
Develop-Commit wird nicht mehr veröffentlicht.

Zunächst entsteht ein Draft. Erst wenn alle Dateien hochgeladen und deren
Namen, Größen sowie verfügbare GitHub-Prüfsummen geprüft sind, wird er sichtbar.
Fehler lassen den vorherigen Download stehen. Ein eigener veröffentlichter
Release bleibt bei Wiederholung unverändert; ein unterbrochener eigener
Draft kann erneut befüllt werden.

## Version und Herkunft

`release-manifest.json` enthält vollständigen Commit, Commitdatum,
Workflow-Run, Paketversion, MSI-Version und Signierungsstatus. Die eingebettete
Build-Herkunft bleibt über Quellarchiv, Wheel und Windows-Paket erhalten.
ZIP/MSI-Dateinamen enthalten Version, Datum und kurze Commitkennung. Das Wheel
trägt Datum und Commit im gültigen Wheel-Build-Tag. `SHA256SUMS` enthält die
SHA-256-Werte aller Download-Dateien außer sich selbst.

MSI erlaubt keine Prerelease-Suffixe und höchstens `255.255.65535`:

| Paketversion | MSI ProductVersion | Kanal |
| --- | --- | --- |
| `2.0.0.dev123` | `2.0.123` | Develop |
| `2.0.0` | `2.0.0` | Stable |

Beide Kanäle haben eigene Upgrade-IDs und Installationsordner. Buildnummern
werden niemals abgeschnitten oder umgebrochen; bei Überschreiten der Grenze
stoppt der Build und die Zuordnung muss bewusst angepasst werden.
Alte Datumsversionen sortieren bei Python höher als `2.0.0`: zum Umstieg eine
frische Umgebung oder die ausdrücklich gewählte Wheel-Datei verwenden.

## Aufbewahrung und Betrieb

Develop-Tags heißen `develop-ci-<Run-ID>`; Prereleases werden nie „Latest“.
Nach erfolgreicher Veröffentlichung bleiben die letzten **zehn** eigenen
Develop-Releases erhalten. Bereinigt werden nur veröffentlichte Prereleases
mit passendem Tag, vollständiger Commitkennung und eigenem Herkunftsmarker.
Vor Löschen eines Tags wird dessen Commit nochmals geprüft. Stabile Releases,
fremde Previews und Drafts werden nicht bereinigt. Stabile Releases werden
dauerhaft aufbewahrt und als „Latest“ markiert.

Nach erfolgreicher Veröffentlichung werden die doppelten Actions-Paketkopien
genau dieses Runs entfernt. PR-Pakete und fehlgeschlagene Runs verfallen nach
sieben Tagen. Es werden keine Build-Caches angelegt. Vor Aktivierung am
02.11.2026 geprüft: öffentliches Repository, Organisation GitHub Free,
zwei bestehende Actions-Artefakte mit zusammen 1.163.538 Bytes, keine Releases.
Öffentliche Standard-Runner sind laut GitHub kostenlos; die Free-Organisation
weist 500 MB enthaltenen Actions-Artefaktspeicher aus. Speicherverbrauch und
Tarif bei Änderungen erneut prüfen; dies ist keine unbegrenzte Speicherzusage.

Windows-Pakete sind zunächst ausdrücklich **unsigned**. Eine spätere
Codesignierung benötigt ein separat bereitgestelltes Zertifikat und sichere
CI-Zugangsdaten. Dann EXE/DLL vor dem MSI-Build und MSI vor der ZIP-/Prüfsummen-
und Veröffentlichungsstufe signieren und verifizieren. Der aktuelle Workflow
behauptet keine Signatur und benötigt keine Signierungssecrets.

Aktivierung: Repositoryvariable `CI_RELEASES_ENABLED=true`. Zum Anhalten
öffentlicher Veröffentlichungen diese Variable auf `false` setzen; Tests und
Paketprüfungen laufen weiter. Ein stabiler Tag wird erst bewusst nach Prüfung
gesetzt und gepusht. M1 (gesonderte Paket-/Debian-Abnahme) bleibt unabhängig.

## Referenzen

- [SemVer](https://semver.org/lang/de/) und
  [Python-Versionen](https://packaging.python.org/en/latest/specifications/version-specifiers/)
- [MSI ProductVersion](https://learn.microsoft.com/windows/win32/msi/productversion)
- [cx_Freeze MSI](https://cx-freeze.readthedocs.io/en/stable/bdist_msi.html)
- [GitHub Releases API](https://docs.github.com/en/rest/releases/releases)
- [GitHub Actions Abrechnung](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
