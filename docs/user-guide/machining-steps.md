# Machining steps and shared contours

The development version has **Geometry** and **Machining** tabs (German:
**Geometrie** and **Bearbeitung**). Geometry contains the original Entities
and Layers trees in collapsible sections, with a vertical divider to adjust
their space. Their selection remains linked to the drawing. Machining owns
the sequence, export checkboxes, tools and operation values. Original contours
are drawn once, even when used by several operations.

## Start from a drawing or an entire layer

On initial import, the machining steps follow the source layers. Each step
has one machining kind and one tool definition. Mixed legacy tools/kinds are
split into consecutive steps, retaining their previous export sequence.

1. Select a layer in the **Layers** section of Geometry to select its contours.
2. Right-click and choose **Create machining step…**, or use **Create…** at
   the top of Machining. The menu also lists linked existing steps for navigation.
3. Enter a name, such as Roughing or Finishing, and choose kind and tool.
4. Choose **Move existing assignments** (the default), **Additional machining**
   to copy, or **Do not use selection — create empty step**. Cancel changes nothing.

Moving retains the existing operation identities. Additional machining creates
independent operations referencing the same original contours. The original
DXF-layer membership does not change. When a selected contour already has
several assignments, activate the intended source operation before using it
for a new step.

**Create…** without a selection creates an empty step. **Edit step** in the
context menu, or **F2** with the tree focused, changes its name, kind and tool. The tool list includes saved project definitions and explicit options
to import a current profile tool. Different definitions may share one output
tool number, including different diameters.

## Choose which operation to edit

Selecting original geometry marks every linked operation. When several
operations use a contour, this does not arbitrarily activate one. Click an
operation in Machining to activate its editing context and preview. Its row
is bold, and **Active** identifies its step and tool.

The familiar tool and contour parameter fields are located directly in
Machining. Select a step to edit its defaults, or activate a contour assignment
to edit its operation values. The former parameter table has been removed.

A small **chain** indicates an inherited value; a **pencil** indicates an own
value in the current editing context. Hover over the symbol or field for the
source and effective value. Editing an operation value creates an own value.
Open the symbol’s dropdown menu and choose **Use step default** to remove
an own operation value. Each row has one symbol button. The **Machining tool**
and contour fields share the same label, unit, value and status columns. Refreshing or leaving
an unchanged field does not create an override. Changing step defaults leaves
explicit operation overrides intact. The default display uses **3 decimal places for mm** and **5 for inches**,
for lengths. **Feeds and angles each default to 1 decimal place**, with
separate configurable settings. Whole numbers remain whole numbers.
Change these under **Options → Configuration → General settings → Number display**.
The settings also apply to configuration fields, tool-table values and numeric
dialogs. Focusing a numeric input shows its full value. Confirming or leaving an
unchanged input retains the stored precision; entering extra places retains
those places in the floating-point value used for planning and export.

The left pane starts at a width derived from the widest content in each
column. Drag the divider to change its width. Labels, units and input columns
resize together across both parameter groups; only the symbol column stays
fixed. Labels wrap on narrow panes instead of pushing the symbol controls
outside the visible form.

Retract height and safety margin always edit the step defaults, including
when an operation is active. Tool selection also belongs to the step. The
tool-value fields can show operation overrides for speed and lead dimensions.
Direction and local start point belong to the active operation. **Edit step
defaults** in the context menu selects the step in this same form.

Old depths and feeds whose origin cannot be established are retained as own
values. Equality with a default does not prove inheritance.

## Change a selected operation's machining mode

Right-click a contour assignment in **Machining**, or right-click the drawing
with its intended operation active. The menu includes **Contour**, **Pocket
Mill**, **Drill Bore** and **Cutter compensation → G40 / G41 / G42**. Checkmarks
show the current state. Selecting original geometry with several references
requires an explicitly active operation before the drawing menu can edit it.

Changing kind moves the selected assignments into a new step immediately after
their source step. The new step keeps the source tool and defaults; own values,
operation identities and original geometry references remain. Other assignments
stay in the original step. Selecting operations from different steps creates a
separate new step for each source, keeping their tools and defaults distinct.
You can rename the generated steps afterward. One action is one undo entry.

Drilling explicitly selects G40. Selecting compensation on a drilling circle
returns that assignment to contour machining in a new step. Clicking an already
checked Pocket/Drill action returns to Contour. Invalid selections are rejected
as a whole: drilling needs a point/circle, and pockets need closed contours in
milling mode with internal compensation. The original layer membership does
not change. Special holding-tab/ignored assignments retain their kind.

## Move, copy, reorder and undo

- Drag operation rows into a target step or before/after a row. A line marks
  the insertion position. Hold **Ctrl** while dropping to copy.
- The context menu provides **Move to step** and **Copy to step**. These also
  assign selected **Unassigned** contours to an existing step.
- The top toolbar separates creation, ordering, history and tree-view actions.
  Collapse/expand controls sit to the right; unavailable actions are disabled.
- **Reverse**, **Edit step** and **Remove** are in the tree context menu.
  **Move workpiece zero here…** belongs to the drawing context menu and is
  available with or without a selection. It changes the workpiece origin;
  it does not edit an individual contour’s machining start. **Delete** removes the selected entry while the tree has focus.
- Use **Up/Down** or **Alt + Up/Down** to reorder entries or steps.
- Use **Undo/Redo** in the tab, or **Ctrl + Z / Ctrl + Shift + Z** while it
  has keyboard focus. A multi-selection action is one undo entry; redo restores
  the same identities.

Own depths, feeds and leads are retained when moving or copying. Inherited
values, tool and machining kind come from the target. Changes are reported
after execution. An incompatible selection is rejected as a whole: for
example, open contours cannot enter a pocket step, and drilling requires a
point/circle and G40. Later planning errors remain visible and block export.

Removing an operation preserves its original contour and other assignments.
Removing a nonempty step offers cancellation, removal of its assignments, or
transfer to another step. Import/reload starts a new history; this undo feature
does not cover every historical CAD or configuration action.

## Export and optimize

The **Export** checkbox controls inclusion independently for each operation.
It is available only in Machining. Selecting geometry is not an export filter.
The drawing's disabled style/visibility reflects whether any linked operation
is enabled. Unassigned contours have no machining preview or export assignment.

Normal export follows the visible steps and rows. Optimization keeps steps
fixed and works within each step, retaining both existing relative constraint
modes. Custom G-code rows form boundaries that optimization cannot cross.
Add them through the context menu and double-click to edit their code.
Profiles declaring managed tool-change return states retain their existing
restriction against opaque custom G-code.

The existing tool-change contract is retained: a tool-change block is emitted
only when the output tool number changes. For consecutive T1 steps, different
saved definitions or spindle speeds do not themselves cause another block or
spindle-speed command. Check the chosen profile and the generated program.

Route display is separate from preview and optimization. Its machining
endpoints come from the planned approach and final position, including leads
and overcut. Preview-only actions do not activate manual route display.

## Saved values and changed drawings

Projects retain saved tool/default values when external profiles change.
The context menu offers explicit **Update tool from profile** and **Update
step defaults from profile** actions, with undo. Own operation values remain
own values. Existing explicit machine-type/tolerance commands still change
the current project. An explicit drawing-unit change converts machining
values once and records that interpretation.

Save as JSON `.d2g` 2.0 to preserve operations and references. Historical
1.1–1.5 files remain readable; first save their migrated state under a new
name. On drawing reload, new contours appear as Unassigned. Missing or
ambiguous active references stop the whole export and preserve an existing
output file. See [Projects](import-and-projects.md).

Manual holding-tab regions and a shared user acceptance of the new workflow
remain separate follow-up stages.
