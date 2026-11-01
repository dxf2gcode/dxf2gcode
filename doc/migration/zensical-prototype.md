# Zensical documentation: publication and migration handover

## Current Pages publication status (2026-11-01)

**Live development documentation:** <https://dxf2gcode.github.io/dxf2gcode/>.
The user explicitly approved integration, Pages activation/publication and
replacement of an empty GitHub Wiki. This section supersedes all earlier
preparation and authorization gates preserved below.

### Integration and acceptance

- `origin/develop` was `e2ceed4`; `origin/docs/zensical-prototype` was `2186f79`.
  The complete 34-path diff matched the approved documentation, branding,
  resource and workflow packages. Develop was fast-forwarded without conflicts;
  every existing commit was retained. No rebase, force-push or history rewrite.
- [e4beb1e](https://github.com/dxf2gcode/dxf2gcode/commit/e4beb1e)
  adds the prominent README documentation link, corrects the outdated claim
  that no publishing workflow exists, records the canonical project URL and
  restricts the prepared manual publishing workflow to `develop`.
- Local checks rerun on the integrated tree: **149 fast tests per Qt binding**,
  Qt5/Qt6 resource loading and compiled DE/FR/RU About translations, strict
  Zensical build, 167 generated-site references, four sitemap URLs and 18 search
  entries. The required PyQt5 fast hook runs before each new local commit.
- [Full integration matrix](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41329328147)
  passed all four Ubuntu jobs: Python 3.11/3.12/3.13 with PyQt5 and Python 3.11
  with PyQt6. [Documentation checks](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41329328253)
  passed on the same integrated commit. No full local suite or installer build
  was started.

### Pages configuration and live verification

- Pages uses **GitHub Actions**, `build_type=workflow`, with HTTPS enforced at
  the exact `/dxf2gcode/` project URL. No custom domain was configured.
- Following the user's automatic-publication request, `documentation-pages.yml`
  now publishes website changes pushed or merged into `develop`, after its
  strict documentation build succeeds. The path filter includes `docs/**`
  (including branding), `zensical.toml`, `requirements-docs.txt` and the Pages
  workflow itself. Manual dispatch still requires `publish=true`; both triggers
  require `DOCS_PREVIEW_PUBLISH_APPROVED=true`, the correct repository and
  `refs/heads/develop`. Pull requests do not deploy. The workflow change takes
  effect once committed and pushed to GitHub.
- The new `github-pages` environment permits only the `develop` branch.
  Build permissions remain `contents: read` / `pages: read`; deployment alone
  gets `pages: write` and `id-token: write`. Other repository rules and secrets
  were not changed.
- [First Pages deployment](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41329699445)
  passed both build and deploy jobs, publishing `e4beb1e`. The subsequent
  handover-only update changes this report/TODO, not website content.
- Direct HTTPS checks passed for **all four pages**, **159 references** and
  **11 distinct live resources**: navigation and active page links, internal
  anchors, canonical URLs, wordmark/header image, favicon, sitemap and search
  data/worker. Image/favicon bytes match the supplied assets. The earlier
  167-reference local check additionally included the generated 404 page.
- The **actual deployed search worker and index** were executed in a Node VM
  using the website's real message protocol, without a browser or new dependency.
  `postprocessor` returned **four results**, including the introduction's
  drawings/output and basic-workflow anchors. Every result target was checked.
  This is functional/HTTP verification, not a new visual browser acceptance.

### GitHub Wiki and repository links

Before deactivation the public `/wiki` address redirected to the repository
root, and the separate `.wiki.git` repository did not exist. Both checks were
repeated before changing the setting: no own Wiki pages/history were found to
back up. HTTP response evidence was saved locally. A Python certificate-chain
failure during the repeat HTML fetch was resolved using Windows' normal
certificate-verifying HTTPS client; TLS verification was never disabled.

Only after successful live Pages/search acceptance was **`has_wiki=false`** set.
The repository website now points to <https://dxf2gcode.github.io/dxf2gcode/>.
There were no active links to the old GitHub Wiki to replace. Historical
SourceForge download/wiki references remain; no SourceForge settings or content
were changed. Unreviewed wiki snapshots, third-party text/media and contributed
attachments are not site content or Git additions.

### Resume work after publication

Continue from the published `develop` branch. The prototype branch remains a
historical review branch; do not recommit the old `.tox/docs-handoff/` indexes.
Local preview and strict-build commands are unchanged (see below and
[Documentation preview](../../docs/documentation-preview.md)). Publication
evidence and request/response logs are ignored under `.tox/pages-publication/`.

For a future website update: commit/review and push the docs changes to develop.
**Development documentation preview** automatically builds and publishes
matching website changes. A local commit alone is insufficient. Manual dispatch
with `publish=true` remains available for republishing without a new commit.
Do not rebuild or redispatch merely because this handover-only report changed.

The next content task is to create `docs/wiki-migration` from current develop
and implement [WP1: First DXF to G-code](wiki-migration-plan.md#wp1-first-dxf-to-g-code),
following the [full migration plan](wiki-migration-plan.md). No Phase-2 chapter
was added during publication. Wiki rights, missing `Spant.png`, fresh installation
variants and real CNC/manual/ATC acceptance remain separate open tasks.

## Previous branch-publication handover (historical, before Pages)

The following status describes the preceding repository-publication step.
Its pending Pages approvals/settings are superseded by the live record above.

This section supersedes the historical preparation record below. The user has
explicitly approved the program/CI corrections, thematic commits and normal
pushes to `origin/develop` and `origin/docs/zensical-prototype`. Pages activation
and deployment still require separate approval. No history rewrite is allowed.

- Program commits `5017e16` and `a982969` were retained unchanged.
- `origin/develop` now includes `1907185` (compensation/path tests), `71eb6ac`
  (GitHub About links, DE/FR/RU translations and accurate version documentation),
  `a500df1` (full CI and local fast hook), and `e2ceed4` (isolated CI fixtures).
- The first full CI run exposed three test-fixture issues and failed:
  [41325996649](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41325996649).
  These were corrected without changing production export code. The follow-up
  [41327575137](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41327575137)
  passed all four Ubuntu 24.04 jobs: Python 3.11/3.12/3.13 with PyQt5 and
  Python 3.11 with PyQt6, including native asset/translation generation.
- The documentation branch was fast-forwarded to the CI-accepted develop
  `e2ceed4`. The three reviewed packages were committed separately and pushed
  through `6831a0b`. The [documentation check](https://github.com/dxf2gcode/dxf2gcode/actions/runs/41328175268)
  passed on GitHub. Old candidate HEAD/tree IDs are stale.
- GitHub Pages remains inactive; the API returned 404 and the publication
  approval variable is absent. Nothing has been dispatched or deployed.

### Confirmed publication record

| Target | Commit | Purpose |
| --- | --- | --- |
| develop (also inherited by docs) | [5017e16](https://github.com/dxf2gcode/dxf2gcode/commit/5017e16) | Existing order/optimization and tool-change contracts, unchanged |
| develop (also inherited by docs) | [a982969](https://github.com/dxf2gcode/dxf2gcode/commit/a982969) | Existing translation compilation and compact version display, unchanged |
| develop | [1907185](https://github.com/dxf2gcode/dxf2gcode/commit/1907185) | Explicit compensation fixtures and Qt path assertions |
| develop | [71eb6ac](https://github.com/dxf2gcode/dxf2gcode/commit/71eb6ac) | GitHub About/startup links, translations and version documentation |
| develop | [a500df1](https://github.com/dxf2gcode/dxf2gcode/commit/a500df1) | Full GitHub matrix, local fast hook and CI planning |
| develop | [e2ceed4](https://github.com/dxf2gcode/dxf2gcode/commit/e2ceed4) | Active-binding layout tests and isolated precision/workflow fixtures |
| docs/zensical-prototype | [e2ba4b5](https://github.com/dxf2gcode/dxf2gcode/commit/e2ba4b5) | Four-page Zensical prototype and migration inventory/plan |
| docs/zensical-prototype | [bbc8354](https://github.com/dxf2gcode/dxf2gcode/commit/bbc8354) | Versionless supplied branding and resource references |
| docs/zensical-prototype | [6831a0b](https://github.com/dxf2gcode/dxf2gcode/commit/6831a0b) | Documentation checks, gated manual Pages workflow and DOC1 |

Public branches: [develop](https://github.com/dxf2gcode/dxf2gcode/tree/develop)
and [docs/zensical-prototype](https://github.com/dxf2gcode/dxf2gcode/tree/docs/zensical-prototype).
This record-only update follows those feature commits; identify its own hash
with `git log -1 --oneline`. The documentation/branding changes have **not** been
merged into develop. No pull request, release, Pages activation or deployment
was created. All pushes were normal, without force or history rewrite.

The successful Linux matrix ran **831 tests in each of its four jobs**, including
native UI/resource generation and translation compilation. The separate docs
job installed the existing requirements and passed the strict build.

### Index preservation and local artifacts

Program commits were created in the separate `.tox/publish-program` develop
worktree. Documentation commits used explicit alternate indexes. The only
originally staged file, `.githooks/pre-commit`, was included in the authorized CI
commit with its original blob and executable mode. The original main index and
file hashes were backed up under `.tox/publish-handoff/`; no unknown staged or
working-tree changes were incorporated.

A final status assertion initially compared the committed docs HEAD with the
deliberately retained old main index. It therefore reported misleading deleted
files, and the first docs push was mistakenly allowed to proceed before that
assertion was resolved. The exact three commit path lists were already correct.
A fresh separate HEAD-based index subsequently verified **all working files
match their committed content and no nonignored untracked files exist**, before
the main index was reconciled. The working tree was then clean. No data was
discarded; both earlier index backups remain available.

The old preparation artifacts under `.tox/docs-handoff/` are historical review
data, not instructions to recommit their trees. `.tox` worktrees/logs/indexes,
Qt caches/QM files, local package artifacts and raw wiki snapshots are ignored
and untracked. They were retained locally and excluded from the published trees.

### Changes and evidence

| Area | Scope / evidence |
| --- | --- |
| Application/tests | Original order/optimization and optional tool-change contracts retained; explicit machine/software compensation expectations and state restoration; Qt path checks use `isMoveTo()` |
| CI/translations/About | Full suite on develop pushes and PRs; local fast hook; GitHub project/Issues links; existing forum; compact version documentation; compiled DE/FR/RU catalogs |
| Branding/resources | Versionless supplied wordmark/symbol sources; wordmark in README/Home/About; symbol in icons/header/favicon; Windows ICO and packaged ICNS/Linux SVG |
| Zensical | Four English prototype pages, existing pinned docs dependencies, provenance/rights inventory and 15-page migration plan |
| Docs workflows/TODO | Separate read-only checks and explicitly gated manual Pages workflow; CI1 download planning retained, not implemented |
| Excluded material | Raw wiki snapshots, `.tox` review/test/worktree data, generated UI/RCC/QM, metadata, EXE/MSI/wheel/build outputs; no unknown contribution was added |

Local checks actually executed on Windows/Python 3.11.1:

- Fast suite: **149 tests passed with each of PyQt5 and PyQt6**. Every created
  commit also runs the required PyQt5 pre-commit hook (147 before hook tests
  were introduced, 149 afterwards).
- Focused export/order/lead-move/Golden/dialect/tree/version/provenance checks:
  **326 passed per Qt binding**. Two newly exposed Qt6 test-helper failures
  were corrected and both selections rerun successfully.
- All 17 tool-change tests passed in normal and reversed order, starting with
  both inherited compensation modes: **68 test executions per binding**.
- After the first GitHub failure, **35 affected layout/precision/workflow tests
  passed per binding**. The fast suite was rerun with both bindings.
- Compiled About translations were loaded under both Qt bindings and their
  project/Issues/forum links checked; English source and TS keys agree.
- Qt5 UI/resources generated with the existing helper. Qt6 UI generated with
  PyQt6; existing PyQt5 RCC data adapted to the Qt6 import and actually loaded.
  A native Qt6 RCC is not installed locally; its Linux generation is checked
  by GitHub CI. No new dependencies were installed.
- New resource images, ICO 256x256, ICNS 512x512, SVG content and QRC targets
  checked. Package metadata includes ICNS and the Linux SVG; no dedicated
  macOS application-bundle build configuration exists in this repository.
  No macOS bundle/Windows installer was built or claimed as tested.
- Zensical `--strict` passed; **167 local links/assets/anchors**, four canonical
  sitemap URLs under `/dxf2gcode/`, **18 search entries** and image bytes passed.
  Workflow YAML, event filters, publication gates and least-privilege job
  permissions were inspected. Push/PR cannot trigger the Pages workflow.

The prior four-page visual acceptance remains valid. The refreshed symbol/header
still needs the user's short visual confirmation before deployment. No browser
automation, fresh application installation, local full suite, Debian/SSH,
release/MSI build or real CNC/manual/ATC acceptance was performed. GitHub matrix
results are recorded separately; local tests do not substitute for those runs.

### Remaining publication and migration gates

The prototype contains no archived wiki prose or contributed attachments. The
15 pages and 23/24 media references remain privately preserved, with provenance
in the manifest; `Spant.png` is still missing. Wiki prose, screenshots, DXFs and
third-party graphics require the [rights review](sourceforge/RIGHTS.md) before
reuse. New branding records the user's own-design/GPT-assisted declaration and
public project-use request; no new blanket asset license or exclusive-rights
guarantee has been inferred.

Before Pages: integrate the reviewed docs changes into `develop` with separate
approval, make the manual workflow available there, confirm the project URL,
enable Pages with GitHub Actions, review the `github-pages` environment, and
explicitly approve deployment before setting `DOCS_PREVIEW_PUBLISH_APPROVED` and
dispatching `publish=true`. This task performs none of those settings changes.

### Next steps / Resume work (current)

1. Read this current handover and `doc/todo.md` DOC1; inspect `git status -sb`
   and `git log --oneline --decorate -12` on `docs/zensical-prototype`.
2. Check the latest CI and the recorded publication status before continuing.
   Review artifacts under `.tox/docs-handoff/` and `.tox/publish-handoff/` are
   local aids, not commit sources. Never commit their indexes or raw snapshots.
3. Local preview: `.\.tox\docs\Scripts\python.exe -m zensical serve`.
   Local docs check: the same interpreter with `-m zensical build --strict`.
   The local pre-commit hook runs `python tests/run_tests.py fast` automatically.
   Do not start a full local suite or release build merely to resume work.
4. Obtain the remaining new-branding visual check and separate Pages approval.
5. After review/integration into develop, create `docs/wiki-migration` from the
   updated develop. Start [WP1: First DXF to G-code](wiki-migration-plan.md#wp1-first-dxf-to-g-code),
   then follow the [complete migration plan](wiki-migration-plan.md).

---

## Historical preparation record (superseded status)

The following record preserves the earlier scope, evidence and review gates.
Statements about no commits/pushes, pending authorization, the old base HEAD,
and failed Fast tests describe that earlier stage. The current handover above
and its eventual publication record take precedence.

# Zensical prototype: phase 1 acceptance

## Scope and files

Local branch: `docs/zensical-prototype`, created from `develop` at
`a982969591868595b2d9729917bf92b766b5ec05`. Previously existing working-tree and
staged changes were retained. No application source or existing CI was changed
by this task. No commits, pushes, SourceForge edits or Pages deployment occurred.

**Accepted local prototype, 2026-11-01.** The four pages are a technical
prototype, not the complete dxf2gcode documentation. Phase 2 is planned
separately in [Wiki migration plan](wiki-migration-plan.md); no Phase-2 chapter
has been implemented by preparing that plan.

| File | Purpose |
| --- | --- |
| `zensical.toml` | Native Zensical TOML configuration; four-page navigation, English theme, project logo, system fonts and link checks |
| `requirements-docs.txt` | Separate documentation dependency: Zensical 0.0.74, Python >= 3.11 |
| `docs/index.md` | Brief project overview and explicit development-prototype status |
| `docs/installation.md` | Current source-checkout setup for Windows PowerShell and Ubuntu; PyQt5, PyQt6, Qt tools and translation preparation |
| `docs/introduction.md` | Basic workflow supported by the repository documentation |
| `docs/documentation-preview.md` | Windows setup, preview and strict-build commands |
| `docs/assets/images/dxf2gcode_logo.png` | Unchanged copy of the user-supplied v3 PNG, replacing the initially reused logo |
| `tools/documentation/archive_sourceforge.py` | Read-only wiki/API/media preservation helper, using only the Python standard library |
| `doc/migration/sourceforge/manifest.json` | URL, file, hash, status, link and attribution inventory |
| `doc/migration/sourceforge/README.md` | Snapshot scope, remaining gap and preservation instructions |
| `doc/migration/sourceforge/RIGHTS.md` | Rights evidence and unresolved publication conditions |
| `.gitignore` addition | Prevent raw wiki/discussion snapshots from accidental Git inclusion |

Original wiki material is outside `docs/`, is excluded from Git, and is not
indexed by site search. Existing `doc/` working notes are not automatically
published. The snapshot is not a completed wiki migration.

## Official configuration and dependencies

Configuration follows the official [Zensical basics](https://zensical.org/docs/setup/basics/),
[navigation](https://zensical.org/docs/setup/navigation/),
[logo settings](https://zensical.org/docs/setup/logo-and-icons/) and
[validation](https://zensical.org/docs/setup/validation/) documentation.
The [built-in search](https://zensical.org/docs/setup/search/) is enabled by
default; no Material/MkDocs search plugin is installed.

Tested with Windows, Python 3.11.1, Zensical 0.0.74 and zensical-ui 0.0.41.
The top-level dependency is pinned in `requirements-docs.txt`; transitive
dependencies are resolved by pip, not fully locked. They are independent of
the application's Qt dependencies. Before automated publication, decide on
dependency locking and a supported documentation Python version.

The prepared canonical project-site URL is
`https://dxf2gcode.github.io/dxf2gcode/`, including the repository subpath.
The site title now explicitly says Development Documentation. This prepares
the destination; it does not mean that a site exists or publication is approved.
Generated files go to `.tox/docs-site/`. Two new documentation-only workflow
files have been prepared separately from the 15-path prototype commit; neither
has run on GitHub and no existing CI workflow was edited by this preparation.

## Verification

- `python -m zensical build --strict`: passed, with no issues reported.
- Generated internal page links, anchor targets and local images/assets:
  checked against the built files.
- The supplied v3 PNG, documentation copy and generated-site copy have matching
  hashes. Application branding uses smaller derived images, recorded separately.
- Search index is present and includes the introduction and the word
  `postprocessor`; search JavaScript and worker assets are built locally.
- Website contains no archived wiki pages, discussions or HTML mail attachments.
- The user accepted the installation page, including tables and command
  blocks, with "Darstellung passt". The subsequent whole-site visual checklist
  was accepted with "Alle genannten Punkte passen": logo, navigation and active
  page marking, readability, headings/spacing, command blocks, search with
  result navigation and a narrow browser window. Browser appearance was checked
  by the user only; no automated browser result is claimed.
- Code-copy controls and a light/dark palette toggle are not enabled in the
  current configuration. They are not claimed as tested features.
- Snapshot files and Markdown hashes were verified against the manifest.

The final whole-site check covered **167 local link/asset references** across
the **four content pages** and generated 404 page: **zero missing files or
anchors**. All four pages returned HTTP 200 from the local preview. The search
index contains **18 entries**, referring only to those four pages.

The SourceForge inventory contains **15 wiki pages** and **24 media/attachment
references**; **23 files were saved**. The outstanding `Spant.png` returned HTTP
404 and remains recorded as unavailable. During preservation, all 87 saved
original resources and all 15 extracted Markdown files matched their recorded
hashes. The later acceptance check confirmed the saved files' presence and
sizes. This is a latest-public-content snapshot, not a complete revision or
administrative export.

Installation checks executed in the existing Windows/Python 3.11.1 environment:
PyQt5 selection, fallback to PyQt5 when Qt6 was requested but unavailable,
the source launcher and module entry point with `--help`, translation-helper
`--help`, and syntax parsing of the three PowerShell command blocks. These
passed. Dependency/version declarations, generation commands and package
entry points were also compared with the current repository and official tool
documentation. No fresh application installation, GUI launch, Ubuntu/PyQt6
installation or Python/Qt matrix was performed. Such checks remain separate
work requiring an explicit commission, not tasks delegated to the visual reviewer.

The earlier web fetcher could not verify GitHub/forum targets. A subsequent
authenticated GitHub CLI read confirmed the public `dxf2gcode/dxf2gcode`
repository, `develop` as default branch and ADMIN access for the current user.
The Pages endpoint returned HTTP 404: no existing Pages configuration/site was
available through that endpoint. Forum reachability remains unverified.

No application test suite or release/package build was run for this
documentation-only prototype.

## Run the preview

Full Windows commands are maintained in
[Documentation preview](../../docs/documentation-preview.md). From the repository
root, after setup:

```powershell
& .\.tox\docs\Scripts\python.exe -m zensical serve
```

Open <http://127.0.0.1:8000/>. If an existing preview server is using port 8000,
reuse it or stop it with Ctrl+C before starting another. No activation script
or execution-policy change is needed.

## Exact Phase-1 commit scope

The following **15 paths** are the current positive list for the documentation
commit: 14 prototype/provenance paths and the separately identified Phase-2
plan. The original prototype touched 12 paths. The installation step added
`docs/installation.md` and amended the existing home, introduction and navigation.

```text
.gitignore
zensical.toml
requirements-docs.txt
docs/index.md
docs/introduction.md
docs/installation.md
docs/documentation-preview.md
docs/assets/images/dxf2gcode_logo.png
docs/assets/images/dxf2gcode_symbol.png
tools/documentation/archive_sourceforge.py
doc/migration/zensical-prototype.md
doc/migration/wiki-migration-plan.md
doc/migration/sourceforge/README.md
doc/migration/sourceforge/RIGHTS.md
doc/migration/sourceforge/manifest.json
```

Proposed commit message (not executed):

```text
docs(site): add Zensical prototype and wiki migration plan

Add four English pages, source-checkout setup and local preview guidance.
Record wiki provenance, acceptance results and unresolved publication rights.
Keep unreviewed raw snapshots outside Git and the generated site.
Plan the full migration without implementing its content or publishing.
```

The new `doc/migration/wiki-migration-plan.md` is a planning deliverable included
for a reviewable handover. It does not implement Phase 2 or authorize migration
implementation. It is outside the public site's `docs_dir`.

The default index is left unchanged: `.githooks/pre-commit` was already staged.
Other local CI, hook, test, contribution-guidance and Todo changes must remain
outside this commit. Do not use an unrestricted `git add .` or an ordinary
commit of the current index. An isolated candidate index is prepared under
`.tox/docs-handoff/prototype.index`, with its review diff at
`.tox/docs-handoff/prototype.patch`. It contains only the 15 paths and no commit
has been created. The candidate uses the user's supplied new documentation PNG;
the application-branding follow-up remains separate. Inspect both packages
before public release. Include
the `.gitignore` snapshot exclusion. The
repository's required fast pre-commit check still applies; do not bypass it.

## Next review gate

Review this acceptance record and the positive commit list, then explicitly
approve a Phase-1 commit. No commit, integration or push is implied by visual
acceptance. Only after Phase 1 is integrated into `develop`, create a fresh
`docs/wiki-migration` branch from that updated base. The proposed first content
slice is the [First DXF to G-code work package](wiki-migration-plan.md#wp1-first-dxf-to-g-code).

The [rights findings](sourceforge/RIGHTS.md), missing LayerControl image and
public-link verification remain open. Unclear wiki prose/media are not public
site content. Publication requires the new-logo visual review, confirmed Pages
configuration and separately approved deployment. Prepared workflow files are
not a deployed arrangement.

## GitHub preview preparation and resume work

Status on 2026-11-01:

| Item | Actual status |
| --- | --- |
| Local branch / HEAD | `docs/zensical-prototype` / `a982969` |
| Documentation commit | Candidate only; no commit and no commit hash |
| GitHub branch push | Not performed; no remote `docs/zensical-prototype` was returned by `ls-remote` |
| GitHub develop | Read as `95953b6dc2bf113066729130929ace29ab64f8c0`; ancestor of local HEAD |
| Unpushed ancestry | `5017e16` and `a982969` would also be sent with this branch |
| Pages | Prepared locally only; no deployment or GitHub settings change |
| Logo | User-supplied v3 SVG/PNG applied; provenance recorded; visual check pending |
| Phase 2 | Matrix/navigation/work packages planned; not implemented |

The two existing local commits are the tool-change/order and version/translation
changes; they are not unrelated working-tree edits. They must be included in the
push review. Remote state can change: repeat `ls-remote` and compare ancestry
immediately before any separately approved push. Do not force-push or silently
rebase to conceal the two commits.

Prepared follow-up changes, **outside the 15-path first commit**, are
`.github/workflows/documentation-check.yml`,
`.github/workflows/documentation-pages.yml`, and the appended DOC1 section of
`doc/todo.md`. The existing Todo already contains other uncommitted work; its
whole-file diff must not be swept into the prototype commit. Review this
follow-up independently. The existing unrelated CI/hooks/tests remain untouched.

The user's earlier request to replace branding everywhere initially added a
follow-up package: `README.md` and four existing files under
`source/dxf2gcode/presentation/qt/resources/images/` (`dxf2gcode_logo.png`,
`dxf2gcode.svg`, `DXF2GCODE-001.ico`, `dxf2gcode.icns`). They are outside the
original 14-path documentation candidate. A later symbol refresh extends the
documentation candidate to 15 paths and the branding candidate to 16 paths,
including six icon-path references and deletion of the renamed old ICO path.
No runtime behavior or translation text was changed. Public GitHub asset delivery
is requested; because the initial handover
requires explicit commit/push approval, present the final commit packages and
two-commit ancestry for confirmation before creating commits or pushing.

Three candidate packages are prepared under `.tox/docs-handoff/`:
`prototype.index` / `prototype.patch` (15 paths), `branding.index` /
`branding.patch` (16 paths), and `preview-followup.index` /
`preview-followup.patch` (3 paths). `candidates.json` records base HEAD, tree IDs,
exact paths and current hashes. These are tree/index objects, **not commits**.
The third candidate includes only the appended DOC1 Todo section, not existing
CI1/test-strategy edits. The normal index is unchanged.

The ignored local helper `.tox/docs-handoff/prepare_candidates.py` refreshes the
review artifacts after edits. Do not clean this directory during the pending
handover. If absent, reconstruct candidates from the documented path lists.
At commit time recheck HEAD/files, run the fast hook, and reconcile only approved
paths with the real index while preserving unrelated staging. Do not blindly
commit the stacked indexes as independent HEAD-based commits.

Documentation checks build on relevant pushes/PRs and have read-only repository
permissions. The publishing workflow accepts manual dispatch only, requires a
deliberate `publish=true` input and `DOCS_PREVIEW_PUBLISH_APPROVED=true`, restricts
the repository/branch, and separates build from an OIDC Pages deployment job.
This task does not set the variable or dispatch the workflow. The configured
Pages `base_url` must match `zensical.toml`, otherwise the workflow stops.
Only `.tox/docs-site` is offered as a Pages artifact, never the repository or
raw snapshot. Action versions were read from the official actions repositories.

Before enabling publication, explicitly approve rights and destination, enable
Pages with GitHub Actions, and review the `github-pages` environment's branch
and reviewer rules. None of those settings were changed. Manual-dispatch
workflows normally need to exist on the default branch before they can be
started; a first prototype-branch push is not sufficient evidence of a working
deployment. Any promotion to `develop` requires a separate integration approval.

### Next steps / Resume work

1. Read this report, `doc/todo.md` DOC1 and the [migration plan](wiki-migration-plan.md).
   Start on `docs/zensical-prototype`; inspect status and the pre-existing staged
   hook. Do not create the Phase-2 branch yet.
2. Review the supplied v3 logo/header locally. SVG and PNG are present; the user
   reports own design with GPT assistance and no third-party components. See
   [provenance](sourceforge/RIGHTS.md). The subsequent request expanded scope to
   application branding and README; review the expanded branding package separately.
3. Refresh the isolated 15-path candidate after all edits. If HEAD or staged
   work changed, stop and recompute the candidate; never commit a stale alternate
   index. Preserve the original index and the other work throughout.
4. Obtain explicit commit approval, then run the required fast check through
   the pre-commit hook at commit time. No application test matrix, fresh install,
   full suite or release build is part of this task.
5. Obtain separate public-push approval, including the two ancestor commits.
   Review pending workflow/Todo changes separately and clarify their integration.
6. Obtain separate Pages setup/deployment approval after rights and target
   confirmation. Verify the deployed four pages, assets, search and repository
   subpath; update Todo with the real URL, run and commit IDs only after success.
7. After Phase 1 is integrated into `develop`, create `docs/wiki-migration` from
   that updated branch and request WP1: First DXF to G-code. Follow the full plan
   instead of reproducing it in Todo.

Local preview and focused documentation validation (from the repository root):

```powershell
& .\.tox\docs\Scripts\python.exe -m zensical serve
& .\.tox\docs\Scripts\python.exe -m zensical build --strict
```

The public canonical URL is not a claim that Pages is live. Use the address
printed by the local server, normally `http://127.0.0.1:8000/`; confirm its routes
after any configuration change. Do not reinstall dependencies merely to resume.

### Handover verification, 2026-11-01

The rebuilt site passes `--strict`: 167 local references, four sitemap URLs
under `https://dxf2gcode.github.io/dxf2gcode/`, 18 search entries, correct supplied
PNG hash, and HTTP 200 from the four local preview routes. New workflow YAML
parses and its event, read/write permissions, manual-publication gates and Pages
artifact path were inspected. It has not run on GitHub; local structural checks
are not an Actions acceptance result.

SVG and PNG sources are retained unchanged; the derived PNG/ICO/ICNS load with
the expected sizes. Ignored Qt resource caches were refreshed, and separate
Qt5/Qt6 resource imports read the new 492 x 157 image. No application GUI,
installer, full suite or release build was run. Existing packaged EXE/MSI/wheel
artifacts were not rebuilt. The new logo/title still need the user's visual check.

### Latest logo/icon refresh

The latest user-provided files have stable, version-free names in
`source/dxf2gcode/presentation/qt/resources/images/`:
`dxf2gcode-logo.png`, `dxf2gcode-logo.svg`, `dxf2gcode-symbol.png` and
`dxf2gcode-symbol.svg`. The original input bytes are preserved. The full
wordmark remains on the documentation home page, README and About image;
the dedicated square symbol now supplies documentation header/favicon,
`dxf2gcode.svg` for Linux, `dxf2gcode.ico` for Windows and `dxf2gcode.icns`.
The former `DXF2GCODE-001.ico` was renamed and its QRC/UI/dialog/builder
references updated. This is branding/resource maintenance, not the pending
export-test or version-documentation correction.

The previous 14/5/3 candidates are superseded by the refreshed 15/16/3 review
packages; no commits or push are authorized by refreshing them. The separate
program-commit review found the committed Fast suite still fails at the
order-dependent tool-change test, so the publication hold remains. That test
and its existing uncommitted change are untouched by this logo refresh.
