# Architecture

The code is organized around drawing/project state, application workflows,
toolpath planning, adapters and Qt presentation. The directory layout expresses
those responsibilities; legacy dependencies remain and must be checked before
assuming that every module is isolated.

| Package under `source/dxf2gcode/` | Responsibility |
| --- | --- |
| `bootstrap` | Launcher, composition, runtime/version state |
| `domain/geometry` | Points, lines, arcs and geometry calculations |
| `domain/project` | Shapes, layers, machining state and tool settings |
| `domain/toolpath` | Planning inputs, strategies, semantic movements and diagnostics |
| `application` | Import, project, export, shape actions and optimization workflows |
| `adapters` | DXF/config/project storage, planning snapshots, serialization and dialects |
| `presentation/qt` | MainWindow, tree controllers, 2D/3D views, widgets and Qt resources |

## From geometry to output

![Drawing and settings feed planning; preview and serialization consume its result](../assets/images/developer/planning-flow.svg)

Imported geometry describes the drawing. A prepared path includes offsets,
leads and clearing geometry. The semantic toolpath plan adds operation order,
depth passes, feeds, tabs, compensation transitions and retracts. A projection
draws it; serialization emits actions through the selected dialect.

The planner is not the tree-order optimizer, and a route-display redraw is not
a request to rebuild/export G-code. A tree reorder must synchronize export
state even when live route drawing is disabled.

## Boundaries that matter during changes

- **Input snapshots:** resolve effective tools, application settings, geometry
  and postprocessor capabilities before planning. A plan should not silently
  retain values from before the latest edit.
- **Geometry:** preserve continuity, order and direction when imported compound
  entities expand into segments. Reverse a complete chain consistently.
- **Planning:** own pass repetition, open-contour reversals, ramps, knife
  orientation and diagnostic outcomes; do not encode these only as canvas effects.
- **Projection:** retain original geometry for selection and show planned
  overlays separately. 2D can coalesce coincident paths; 3D retains depth.
- **Serialization:** format semantic actions and maintain dialect/modal state.
  A controller template must not determine geometry by parsing its own strings.

Milling/lathe/knife mode, G40/G41/G42 side, machine/software compensation and
postprocessor capabilities are separate inputs. A software-compensated side
choice can legitimately serialize a geometric centre path in G40.

## Current coupling and compatibility limits

`bootstrap/runtime_state.py` still holds shared configuration/window state.
Some project/preparation/GUI paths read it. `domain/constants.py` imports Qt
compatibility code, and preparation reuses established shape/lead/offset
algorithms. A clean package hierarchy is not proof of a completely Qt-free
application or domain runtime.

The old internal import namespaces were removed rather than kept as public
aliases. File-format compatibility is a separate contract: the current readers
support D2G 1.1–1.5, application configurations 9.11–9.19 and postprocessors
8–8.3. Do not infer arbitrary future-version support from those ranges.

## Review behaviour end to end

Trace a change through imported model, current selection/settings, plan,
preview, saved project and emitted output as applicable. Existing golden files
capture particular serialization contracts; they are not physical-machine
acceptance. Loaded contradictory machining settings remain visible and block
the affected plan rather than being silently repaired.

For implementation detail see the repository's
[architecture contracts](https://github.com/dxf2gcode/dxf2gcode/blob/develop/doc/architecture.md),
current `domain/toolpath`, `adapters/toolpath` and their focused regressions.
The English overview reflects the current readers rather than the historical
format ranges in older architecture notes.
