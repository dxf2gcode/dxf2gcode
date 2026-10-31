# Contributing to dxf2gcode

Thank you for helping maintain dxf2gcode. Development is taking place on the
`develop` branch while the existing application is modernized incrementally.

## Questions and proposals

- Use [GitHub Issues](https://github.com/dxf2gcode/dxf2gcode/issues) for bugs
  and improvement proposals. Check existing issues before opening a new one.
- Use the [existing forum](https://www.ltspiceusers.ch/forums/english-section.67/)
  for user questions and discussions.
- Discuss substantial behavior or architecture changes before implementing them.

## Pull requests

- Target `develop` and keep each change small, focused and easy to review.
- Explain the problem, the resulting behavior and how you checked the change.
- Respect the ongoing restructuring and existing file formats and behavior.
  Avoid unrelated moves, renames and broad rewrites.
- Add or adjust tests that demonstrate the affected behavior. For documentation
  changes, check links, commands and consistency instead.
- Describe validation results and anything you could not verify in the PR.
- Use English Conventional Commit subjects, such as
  `fix(core): preserve contour order during export`, with a maximum of
  75 characters and no final period.

Read the [technical documentation](source/README.md),
[architecture contracts](doc/architecture.md) and
[repository instructions](AGENTS.md) for the area you change.

## Tests

Prepare the checkout using the [root README](README.md), then run the focused
checks from the repository root:

```sh
python tests/run_tests.py fast
```

Use relevant individual regression tests for the affected behavior. The
[test guide](tests/README.md) explains prerequisites, test selection and the
full suite. Agree on full-suite runs, Debian/SSH validation, complete release/MSI
builds or other extensive checks with a maintainer before starting them.

## Translations and generated files

When adding or changing GUI text, update all maintained translation catalogs
in `source/i18n/`: German (`dxf2gcode_de.ts`), French (`dxf2gcode_fr.ts`) and
Russian (`dxf2gcode_ru.ts`). Regenerate the corresponding QM files and verify
the changed translations.

The translation and Qt generation commands are documented in
[source/README.md](source/README.md). Keep generated files subject to the
repository's ignore rules; do not force-add compiled QM files or generated
UI/resource modules. Include the maintained TS changes in the contribution.
