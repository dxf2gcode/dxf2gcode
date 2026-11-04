# Releases and downloads

Use [GitHub Releases](https://github.com/dxf2gcode/dxf2gcode/releases) for current
project downloads. Choose the actual release entry and read its channel,
description and included files. This documentation does not hard-code a moving
“latest” preview or imply that the target stable version has already shipped.

## Stable versus Develop

The next stable target is **2.0.0**. A version such as `2.0.0.dev123` is a
development preview, not stable 2.0.0. The stable release is deferred until the
entire active Todo has been completed. Documentation publication is independent
of that release decision.

The 2.0 line includes reorganized code responsibilities, a shared planning basis
for preview/export, expanded machining options and changed parameter meanings
with migrations. The move to GitHub adds the repository, testing, release and
documentation workflows; a hosting move alone is not the technical version change.

Develop previews are published manually through **Actions → Publish release →
Run workflow** on develop, after checks. Ordinary pushes and PRs run tests/package
checks but do not create a release. Stable releases use matching semantic-version
tags. The published preview number is separate from the GitHub workflow run number.

## Choose an artifact

| Artifact | Intended use |
| --- | --- |
| Windows x64 portable ZIP | Extract the entire archive and start `dxf2gcode.exe` |
| Windows MSI | Per-user install; Develop and stable channels are separated |
| Python wheel | Install the selected file in a suitable virtual environment |
| Source archive | Source package and build inputs; not a preinstalled runtime |
| `SHA256SUMS` | Check transferred file bytes |
| `release-manifest.json` | Version, revision, run identity, MSI mapping and signing status |

Initial Windows packages use Python 3.11 / PyQt5 and are unsigned. Do not assume
a valid publisher signature. The manifest identifies that state. A checksum
helps detect corruption or a mismatched download; it is not an independent
publisher-signature mechanism.

For a wheel, use `python -m pip install ACTUAL_WHEEL_FILE.whl` in a virtual
environment. Old date-based versions sort above 2.0.0 under Python version
ordering. Use a fresh environment or explicitly select the chosen wheel when
migrating, rather than assuming an unqualified upgrade chooses it.

## Linux installer and older releases

The separate [Linux Installer](https://github.com/dxf2gcode/dxf2gcode_installer)
offers a script-based path for Debian/Ubuntu/Mint and Arch-based distributions.
Its README defines its own support and development status. Use its issue tracker
for script failures; it is not the Windows MSI installer.

The [SourceForge archive](https://sourceforge.net/projects/dxf2gcode/files/)
retains older releases and development candidates. Their requirements and
interfaces can differ. Read their descriptions instead of treating every old
download as a stable release matching this development guide.

## Retention and provenance

The automated policy retains the ten most recent successful owned Develop
releases. Stable releases are retained. Temporary PR/failed-run Actions packages
expire after seven days; duplicate Actions copies for a successful published
run are removed after publication. Release assets and Actions artifacts are
different copies with different retention rules.

Keep the release manifest and compare revision/version with the application's
About information when reporting a package problem. Exact current rules and
build stages are in the [pipeline reference](../developer/packaging.md).
Package/platform acceptance and physical-machine acceptance remain separate.
