# Qt resources and translations

The application supports PyQt5 and PyQt6 through its compatibility layer.
Source UI/QRC files live in `source/dxf2gcode/presentation/qt/resources/`;
generated Python modules live in `presentation/qt/generated/`. Maintained
translation sources are `source/i18n/dxf2gcode_de.ts`, `_fr.ts` and `_ru.ts`.

## Generate UI and resources

From the repository root, select a binding and run the helper:

```sh
python source/tools/build/qt_assets.py
```

Set `DXF2GCODE_QT=5` or `6` in the shell beforehand. PyQt's `uic` produces the
UI module. Qt5 uses its Python resource compiler; Qt6 needs a discoverable Qt
`rcc` executable. The helper repairs generated resource imports for the package
and selected binding. Installing PyQt6 alone is not proof that `rcc` is available.

Expected generated names include `dxf2gcode_ui5.py` / `dxf2gcode_ui6.py` and
`dxf2gcode_images5_rc.py` / `dxf2gcode_images6_rc.py`. Do not hand-edit generated
modules as the maintained fix: update the UI/QRC input or generation helper.

## Compile existing catalogs only

For startup/package preparation without changing translation source text:

```sh
python source/tools/build/translations.py --no-pylupdate
```

This invokes `lrelease` for the existing TS files and creates QMs. It does not
run extraction or update TS entries. Tool discovery checks the current
interpreter's tool directories and PATH/platform candidates. Missing Qt
Linguist tooling is a preparation error, not an instruction to delete catalogs.

## Change GUI text

1. Update source strings in the correct runtime translation context.
2. Extract/update catalogs with the selected binding's `pylupdate` tooling:
   `python source/tools/build/translations.py --keep-ln`.
3. Edit **German, French and Russian** entries, preserving placeholders and
   relevant plural forms. `--keep-ln` retains source locations and skips QM
   compilation for the editing stage.
4. Run `python source/tools/build/translations.py` to update, strip locations
   and compile. Review the TS diff for unintended changes.
5. Verify changed messages using the actual context and loaded catalogs.

From `source/`, GNU Make provides `trs` for the editing stage and `trf` for
finishing. `make prepare` compiles/prepares the selected runtime; it is not a
substitute for translating new strings in every maintained catalog.

## Locale and packaging

Runtime lookup tries the system locale and its language fallback. Resource
lookup is independent of the process working directory. Test a translated
startup from outside the checkout when checking packaged resources; an
in-checkout success can hide missing assets.

QM files and generated UI/resource modules follow `.gitignore`; do not force-add
them. TS sources and maintained UI/QRC changes belong in the contribution.
Release preparation includes generated assets for **both** supported bindings,
then verifies their presence; ordinary selected-binding startup needs less.
See [Packaging and builds](packaging.md).

Changing this website's English prose does not change Qt GUI strings and does
not require a TS/QM regeneration. Website build and application preparation
remain independent workflows.
