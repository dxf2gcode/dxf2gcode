# Repository instructions

## Clarification

- If a requirement is unclear, ask the user before implementing the
  ambiguous part instead of guessing the intended behavior.

## GUI translations

- When adding or changing GUI text, update all maintained translation catalogs
  in the same change: German, French and Russian under source/i18n.
- Regenerate the corresponding QM files and verify the changed translations.
  Generated files remain subject to the repository's ignore rules.

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
