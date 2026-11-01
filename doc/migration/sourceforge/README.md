# SourceForge wiki preservation

This is a local preservation record, **not migrated user documentation**.
Do not publish the snapshot before completing the [rights review](RIGHTS.md).
It contains obsolete instructions, discussion posts and personal contact details.

## Snapshot

The authoritative inventory is [manifest.json](manifest.json). Its
`snapshot_root` points to `snapshot/phase1-complete/` in this directory.
The directory is excluded by the repository's `.gitignore` and is outside
Zensical's `docs_dir`. It is not included in the built website or its search.

The completed phase-1 snapshot contains:

- A live API index listing exactly 15 public wiki pages.
- All 15 latest page texts as UTF-8 Markdown, without editorial corrections.
- Original API responses and rendered HTML for all 15 pages.
- Retrieved history HTML as evidence of editors, without exporting every
  historical page revision.
- Public discussion API responses and their attachment metadata.
- 23 of 24 discovered images, example files and discussion attachments.
- Retrieved SourceForge project-summary and hosting-terms HTML.

An earlier timestamped snapshot remains as an intermediate preservation copy.
Use `manifest.json` and `phase1-complete` for the completed inventory.

Each downloaded resource records its source URL, final URL, retrieval status,
content type, relative local path, byte count and SHA-256. API attachment byte
counts are checked when available. Page entries include original URLs,
modification dates, Markdown hashes, observed history editors and internal /
external links. Media entries record source pages and known uploaders.
Observed editors and uploaders are not automatically the copyright holders.

## Remaining gap

The LayerControl illustration `Spant.png` returns HTTP 404:

<https://lh6.googleusercontent.com/-MzmeNlgC5rg/Uu4Ra-qwNwI/AAAAAAAACCg/PGOyXf3choI/s320/Spant.png>

Its failed request is retained in the manifest. The linked Google Drive DXF
example was successfully downloaded. Four discussion attachments named
`alternate` were identified as HTML mail bodies; they were preserved locally
after matching their sizes against the API. They must not be embedded into the
website as trusted HTML.

This is not an administrative export: deleted/private pages, unreferenced
attachments, every revision's text and all SourceForge project downloads are
outside the verified scope. The archive is not a self-contained offline HTML
mirror; original HTML still has its original links. Original files and the
manifest are retained for a later controlled conversion.

## Repeat a read-only snapshot

From the repository root, with Python 3.11 or newer:

```powershell
py -3.11 tools\documentation\archive_sourceforge.py
```

The standard-library-only script uses public HTTP GET requests. It creates a
new snapshot directory and updates the top-level manifest. It refuses to
overwrite an existing snapshot directory. Failed resources remain explicit.
It does not modify SourceForge, rewrite the source texts, commit or publish.

The ignored snapshot is **only a local copy**. Before cleaning the workspace,
copy it to a private backup location together with its manifest and rights
notes. Do not add the raw snapshot to a public Git repository until publication
rights and personal data have been reviewed.
