# Documentation site maintenance

## Agreed information structure (15 November 2026)

The top-level sections are Home, User guide, Settings, Postprocessors,
Help and troubleshooting, Developer guide and Project information. User guide
contains six workflow groups: Getting started, Drawing and project, Tools,
Prepare machining, Toolpaths and output, Special applications. Tool configuration
and assignment have their own guide; emitted tool-change commands remain under
Postprocessors. Support's existing URL stays under `project/support/`, but its
navigation position is Help. No URL migration is implied by regrouping.

Section `index.md` pages give short starting points. Zensical's documented
`navigation.indexes` and `navigation.path` keep those headings clickable and
display breadcrumbs. Do not enable global expansion or flatten all the chapters
again. The [public maintenance guide](../../docs/developer/documentation.md)
records the editing contract and the
[upstream reference](https://zensical.org/docs/setup/navigation/) explains it.

The current public developer chapter is
[Documentation maintenance](../../docs/developer/documentation.md). This internal
note retains the operational setup details from the earlier public prototype.

The documentation site uses [Zensical](https://zensical.org/docs/get-started/), configured
in `zensical.toml` at the repository root. The development website is hosted
with GitHub Pages. A separate GitHub Actions workflow automatically publishes
website changes pushed or merged into `develop`, after a successful strict
documentation build. Local builds and pull-request checks do not deploy.

## Publish website updates

Commit and push the reviewed website changes to `develop`, or merge a reviewed
pull request into `develop`. Changes under `docs/` (including logos and icons),
to `zensical.toml`, `requirements-docs.txt` or the publishing workflow trigger
**Development documentation preview** automatically. A local commit alone
does not update the live website.

The workflow builds the documentation in strict mode and publishes only if
that build succeeds. Check the build and deploy jobs under
[GitHub Actions](https://github.com/dxf2gcode/dxf2gcode/actions/workflows/documentation-pages.yml).
The existing repository approval variable `DOCS_PREVIEW_PUBLISH_APPROVED=true`
and the `develop`-only Pages environment remain required.

To republish the current site without a new commit, select **Run workflow**
on `develop` and enable the `publish` input. Pull requests targeting `develop`
run documentation checks without publishing.

## Requirements

- Python 3.11 or newer with `pip` and `venv`.
- The packages in `requirements-docs.txt`, including Zensical 0.0.74.
- Internet access for the initial package installation.

The documentation environment is independent of the Qt application and does not
require PyQt, a Rust compiler or the application build. Use system fonts; the
site does not request Google Fonts. Zensical supplies the client-side search.

## Windows PowerShell

Run these commands from PowerShell. Replace the checkout path if necessary:

```powershell
Set-Location D:\GIT\dxf2gcode-sourcecode
py -3.11 -m venv .tox\docs
& .\.tox\docs\Scripts\python.exe -m pip install -r requirements-docs.txt
& .\.tox\docs\Scripts\python.exe -m zensical serve
```

Open <http://127.0.0.1:8000/> in your browser. Stop the server with **Ctrl+C**.
The commands call the environment's Python directly, so activating a PowerShell
script or changing the execution policy is unnecessary.

After the first installation, only the last command is needed to start the
preview. If Python 3.11 is not installed, select an installed Python version
of at least 3.11 instead.

## Build and check

From the repository root:

```powershell
& .\.tox\docs\Scripts\python.exe -m zensical build --strict
```

The generated website is written to `.tox/docs-site/`. Internal page links and
anchors are validated during the build. The build does not publish anything.

For a quick browser check, open [First DXF to G-code](../../docs/getting-started/first-dxf-to-gcode.md),
check the logo on the [home page](../../docs/index.md), and search for
**postprocessor**. Check that search results open the appropriate chapter.
Do not open generated HTML through `file://`;
use the local server so that search and assets load correctly.
