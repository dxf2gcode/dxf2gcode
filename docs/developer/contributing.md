# Contributing

Target the `develop` branch and keep changes focused. Explain the concrete
problem, resulting behaviour and validation. Discuss major behaviour/API changes
before implementation. Read the current
[repository instructions](https://github.com/dxf2gcode/dxf2gcode/blob/develop/AGENTS.md)
and [contribution guide](https://github.com/dxf2gcode/dxf2gcode/blob/develop/CONTRIBUTING.md).

## Make changes reviewable

- Keep geometry, planning, projection and serialization responsibilities clear.
- Preserve established order, configuration and project contracts unless a
  deliberate change is agreed and migration is described.
- Add focused regressions for meaningful behaviour/state/error changes.
- For pure documentation, verify commands, links, assets and the strict site build.
- Update all maintained GUI translations when source GUI text changes.
- Report limitations precisely; a simulated or mocked check is not hardware acceptance.

Inspect the actual diff before selecting checks or writing a commit description.
Avoid broad reformatting, generated-file churn and unrelated fixes in one PR.

## Tests and local hooks

Code/test/executable-tool changes require Fast through the pre-commit hook.
Enable the hook from the intended prepared interpreter with
`python tools/install_hooks.py`; do not rerun Fast after a passed hook.
Use focused tests while developing and agree separately on full-suite,
Debian/SSH or complete release/MSI runs. Automatic GitHub CI has its own scope.

Documentation-only commits need relevant documentation checks. After confirming
that staged paths contain only documentation/assets/site navigation, an empty
hooks directory can be supplied to the individual commit command while the
current hook is unconditional. Do not persistently disable `core.hooksPath`.
This exception does not cover source, tests or executable tooling.

## Commit and PR text

Use English Conventional Commit subjects:

```text
docs(guide): explain profile selection and project references
fix(core): preserve contour continuity after reversing imports
```

Use an imperative lowercase summary, no final period, ideally 50–70 characters
and at most 75. Add a body only when needed; wrap near 80 columns and keep the
complete message within 1,400 characters. A request for a suggested message is
not permission to create a commit.

A PR description should explain the final change for a reviewer who has not
seen the conversation. Include relevant checks and remaining risks, not the
history of abandoned approaches. Do not claim a deployment merely because the
code or prose was committed.

## Task records and source material

Keep `doc/todo.md` limited to open work. Move outcomes and evidence to
`doc/archive/toolpath-refactoring-completed.md`; preserve useful future writing
material under `doc/documentation-notes/` and update its index. Keep task IDs,
decisions and working links when reorganizing.

Do not copy wiki prose, third-party screenshots/DXFs or private discussion
archives just because they are downloadable. Record attribution and rights,
or write an original explanation and create an original example. See
[License and credits](../project/license-and-credits.md) and
[Historical documentation](../project/history.md).
