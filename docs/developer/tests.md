# Tests

Run checks proportionate to the change. The maintained suite lives under
`tests/`; fixture drawings live under `dxf/`. Test modules are deliberately
flat because existing helpers are shared between them.

## Select the scope

All commands below run from the repository root in a prepared environment:

```sh
python -m unittest discover -s tests -p dxf2gcode_machining_modes_test.py
python tests/run_tests.py fast
python tests/run_tests.py full
```

The first command is an example of a focused regression module. `fast` uses
the runner's explicit module list; `full` discovers `dxf2gcode_*test.py`.
Both return nonzero on failure. Check the current runner rather than relying
on a fixed historical test count.

The Fast group includes integration paths and an isolated quiet export; it
is not limited to pure geometry units. The full group adds broader GUI/CLI,
architecture, configuration and regression coverage. Headless GUI tests use
`QT_QPA_PLATFORM=offscreen`; this does not establish real OpenGL/desktop acceptance.

Tox environments are also defined:

```sh
python -m tox -e fast
python -m tox -e full
```

Prepare UI/resources and QMs first. A test dependency installation does not
automatically supply the Qt development tools or generated application assets.
See [Development setup](setup.md) and [Qt preparation](qt-and-translations.md).

## Before local commits

Enable the versioned hook once from the prepared test interpreter:

```sh
python tools/install_hooks.py
```

The installer stores that interpreter in local Git configuration and sets
`core.hooksPath = .githooks`; it refuses to overwrite an existing custom hook
arrangement. The hook runs Fast and blocks code commits on failure. Do not
repeat Fast manually after the hook has already passed.

Pure documentation changes, images, drawing examples and site navigation need
documentation checks rather than source-code tests. Inspect staged paths first.
While the hook is unconditional, the repository instructions permit a
command-local empty hooks directory for that documentation-only commit; do not
disable the persistent hook. See [Contributing](contributing.md).

## Local approval and automatic CI

Full-suite, Debian/SSH workflows and complete release/MSI builds need a specific
request or an accepted proposal before an agent starts them locally. A prior
approval is not a permanent authorization for later large runs.

GitHub automatically runs **Tests and package checks** for pushes to `develop`
and PRs targeting it. The shared workflow covers the current Python/Qt matrix,
then Python and Windows packages. This is distinct from the manually initiated
**Publish release** workflow. A passing test workflow does not publish a release.

## Useful evidence

For geometry defects compare original contour, prepared path and serialized
movements. For GUI binding differences exercise actual Qt events as needed,
not only mocks. For file/state changes check persistence and diagnostic paths.
Prefer meaningful assertions over tests that merely repeat an implementation.

Record commands, interpreter/binding, result and remaining acceptance limits.
Do not label mocked OpenGL, config parsing or a successful package build as
target-machine acceptance. The authoritative scope is in
[AGENTS.md](https://github.com/dxf2gcode/dxf2gcode/blob/develop/AGENTS.md) and
the [test README](https://github.com/dxf2gcode/dxf2gcode/blob/develop/tests/README.md).
