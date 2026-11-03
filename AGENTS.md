# Repository instructions

## Clarification

- If a requirement is unclear, ask the user before implementing the
  ambiguous part instead of guessing the intended behavior.

## Validation scope

- Run Debian/SSH test workflows, full test suites, complete release/MSI builds,
  and other lengthy validation only when explicitly requested or after the
  user accepts a concrete proposal for that work.
- Prefer focused, quick local checks for routine changes. Earlier one-off
  approvals do not authorize later lengthy builds or Debian test runs.
- These limits apply to agent-started local validation. GitHub CI runs the
  full suite on pushes to `develop` and pull requests targeting `develop`.
- Before local commits that change source code, tests or executable tooling,
  run the fast suite through the pre-commit hook. Do not run it a second time
  manually when the hook has already passed.
- Documentation-only commits (including documentation images, example drawings,
  site navigation and repository instructions) do not require source-code tests.
  Check the staged paths before committing and run the relevant documentation
  checks instead. While the hook is unconditional, disable it only for that
  individual documentation-only commit with a command-local `core.hooksPath`
  pointing to an empty directory; do not change the persistent Git setting.

## Efficient completion

- Keep work proportional to the requested change. Read only relevant file
  sections and keep progress messages brief and informative.
- Ask only about unresolved decisions that materially block implementation.
- Run the appropriate focused checks once. Repeat or broaden them only after
  a new change, a failure or a concrete unresolved risk warrants it.
- Update Todo, completion records and documentation notes in one closing pass,
  then finish. Do not add speculative checks or extra polishing rounds.
- Required translation checks and the pre-commit hook still apply; do not
  duplicate checks that have already passed without a concrete reason.

## GUI translations

- When adding or changing GUI text, update all maintained translation catalogs
  in the same change: German, French and Russian under source/i18n.
- Regenerate the corresponding QM files and verify the changed translations.
  Generated files remain subject to the repository's ignore rules.

## Task tracking and documentation

- Keep `doc/todo.md` concise and limited to genuinely open work, including
  unresolved decisions and explicitly deferred tasks. Link detailed plans
  instead of keeping implementation history or completed checklists there.
- When work is completed, move its outcome, validation evidence and remaining
  acceptance limits to `doc/archive/toolpath-refactoring-completed.md` in the
  same change. Do not leave completed items in the active Todo.
- Preserve useful material for future user documentation in topic files under
  `doc/documentation-notes/`, with links to authoritative guides, examples and
  sources. Keep these notes separate from open tasks and completion history.
- Retain task identifiers, decisions, source attribution and working relative
  links when reorganizing documents. Software completion must not imply a
  package, platform or physical-machine acceptance that has not occurred.
- Apply these rules during ongoing work, not only when explicitly asked to
  clean up the Todo. Update the documentation index when adding topic files.

## Commit messages

- Write commit messages in English, following the repository's Conventional
  Commit style: `type(scope): imperative summary`.
- Keep the subject concise: aim for about 50–70 characters and do not exceed
  75 characters. Recent repository subjects range from 44 to 74 characters,
  with most around 50–65. Start the summary with a lowercase verb and omit the
  final period.
- Choose a type that describes the change, such as `feat`, `fix`, `refactor`,
  `test`, `docs`, `build`, `ci` or `chore`.
- Use a short, relevant scope when practical. Existing scopes include `core`,
  `gui`, `cli`, `suite` and `coverage`; add another scope when it describes the
  changed area more clearly.
- Add a body only when it helps explain the reason for the change or details
  the subject cannot convey. Separate it from the subject with a blank line
  and wrap body text at about 80 characters per line.
- Keep the complete message, including subject and body, within 1,400
  characters. This allows a detailed explanation comparable to the longer
  recent messages while keeping the message focused.
- Examples based on this repository's history:
  - `fix(core): prevent offset collapse at degenerate spline ends`
  - `feat(gui): add configurable scale bar overlay`
  - `test(suite): add portable regression tests`
- When asked to suggest a commit message, inspect the actual staged or requested
  changes and propose a message that describes them. Do not create a commit
  unless explicitly asked.
