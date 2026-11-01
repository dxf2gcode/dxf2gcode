# Rights and attribution review

Reviewed for the local prototype on 2026-11-01. This record documents the
available evidence and unresolved publication conditions. **No blanket
republication license has been established for the SourceForge wiki or its
contributed attachments. No SourceForge text or attachment is embedded in the
prototype site.**

## Evidence examined

- The repository's `LICENSE` and `source/COPYING` contain GNU GPL version 3.
  That is evidence for the software's licensing, not an asset-by-asset grant
  for separately contributed wiki material.
- The 15 original wiki texts, API metadata, page histories and attachment
  metadata have been inspected. No explicit blanket wiki-content license or
  image-specific reuse grant was found in those texts. Mentions of software
  licensing in release notes and dependency filenames do not supply one.
- [Slashdot Media terms, sections 9 and 10](https://slashdotmedia.com/terms-of-use/)
  distinguish hosted content and code. Section 9 grants rights to the hosting
  company and states that contributors retain ownership. It is not evidence
  of a general GPL or Creative Commons grant to this documentation project.
  Current terms alone also do not establish which terms governed old uploads.
- The retrieved terms and project-summary HTML are preserved under
  `snapshot/phase1-complete/rights/`, with hashes in the manifest.

## Attribution evidence

The retrieved page-history tables name these editors:

| Pages | Editors observed |
| --- | --- |
| Home; General Configuration; GIT Workflow; User Guide | `christi_ko` |
| China Laser Cutter, DXF, Lathe and Python postprocessor examples | `christi_ko` |
| Styrofoam example; Postprocessor Configuration | `christi_ko`, anonymous |
| DevelopmentEnvironment_Win7 | `christi_ko`, `jp1357`, anonymous |
| Installation | `christi_ko`, `dwrobel`, `jp1357`, `treki`, anonymous |
| ImportExport | anonymous |
| LayerControl | `rli`, anonymous |
| Release notes | `dwrobel`, `jp1357`, anonymous |

These are observed editors, not a complete authorship determination. Older
revisions, imported contributions and third-party sources may require further
review. The per-page URLs and observations are recorded in the manifest.

## Publication decisions still needed

| Material | Current finding | Required before public reuse |
| --- | --- | --- |
| Wiki prose and page screenshots | Separate grant not found | Confirm ownership / applicable license and retain attribution; otherwise write a new explanation from verified facts |
| `git-model@2x_red.png` | Uploaded by `christi_ko`; this does not establish rights to the underlying Git-flow diagram | Trace the original diagram and any modifications, check license and required credit |
| Panel-cutout DXFs and screenshots | Uploaded by `glasairman` and `bob2718281`; the discussion refers to a manufacturer's drawing | Confirm rights to redistribute both the drawing and modifications |
| LayerControl Google Drive DXF | Downloaded successfully; owner/license not established | Confirm origin and permission |
| External `Spant.png` | Missing (HTTP 404); author/license not established | Find an authorized original or create a clearly identified replacement later |
| Discussions and `alternate` HTML mail attachments | Some contain addresses, phone numbers and quoted emails | Keep raw preservation private; extract useful technical knowledge only after privacy and rights review |

No messages requesting permission have been sent to contributors or maintainers.
No publication approval is inferred from an attachment being publicly downloadable.

## Material used in the prototype

The four English prototype pages are newly written from the checked-out
repository's README, source README and inspected application behavior. They
do not import wiki paragraphs, screenshots or contributed machine profiles.
The baseline commit is `a982969591868595b2d9729917bf92b766b5ec05`.
The later installation page was checked against package metadata and build
helpers, with official Python, Qt and Ubuntu references. This adds no license
grant for archived wiki material. The final local technical and user-performed
visual acceptance is recorded in [Phase-1 acceptance](../zensical-prototype.md).

The initially reused project logo has now been replaced at the user's request.
The following identifies the earlier asset for historical reference:

- Original: `source/dxf2gcode/presentation/qt/resources/images/dxf2gcode_logo.png`
- Copy: `docs/assets/images/dxf2gcode_logo.png`
- SHA-256: `6c17c71d376f7e013741a954c841fe2abaff5baf1354a4aec3e10ea8c8214bd7`
- These copies were byte-identical at initial acceptance, before replacement.
- Repository history records edits by Jean-Paul Schouwstra and a later move
  by `christi_ko`. These commits do not by themselves prove original authorship.

No separate logo license or original-artist notice was identified. Local
prototype use is authorized by the user; confirm the project's redistribution
rights before publishing the website. No new documentation license has been
assigned to the imported archive or assumed for third-party assets.

### Supplied replacement and project-use authorization, 2026-11-01

The user states that they designed the old logo themselves, but are unsure
about its rights. They now request replacement by a new logo they are creating
with GPT assistance and report that it contains no design components made by
others. The user subsequently supplied `dxf2gcode-logo-v3.svg` and
`dxf2gcode-logo-v3.png` and expressly asked to replace the logo everywhere and
include it on GitHub. This records reported authorship and permission for public
project use, not a blanket license or a guarantee of exclusive rights to GPT output.

Static inspection found SVG geometry, styles, title and description, with no
scripts, text/font dependency, external links or embedded image. The supplied
PNG loads as 4096 x 1300. File inspection does not independently prove authorship;
the provenance statement is the user's declaration.

| Supplied source | SHA-256 | Repository use |
| --- | --- | --- |
| `dxf2gcode-logo-v3.png` | `bd226aea55080191e843c709b225fc6d142b5ad7afadd33c916067cc51b81039` | Unchanged bytes at `docs/assets/images/dxf2gcode_logo.png` |
| `dxf2gcode-logo-v3.svg` | `933001cd5106bbebcebfe74f5dac3dc4dc285300f4d8cc357d640d0d0acb8419` | Unchanged bytes at `source/dxf2gcode/presentation/qt/resources/images/dxf2gcode-logo.svg` |

Application-branding working-tree changes are a separate follow-up. The latest
refresh retains the aspect-preserving 492 x 157 wordmark PNG for About and
README, but uses the user's dedicated square symbol for the 256 x 256 ICO,
512 x 512 ICNS and Linux SVG. The ICO's version-free name is `dxf2gcode.ico`.
Existing Qt encoders were used; no dependency was installed or new artwork
generated. The documentation copy remains the original supplied PNG. Both
supplied formats are retained in the repository for the GitHub handover.

The old-logo question is superseded for this replacement by the supplied design
and user's project-use request. Wiki/third-party content rights are unchanged.
No new blanket branding license has been assigned. The logo/header need a short
visual check before deployment. Commit, push and deployment still have the
separate status recorded in the handover report.

### Latest supplied symbol and stable source names

The user placed the latest wordmark and icon files in the application resource
directory and requested replacement and filenames without version numbers.
Wordmark sources are now `dxf2gcode-logo.png` / `.svg`; symbol sources are
`dxf2gcode-symbol.png` / `.svg`. The supplied symbol PNG is 512 x 512 with
SHA-256 `baa9b5a3032a3889d1a3234d3b9379d72639c0ba4a8091773c5ff8b190402392`;
its SVG has SHA-256
`0b6936714f4d23437722d2e2d09a07d7008fcd2e9009d283716c8c441442af5d`.
SVG inspection found only geometry/title/description and no external references,
scripts or text/font dependency. The documentation symbol PNG is copied
unchanged; application icon formats are derived with existing Qt encoders.
Historical source names above are provenance records, not active file paths.
This refresh does not alter the recorded user authorship/project-use request
or assign a new general license. Visual acceptance of this new icon remains open.
