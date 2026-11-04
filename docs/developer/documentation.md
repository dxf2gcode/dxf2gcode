# Documentation maintenance

The site source is `docs/`, navigation/settings are in `zensical.toml`, and
the independent build dependencies are in `requirements-docs.txt`. The current
dependency pin is Zensical 0.0.74. Application Qt preparation is unnecessary
for a documentation-only build.

## Preview and strict build

From the repository root, create a separate environment:

```sh
python -m venv .tox/docs
```

On Windows PowerShell:

```powershell
.tox/docs/Scripts/python.exe -m pip install -r requirements-docs.txt
.tox/docs/Scripts/python.exe -m zensical serve
```

On POSIX shells use `.tox/docs/bin/python` in place of that executable.
Open the local server address printed by the command (normally
`http://127.0.0.1:8000/`). Stop the server with Ctrl+C. Using the interpreter
directly avoids shell activation requirements.

Build without serving:

```powershell
.tox/docs/Scripts/python.exe -m zensical build --strict
```

Generated output is `.tox/docs-site/`. Strict validation checks internal links
and anchors. Also inspect changed images, downloads, navigation and search as
applicable. Use the HTTP server for browser checks rather than opening the
generated files through `file://`.

## Add or revise a chapter

Write current instructions from the current implementation. Distinguish a
code-reviewed command from an executed example. Name units, prerequisites and
the actual profile when movement/output matters. Use original or cleared assets
and keep an adjacent metadata file for provenance and acceptance limits.

Add the page to the appropriate navigation group and link related chapters.
When removing a public draft, update incoming links and the navigation too.
Keep developer website instructions in this chapter or internal notes rather
than presenting prototype setup as an application operating step.

Use short relative paths for site-local links and full canonical URLs for
repository files outside `docs/`. Do not publish a raw private snapshot or
personal configuration to make a broken link resolve.

## Publish deliberately

The canonical site is <https://dxf2gcode.github.io/dxf2gcode/>. The
[Pages workflow](https://github.com/dxf2gcode/dxf2gcode/actions/workflows/documentation-pages.yml)
builds reviewed changes pushed/merged to `develop`, then deploys after a strict
build. It requires `DOCS_PREVIEW_PUBLISH_APPROVED=true` and the develop-only
Pages environment. A local commit or PR build does not publish the site.

The manual workflow can republish develop with its `publish` input enabled.
Publishing documentation is separate from creating a software release. Check
the workflow result and representative public page/download URLs after deploy.
If one page shows old navigation, force-reload that page and compare with a
private browser window before assuming the source build is inconsistent.

Maintain Todo/completion/provenance notes in one closing pass. Do not run
application Fast/full tests solely for prose, images or navigation changes.
See [Contributing](contributing.md) and the repository's internal site-maintenance
notes for the operational record.
