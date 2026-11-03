# SourceForge wiki migration: phase 2 plan

**Planning only, 2026-11-01.** The accepted four-page Zensical site is a technical
prototype, not the completed manual. No chapters or machine profiles below have
been implemented by writing this plan. See [Phase-1 acceptance](zensical-prototype.md)
for its scope and proposed commit. This plan is outside the public `docs_dir`.

**Progress, 2026-11-03:** WP1 and WP2 are implemented on
`docs/wiki-migration`: the first-export walkthrough, Interface and Navigation,
and Import Drawings and Save Projects. WP2 reuses WP1's newly authored rectangle
and current screenshots. See [WP1 evidence](../archive/toolpath-refactoring-completed.md#doc1-wp1)
and [WP2 evidence](../archive/toolpath-refactoring-completed.md#doc1-wp2).
Commit `5cee4ad` was merged into `develop` through
[PR #1](https://github.com/dxf2gcode/dxf2gcode/pull/1) (`39351f8`). The user
authorized publication; Pages build/deploy
[41712224311](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41712224311)
succeeded, and both WP2 chapter URLs returned HTTP 200 with the expected titles.
WP3–WP5 have also been authored locally on `docs/user-guide-wp3-wp5`, with
seven pages, an original three-shape example and two current 2D captures.
See [completion evidence](../archive/toolpath-refactoring-completed.md#doc1-wp3-wp5).
WP6–WP8 have now been added on the same local branch: tabs/breaking layers,
machine modes, drag-knife cutting, command-line usage, troubleshooting,
application settings and layer naming. See
[WP6–WP8 evidence](../archive/toolpath-refactoring-completed.md#doc1-wp6-wp8).
The user has authorized committing, integration and publication of WP3–WP8
for a first review. The public Introduction prototype is removed; website
maintenance instructions have moved out of the public navigation into
`doc/documentation-notes/documentation-site-maintenance.md`. Installation and
linked example drawings remain available. Deployment evidence is recorded in
the completion log. WP9–WP13 below remain plans, not implemented chapters.

## Baseline, evidence and publication gates

- Source baseline: the local `docs/zensical-prototype` checkout, based on
  `a982969591868595b2d9729917bf92b766b5ec05`. Code, configuration declarations,
  tests and technical documentation were read; tests were not run for planning.
- Historical source: the 15 latest public pages in
  [manifest.json](sourceforge/manifest.json), with original Markdown, API data,
  rendered HTML, observed history editors and attachment provenance. See
  [snapshot scope](sourceforge/README.md) and [rights review](sourceforge/RIGHTS.md).
  This is not an export of every revision, orphan attachment or deleted page.
- 23 of 24 discovered media/attachment files are saved. `Spant.png` is missing
  (recorded HTTP 404). The Google Drive DXF and four HTML mail attachments were
  saved; their download does not establish redistribution rights.
- Application configuration currently declares 9.16, reading 9.11 through 9.16;
  the wiki describes 9.8. Postprocessor configuration declares 8.2, reading 8,
  8.1 and 8.2; wiki reference/examples use 4 through 7. Recheck these at the
  implementation baseline. Never migrate a profile just by changing its version.
- Original wiki prose/media stay outside the public site until rights and
  technical accuracy are cleared. Where rights remain unknown, write new text
  from verified behavior; preserve the original privately. Historical pages
  also require rights clearance before public reproduction.
- Repo file paths below are relative to the repository root. They are evidence
  pointers, not an assertion that every feature has been tested on a machine.
  Existing regression tests describe expected cases, not universal acceptance.

## Complete wiki-to-target matrix

Priorities: **P1** first user workflows; **P2** configuration/postprocessors;
**P3** developers and historical reference. **Archived** means a local source
copy exists, not permission to republish. All original reuse remains subject
to the rights gate. Exact source URLs and local paths are in the manifest.

| SourceForge wiki page | New documentation page(s) | Required changes | Priority | Status |
| --- | --- | --- | --- | --- |
| Home | Home / Project Overview; Support; Historical Documentation | Replace wiki index with task-based entry points; preserve source URL mapping | P1 | Archived; brief new Home exists in prototype |
| Installation | Getting Started / Installation, platform sections and Run from Source | Replace old Python/Qt dependencies and removed setup scripts; distinguish released packages from develop; no unverified macOS commands | P1 | Archived; current Windows/Ubuntu source setup exists as prototype, not clean-install acceptance |
| User Guide DXF2GCODE | First DXF to G-code; Interface; Import and Projects; Shapes and Tree Order; Machining; Preview/Export; CLI; FAQ | Split long page; verify labels and selection vs enabled state; replace mandatory-xvfb claim for supported headless exports; preserve screenshots separately | P1 | Archived; Introduction exists, full guide pending; screenshot rights pending |
| ImportExport | Import Drawings and Save Projects; Configuration / Layer Naming; Developer Architecture | Recheck supported input paths, entity chaining, tolerances and spline approximation; update old package paths and drilling statements | P1 | Archived; behavior rewrite pending |
| LayerControl | User Guide / Tabs; Machining Parameters; Configuration / Layer Naming Rules | Correct no-project-saving claim; verify prefixes, aliases, separator, signed depths, ignore filtering and per-pass tab behavior | P1/P2 | Archived; external illustration missing; example rights pending |
| General Configuration | Configuration / Application Settings; Layer Naming Rules; User troubleshooting | Replace 9.8 reference with current schema; profile locations, defaults, override precedence and errors must match code | P2 | Archived; current reference pending |
| Postprocessor Configuration | Postprocessor Reference; Tool Changes and Macros; Examples index | Replace version-4 reference; check all sections/placeholders, units, modal state and machine/software compensation; add managed macro contract | P2 | Archived; new reference pending |
| Postprocessor-Example China Laser Cutter | Postprocessor Examples / Laser Cutter; Historical Documentation | Preserve original privately; version 4, typo/copy-path issues and laser switching/arc assumptions need review; do not claim controller certification | P2 | Archived; rights and controller assumptions unresolved |
| Postprocessor-Example Styrofoam | Postprocessor Examples / Hot-wire / Styrofoam; Historical Documentation | Review version 4, omitted Z moves and heat enable/disable ordering; declare controller assumptions | P2 | Archived; rights and current-profile validation pending |
| Postprocessor-Example Lathe | User Guide / Machine Modes; Postprocessor Examples / Lathe | Review version 6, axis mapping, plane and radius/diameter scaling against current dialect; distinguish machine mode from profile | P2 | Archived; technical and rights review pending |
| Postprocessor-Example DXF | Postprocessor Examples / DXF Output | Review version 7, output type/format, number formatting and exported entities; no unsupported round-trip promise | P2 | Archived; technical and rights review pending |
| Postprocessor-Example Python | Postprocessor Examples / Python Output | Review version 5 and generated text semantics; do not present this historical output example as a supported Python API | P2 | Archived; technical and rights review pending |
| DevelopmentEnvironment_Win7 | Developer Guide / Setup; Qt Resources and Translations; Packaging; Historical Documentation | Archive Python2/PyQt4/old-PyInstaller instructions as history; author current checkout workflow from build helpers | P3 | Archived; replacement pending |
| GIT Workflow in dxf2gcode | Developer Guide / Contributing; Documentation Maintenance; Historical Documentation | Reconcile current contribution guidance and branch policy; diagram uploader is not proof of underlying diagram rights | P3 | Archived; workflow rewrite and diagram rights pending |
| Release notes | Project / Releases and Downloads; Historical Documentation | Retain dated history after clearance; 2017 must not be advertised as current latest release; distinguish planned CI releases from real downloads | P3 | Archived; current release links need verification; original prose reuse pending |

## Recommended navigation and URL ownership

Use the requested groups, with two scope changes: keep Installation as **one
canonical page** with Windows, Linux/Ubuntu, macOS status and Run from Source
sections; add **Machine Modes** for milling, lathe and drag knife. Split platform
pages only when verified content justifies it. At present macOS gets a clear
unverified-status note, not invented installer or package-manager commands.

```text
Home
  Project Overview
Getting Started
  Installation (Windows; Linux/Ubuntu; macOS status; Run from Source)
  First DXF to G-code
User Guide
  Interface and Navigation
  Import Drawings and Save Projects
  Shapes, Layers and Tree Order
  Machining Parameters
  Contours, Pockets and Drilling
  Machine Modes (Milling; Lathe; Drag Knife)
  Cutter Compensation and Lead Moves
  Tabs / Breaking Layers
  Route Optimization
  Preview and Export
  Command-line Usage
  Troubleshooting and FAQ
Configuration
  Application Settings
  Layer Naming Rules
  Postprocessor Reference
  Tool Changes and Macros
  Postprocessor Examples
    Laser Cutter
    Hot-wire / Styrofoam
    Lathe
    DXF Output
    Python Output
Developer Guide
  Development Setup
  Architecture
  Tests
  Qt Resources and Translations
  Packaging and Builds
  Contributing
  Documentation Maintenance (includes local Documentation Preview)
Project
  Releases and Downloads
  Support and Issue Reporting
  License and Credits
  Historical Documentation
```

Keep `index.md` and `installation.md` as the current canonical URLs initially.
The introductory workflow moves into First DXF / Overview only after approval;
retain a link/alias for `introduction/`. Preserve `documentation-preview/` when
placing it under Developer Guide in navigation. New content can use
`getting-started/`, `user-guide/`, `configuration/`, `developer-guide/` and
`project/` folders. Do not activate empty placeholder pages in navigation.

Before moving/splitting a page, record old SourceForge URL + fragment, old
prototype URL, target Markdown path + fragment, disposition and media paths in
a URL map. Convert wiki shorthand/absolute internal links to relative links.
Retain explicit anchors where needed. New-site aliases cannot redirect an old
SourceForge URL by themselves; a SourceForge change needs a separate approval.

New content not adequately covered by the old wiki includes the first workflow,
project persistence, manual/export/optimized ordering, per-shape tools and
overrides, machining conflicts, diagnostics, machine modes, managed tool-change
contracts, genuinely headless exports, current architecture, tests, modern
packaging/provenance and documentation maintenance. These are drafting topics,
not new capabilities promised by this plan.

## One source of truth

- `source/pyproject.toml` owns declared dependencies and console entry points.
  `source/tools/build/` and `Makefile` own executable build behavior. Link to
  current technical details; do not copy old setup scripts into the manual.
- Application/profile schemas in `adapters/config/runtime_config.py` and
  `adapters/postprocessor/postprocessorconfig.py` own supported values and
  defaults. Reference tables must record their reviewed code baseline.
- `source/README.md` and `doc/architecture.md` supply architecture/build context;
  `tests/README.md` and `CONTRIBUTING.md` supply contribution/test guidance.
  Public English summaries link to those maintained sources. If authoritative
  text is moved later, replace its old location with a link in the same approved
  change instead of maintaining conflicting copies.
- `doc/tool-change-macros.md` is the current detailed macro source; its older
  proposal is design history. Translate/check the implemented contract before
  publishing an English reference, then establish one canonical version.
- `doc/todo.md` describes pending work, not available features. Current CI/hook
  changes are local and unrelated to this migration; never describe a planned
  release pipeline or proposed workflow as already deployed.

## Work packages and review gates

Every package inherits these checks: reviewed code revision and source list;
English text; rights/privacy clearance for each reused asset; current relative
links and anchors; `zensical build --strict`; search index limited to intended
pages; user-only visual review when appearance changes. Record actual commands
executed separately from static checks. Existing tests can be inspected without
running them. Any needed application execution, fresh installation or longer
test/build must be proposed and authorized separately; this plan authorizes none.

### WP0: provenance and URL ledger (cross-cutting prerequisite)

- **Pages:** migration ledger and Project / License and Credits, Historical
  Documentation outline; ledger stays outside public `docs/` until reviewed.
- **Sources / analysis:** all 15 snapshot texts, API/history metadata, current
  manifest and RIGHTS; distinguish editor, uploader, author and underlying rights.
- **Media:** account for all 24 references, including the four HTML mail bodies;
  retain originals/checksums, never embed mail HTML or contact details. Find an
  authorized `Spant.png` original or propose a new diagram; no silent replacement.
- **Questions:** what licenses/permissions apply, which contributors can supply
  evidence, and which historical material is worth public reproduction?
- **Acceptance:** every page/media item has a target or explicit private/missing
  disposition; no unknown-license material enters public content. This gate runs
  alongside user-first drafting; it must not prevent independently authored text.

### WP1: First DXF to G-code

- **Pages:** `getting-started/first-dxf-to-gcode.md`, small links from Home and
  Introduction; existing Installation remains canonical and unchanged in scope.
- **Sources / analysis:** `docs/installation.md`, source README;
  `application/importing.py`, `application/drawings.py`, `application/exporting.py`,
  `presentation/qt/application.py` and `treehandling.py`; inspect
  `tests/dxf2gcode_mainwindow_workflow_test.py` and `dxf2gcode_export_order_test.py`.
  Trace import, units/origin, enabled shapes, parameters, preview and normal export.
- **Media/examples:** propose a newly authored 20 x 10 mm closed rectangle DXF
  under documentation assets, with author/license/units recorded. It is not yet
  created. Use new screenshots only after scope and capture are approved; no
  third-party panel-cutout drawing. Specify the profile and assumptions, not a
  universally suitable CNC program. No real machine execution is an acceptance step.
- **Questions:** approve example units/geometry and a named demonstration profile;
  choose a normal G40 milling contour for the first walkthrough, leaving advanced
  compensation, pockets and automatic tool changes to linked follow-up chapters.
- **Acceptance:** each step names an actual UI action and expected visible result;
  enabled/selected state and ordinary export order are distinct. File paths and
  download links resolve; parameters have units and are labelled illustrative.
  Trace one export only if separately authorized and record the exact environment.

### WP2: interface, import and projects

- **Pages:** Interface and Navigation; Import Drawings and Save Projects.
- **Sources / analysis:** User Guide + ImportExport originals; `application/projects.py`,
  `application/drawings.py`, `adapters/dxf/reader.py`, `adapters/project/legacy_d2g.py`
  and `file_store.py`; inspect project-adapter and import-contract/chain tests.
  Check DXF linking/tolerances, optional converters, `.d2g` drawing references,
  project reload behavior and compatibility; do not equate project save to export.
- **Media/examples:** reviewed original overview/menu screenshots or newly captured
  ones with provenance; example project uses the approved drawing from WP1.
- **Questions:** which UI language/version do screenshots represent, and which
  reload changes must users expect? Determine limits from code/tests, not old FAQs.
- **Acceptance:** documented formats match current paths; selection vs enablement,
  drawing vs project vs machine output and reload limitations are explained.

### WP3: tree order and route optimization

- **Pages:** Shapes, Layers and Tree Order; Route Optimization.
- **Sources / analysis:** User Guide, `treehandling.py:updateExportOrder`,
  `application/optimization/routes.py`, `tsp.py`, `application/cli_export.py` and
  export-order/treeview tests. Trace `exp_order` and `exp_order_complete`, custom
  G-code rows, disabled shapes and both `TSP_shape_order` modes.
- **Media/examples:** three newly authored labelled shapes with before/after order
  tables; a reviewed screenshot can supplement the textual order example.
- **Questions:** verify constraints and CustomGCode placement for each mode; never
  imply fixed absolute slots when only relative order is retained. Cross-layer
  drag/drop is not promised merely because its future design is in Todo.
- **Acceptance:** manual order, ordinary export, route display and optimize/export
  have separate descriptions; the before/after sequence agrees with current code
  and test expectations. GUI/CLI differences or limitations are explicit.

### WP4: machining parameters, contours, pockets and drilling

- **Pages:** Machining Parameters; Contours, Pockets and Drilling.
- **Sources / analysis:** LayerControl/User Guide; `domain/project/tool_settings.py`,
  `machining.py`, `application/shapes.py`, `domain/toolpath/depths.py`, pocket
  planners and parameter-state/machining-mode/pocket tests. Trace units, signed
  depths, passes, tool dimensions, layer defaults and per-shape overrides.
- **Media/examples:** new simple open/closed contours and a drill/pocket example;
  no imported design without provenance.
- **Questions:** recheck pocket eligibility and the effect of mode transitions;
  loaded drilling/pocket/compensation conflicts must not be silently normalized.
- **Acceptance:** show inherited vs overridden values and their reset behavior;
  drill/G40 transitions and blocking `machining.conflict` diagnostics match code.
  Numbers in examples have units and do not imply a material-specific recipe.

### WP5: compensation, lead moves, preview and diagnostics

- **Pages:** Cutter Compensation and Lead Moves; Preview and Export;
  diagnostic entries linked from Troubleshooting.
- **Sources / analysis:** User Guide; planner, leadmove and shapeoffset modules,
  `application/toolpath/`, `adapters/toolpath/preview.py`, canvas2d/3d and exporter;
  inspect leadmove, overcut, offset-status and toolpath-preview tests/goldens.
- **Media/examples:** newly captured current 2D preview and a simple lead example;
  keep original geometry, offset and lead/start/end colors distinguishable.
- **Questions:** distinguish machine vs software compensation, open vs closed
  contour and lead/overcut applicability; do not infer 3D colors from 2D colors.
- **Acceptance:** one setting has consistent preview/export explanation;
  warnings, unsupported cases and source geometry vs tool motion are explicit.
  A preview is not proof of controller compatibility.

### WP6: tabs and machine modes

- **Pages:** Tabs / Breaking Layers; Machine Modes.
- **Sources / analysis:** LayerControl; `domain/project/layercontent.py`,
  `application/shapes.py:SetShapeBreakPass`, `adapters/postprocessor/breaks.py`,
  drag-knife strategy, lathe formatting in `dialect.py`; inspect breaks-pass,
  slices and drag-knife tests/goldens.
- **Additional drag-knife tutorial (added 2026-11-02):** Erich Styger,
  [Optimized Vinyl Cutting G-Code Tool Path with DXF2GCODE](https://mcuoneclipse.com/2021/07/06/optimized-g-code-tool-path-for-vinyl-cutting-with-dxf2gcode/),
  MCU on Eclipse, 2021-07-06. Use as a reference and further-reading link for
  the future Drag Knife section: blade offset, corner swivels, tool assignment,
  cutting depth and feed, and a practical star-shaped vinyl-cutting example.
  Recheck its historical UI instructions and especially the diameter versus
  blade-offset convention against the current implementation. Shapeoko/Carbide
  Motion postprocessor changes are machine-specific examples, not defaults.
  The comment reporting an incomplete cut at the contour closure also provides
  historical context for D1; it does not establish the current cause. Draft
  current instructions from verified behavior; reuse of article text, images
  or example files requires a separate rights review.
- **Existing regression reference (added 2026-11-02):**
  [Dragknife issue, May 2022](https://www.ltspiceusers.ch/threads/dragknife-issue.1126/)
  and local `dxf/drag_knive_test.dxf`, added by the thread's linked commit
  `0178408`. The historically fixed issue concerns lifting to swivel depth
  before the final swivel, with the corresponding Z/XY feed changes. Use the
  [D1/D2 test plan](../drag-knife-plan.md#vorhandene-forums-testdatei-abschließender-messerschwenk)
  for current verification; do not present the historical defect as current
  or publish the fixture merely because it is available as a local test.
- **Media/examples:** own tab-height/pass diagram and simple mode examples;
  missing `Spant.png` stays an explicit gap until replacement is approved.
- **Questions:** default vs explicit per-pass tabs, sign/depth meaning, lathe
  axis/radius/diameter conventions and drag-knife closure behavior need separate
  confirmation. Do not advertise deferred Todo fixes as implemented.
- **Acceptance:** tabs are distinguished from disabling a shape; machine mode
  and postprocessor choice are separate; each mode's documented limitations
  have an identified implementation/test source.

### WP7: command-line usage and troubleshooting

- **Pages:** Command-line Usage; Troubleshooting and FAQ.
- **Sources / analysis:** current argument parser in `presentation/qt/application.py`,
  headless DXF/project export functions, `application/cli_export.py`, configuration
  profile selection and error handling; User Guide's historical xvfb text is context.
- **Media/examples:** reproducible commands using the approved drawing and profile;
  text output is preferable to screenshots. Optional PDF/PS paths are separate.
- **Questions:** exact options, output/error behavior, config-suffix persistence
  and whether any documented case still initializes a GUI require path-specific review.
- **Acceptance:** commands refer to real flags/files, distinguish code inspection
  from execution, and do not claim the old virtual-display workaround is universally
  necessary. Bugs go to GitHub Issues; usage questions to the existing forum.

### WP8: application settings and layer naming

- **Pages:** Application Settings; Layer Naming Rules.
- **Sources / analysis:** General Configuration + LayerControl; runtime schema,
  configuration store, `layercontent.py`, import filters and config-layering/
  tree-config tests. Extract current sections, supported versions, default profile
  location, named profiles, separators/aliases and override precedence.
- **Media/examples:** reviewed config dialog screenshots; new short layer-name
  examples with expected parsed values. No blind positive-depth copy from the wiki.
- **Questions:** distinguish IGNORE layer disabling from optional import filtering;
  identify supported profile upgrade/rejection behavior instead of advising deletion.
- **Acceptance:** table keys/defaults and example parsing match the current schema;
  precedence and compatibility errors are explained with reviewed evidence.

### WP9: postprocessor reference and tool changes

- **Pages:** Postprocessor Reference; Tool Changes and Macros; Examples index.
- **Sources / analysis:** wiki reference; `postprocessorconfig.py`, `dialect.py`,
  adapter/application tool-change modules and `doc/tool-change-macros.md`;
  inspect postpro-config, dialect and tool-change tests/goldens.
- **Media/examples:** new annotated, minimal configuration snippets; distinguish
  legacy `Program.tool_change` from an explicitly managed return-state contract.
- **Questions:** controller/work-offset/length-offset assumptions, M6 handling,
  available placeholders, CustomGCode restrictions and supported machine modes
  must be verified individually. Generic macros are not controller guarantees.
- **Acceptance:** cover supported 8/8.1/8.2 profiles, first/effective-tool-change
  behavior, same-tool suppression, scalar references, G90/G91 and return state.
  Current German implementation notes and English reference must not diverge.

### WP10: five postprocessor examples (five independent review slices)

- **Pages:** Laser Cutter; Hot-wire / Styrofoam; Lathe; DXF Output; Python Output.
- **Sources / analysis:** each corresponding saved wiki page, current schema,
  dialect/exporter and relevant tests. No tracked `.cfg` profile collection was
  found in the inspected checkout; do not invent one or imply these are shipped
  validated profiles.
- **Media/examples:** preserve original files locally; publish only cleared
  originals as historical downloads or newly authored, validated examples.
- **Questions:** identify a concrete controller/dialect for laser/hot-wire/lathe,
  safe switching order, arc support, axis mapping and expected output semantics.
  Without these answers, mark an example unavailable or historical, not recommended.
- **Acceptance:** review each example separately for rights, loading, output
  format, movement semantics and explicit limits. Record any separately authorized
  export comparison. Successful config loading is not CNC-machine validation.

### WP11: developer setup, architecture and tests

- **Pages:** Development Setup; Architecture; Tests.
- **Sources / analysis:** source README, `doc/architecture.md`, tests README,
  bootstrap/domain/application/adapters/presentation code and architecture tests.
  Compare current boundaries with planned refactors; old Win7 setup is history.
- **Media/examples:** new dependency diagram based on actual imports; link to
  repository examples and test sources rather than copying licensed papers.
- **Questions:** what is a supported public API, and which remaining Qt/global
  dependencies must be disclosed? Declared Python minima differ from verified setups.
- **Acceptance:** paths/imports exist; planning, preview and serialization stay
  distinct; focused/fast/full test scopes are explained without running the suite.

### WP12: Qt, translations, packaging and maintenance

- **Pages:** Qt Resources and Translations; Packaging and Builds; Contributing;
  Documentation Maintenance, reusing Documentation Preview.
- **Sources / analysis:** `source/pyproject.toml`, `Makefile`, `tools/build/`,
  package manifests, wheel-verification code, CONTRIBUTING, AGENTS and current
  workflow files. Check committed vs local-only workflow state after integration.
- **Media/examples:** verified commands and expected generated paths; no generated
  UI/QM files, packages or private snapshot become website source assets.
- **Questions:** release-asset preparation vs ordinary startup; dependency locking,
  tool discovery, provenance, versioning and test hook integration.
- **Acceptance:** compile-only vs TS-update workflows are separate; package entry
  points and both-Qt preparation requirements are accurate. No new build/release
  execution or CI changes are authorized by this documentation package.

### WP13: project pages and publication readiness

- **Pages:** Releases and Downloads; Support and Issue Reporting; License and
  Credits; Historical Documentation. Update Home's authoritative links.
- **Sources / analysis:** README, actual release destinations and source revisions,
  RIGHTS/manifest and completed URL ledger. Release notes remain dated history.
- **Media/examples:** only cleared historical downloads and authorized branding.
  The user supplied a newly designed, GPT-assisted v3 SVG/PNG and requested
  replacement throughout the project. The assets and provenance are prepared
  locally; visual acceptance and GitHub publication approval remain separate.
  Do not publish the old logo or raw discussion archive.
- **Questions:** confirm public GitHub/forum reachability, stable/development
  documentation policy, canonical URL, asset rights and approved deployment branch.
- **Acceptance:** no fabricated/latest download, unresolved public-content rights
  or local/private paths; all intended links and asset provenance accounted for.
  A public `site_url` and Pages workflow are separate approved changes, not part
  of planning or the Phase-1 prototype commit.

## Order, branches and first implementation proposal

1. Review and explicitly approve the Phase-1 candidate commit; keep its 14-path
   list separate from CI/hooks/tests/Todo. Preserve the existing staged hook and
   local changes; no commit, push or integration has occurred in this task.
2. Integrate Phase 1 into `develop` through the separately approved Git workflow.
   The planning document may travel with the prototype, but it is not migration
   implementation. Only then create `docs/wiki-migration` from updated `develop`.
   Do not switch/rebase a dirty checkout blindly; isolate ongoing local work.
3. Start WP0's ledger and request approval for **WP1 only**: one new English
   walkthrough, a newly authored example input, necessary navigation links and
   small provenance entries. Keep the accepted Phase-1 branding and Installation intact.
4. Complete user packages WP2-WP7 in order, with one cohesive slice per review.
   WP8-WP10 then cover configuration and profiles; WP11-WP12 cover developers.
   WP13 assembles the project/publication view, while rights tracking continues
   throughout. Project license/credits skeletons may precede their final review.
5. Record code evidence, remaining gaps and technical vs visual acceptance for
   every slice. A merge or screenshot approval never authorizes a CNC test,
   installation matrix, commit, push or publication by implication.

**First request after integration:** approve WP1's scope, example and profile
assumptions. It can be independently reviewed without waiting for old screenshot
permissions. If an application dry export is desired, propose that narrow check
separately with an isolated config/output path; otherwise label the walkthrough
as code-reviewed until that check has actually been executed.
