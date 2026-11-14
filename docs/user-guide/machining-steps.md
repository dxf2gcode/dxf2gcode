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
2. Right-click and choose **Assign machining…**. The same dialog is available
   from the drawing and machining tree. Geometry menus also list linked steps
   for navigation.
3. Choose **Copy** or **Move**, then **Existing step** or **New step**.
4. For an existing step, choose its name, kind and tool from the target list.
   For a new step, enter its name and choose kind/tool. All fields remain
   visible at fixed positions: existing targets enable the step selector,
   new targets enable name/kind/tool. The initial action is set only when the
   dialog opens. Switching targets never changes Copy/Move or any entered
   values, and the dialog size stays fixed. Cancel changes nothing.

Moving retains the existing operation identities. Additional machining creates
independent operations referencing the same original contours. The original
DXF-layer membership does not change. When a selected contour already has
several assignments, activate the intended source operation before using it
for a new step.

**Create…** in the toolbar retains the dedicated creation dialog, including
an empty step or an unused current selection. Without a selection it creates
an empty step. Double-click a step, or press **F2** with the tree focused, to
change its name, kind and tool. Selecting its row already exposes its defaults;
there are no redundant Edit step/Edit step defaults context-menu commands.
Both tool lists combine saved tools and the current tool table. Identical
complete definitions appear once. Entries show the T-number, diameter and
project unit. Saved definitions that differ from the table are marked
**Project deviation**; the matching **Tool table** variant remains available.
Differing spindle speeds or lead values appear as additional details. Hover
over an entry for its further values.

With a step row selected, selecting the matching table variant replaces that project definition in
**all steps using it**. Other definitions of the same T-number remain unchanged.
Choosing a different T-number changes only the selected step. Undo restores
the previous assignments and definitions. Project files retain their tool
values; later table changes are never applied automatically. Loading a project
unifies fully equal saved definitions without rounding their values.

To change the tool for one or several selected machining contours, use the same tool
dropdown. Only the selected assignments change. The application first looks for
an existing step with the same kind, complete target tool definition and exact
stored source-step defaults. One matching step is reused; multiple matches open
a target chooser. Cancel changes nothing. Names alone do not prevent reuse.
Without a match, a fully selected step changes its tool in place; a partial
selection moves to a new step directly after its source. Own values and
assignment identities remain intact. Different tools/defaults remain separate.
Explicit **New step** always creates a step. Undo/Redo restores the complete action together. Mixed
tools show **Different tools**. Other applicable parameters can also be edited
for the whole selection. Explicitly clicking an operation in the canvas changes
its preview emphasis while retaining a Ctrl-selected group; parameter edits
still apply to the whole selected group. This selection-based change does not replace tool
definitions for unselected steps.

## Choose which operation to edit

### Holding tabs from DXF and manual regions

Imported **BREAKS:** regions appear in a special **Holding tabs** group under
each machining contour whose planned path they actually affect. These are references
to the same global regions, not additional contours or operations. They have no
tool, export checkbox or position in the machining sequence. The group distinguishes
the number of source regions from the resulting tab segments; repeated depth passes
do not multiply the segment count. The separate **Tab regions** section in Geometry
lists all project regions, including disabled regions and those without effective
tabs. Original BREAKS shapes remain in Entities/Layers with region names and icons;
they do not participate in normal contour selection. Removed project regions leave
their original DXF geometry visible with a struck-through region name.

Normal canvas clicks, rectangle selection and original-layer selection skip these
regions. Selecting a machining contour automatically displays the associated
regions as thin dashed magenta outlines. Selecting original geometry shows the
union of regions for its linked operations, drawing shared regions only once.
Selecting a region in either tree highlights its affected contours; this alone
does not enable editing. Enable **Tab edit mode** to select outlines, move regions
and use the four corner handles of rectangular regions.

Clicking a BREAKS layer highlights all regions belonging to that layer and all
machining operations they actually affect. Clicking **Tab regions** below a
machining contour does the same for that group's regions. A global region also
highlights its affected operations in other steps. Repeated clicks retain the
selection; double-clicking a group expands/collapses it without deselecting paths.

Selecting an entire machining step highlights its operations and region descendants
in the tree as well as their paths in the canvas. Lighter tree highlighting marks
**derived references**. It does not add those rows to the editable selection:
step selection still edits step defaults; region selection edits region properties.
A selected region group shows a read-only summary. Export checkboxes and drag
targets do not change merely because descendants are highlighted.

Red denotes selected original geometry; blue denotes the machining/tool-centre
path, which can be offset from that original. Magenta denotes tab movements and
the dashed region outlines. Region references now highlight the associated
machining paths consistently instead of highlighting only the original contour.
The established movement colours remain unchanged.
Its icon shows a dashed region with a pencil and sits directly beside **Create**
on the left, with the machining actions. Tree expand/collapse controls remain
on the right. The button stays highlighted while tab editing is active.
In this mode, clicking an outline selects a region. Its editor offers tab-top Z,
XY/Z feeds and activation. Changes affect every operation using that region.
**Change assignment…** offers Global, Step or Selected operations. A step assignment
also applies to future operations added to that step. Operation assignments follow
their stable IDs when moved. Select the region below a machining contour and use
**Remove assignment** in the tab parameter area to exclude only that operation,
retaining the region elsewhere. The button is disabled without an operation-specific
selection. The assignment
dialog can explicitly clear local exclusions.

**Delete region…** removes the project region and all its links after a confirmation
showing the number of currently affected operations. Original DXF geometry remains.
Undo/Redo restores the complete change, including region identity and assignments.
The original BREAKS layer also offers **Edit imported tab regions** in its context
menu. Exit using the toolbar toggle. There is no special tab context menu in the
canvas, machining tree or region list; use the direct controls and double-click editing.

First select the intended original contours, machining steps or individual
operations. Original-contour selection covers **all linked operations**. Selecting
one or more operations covers **only those operations**; a step covers its
contained operations. No prior selection means no new region can be created.
Switch on **Tab edit mode** in the Machining toolbar to start drawing immediately.
You can also use **Draw new tab region…** from the normal canvas context menu or
the **+** in the Geometry region section. Always drag out a rectangle.
The default is **Snap to contour**: on release, the rectangle becomes an aligned square.
Its side length is the
selected machining tool's diameter plus the configured remaining tab length:
for example, Ø4 mm + 2 mm produces a 6 × 6 mm square. Only selected operations
whose original contours intersect the drawn region receive it. Other contours are
not assigned automatically. Different selected tools/contours can require separate
automatic squares; those are created together in one undo action.
The regions are assigned to the eligible selection and created immediately, without an
editing dialog. Double-click a region in the canvas, machining tree or geometry
region list to edit its name, placement mode, height, feeds and assignment.
The current machining selection supplies
the proposed assignment and feeds. The name defaults to the first unused localized
**Tab 1**, **Tab 2**, etc. (German: **Steg 1**). It remains freely editable;
existing saved names are not renamed when the interface language changes.
The first height defaults to workpiece top; later regions use the last
confirmed height. This is an initial value to review, not a guaranteed tab thickness.
The assignment list contains only operations whose **original contours pass through
the region interior**. Mere edge/corner contact is insufficient. Repeated machining
uses of the same intersecting contour remain separate choices. Steps are offered
only when they contain an eligible operation. One eligible operation is preselected
in the assignment editor when applicable. With no selected intersection, a message is shown and no region is created;
redraw the region. Global scope covers all eligible operations, subject
to any retained local exclusions. Eligibility does not depend on cutter radius,
tab height, export activation or the currently selected tab pass.
Dragging provides a temporary preview from the same planner. Changes are committed
only on release; Escape leaves the project unchanged.
After creating a new region, placement remains active so you can add the next
region on another contour immediately. An empty click clears the region and associated highlighting
without leaving tab mode. The selected region's handles and measurement labels
remain usable while the drawing session is active. Escape ends drawing.
The explicit target selection is retained for successive regions, including while
you inspect a created region. Selecting different contours/operations replaces
these targets; clicking empty canvas clears them. Select the next intended contour
or operation before drawing again. Dragging without targets only selects geometry
and cannot create a region in that same gesture.
In **Configuration → General settings → Tab regions**, choose the default
placement mode and remaining tab length (initially 2 in configuration units;
the standard profile uses mm). The configured length is converted to the drawing
unit before adding the project tool diameter. The **Tab placement** selection
beside the tab edit switch chooses **Snap to contour** or
**Draw manually** for new regions during the session. It does not change an
existing selected region. Use that region's double-click dialog for its own mode.
The selection is visible while tab mode is active. Each region stores its
own **Snap to contour** or **Draw manually** setting in the project. Switching a
region to snap, or resizing one already in snap mode, applies the configured square
size. Manual mode retains the dragged rectangle. A click without dragging
selects another original contour. Changing a machining tool's diameter resizes its
automatic regions to the new diameter plus the configured tab length. Manual
regions keep their dimensions. If a shared automatic region needs different sizes
for different machining uses, it is split into separate operation assignments;
unaffected uses retain their previous shape. Tool change, resizing and splitting
are one undo action. A configuration change alone does not resize existing regions.
Their canvas measurement fields remain
editable; a direct size edit switches that region to manual so its entered size
is retained. Existing imported/older regions default to manual. The square-size
rule is a placement preset; inspect the actual holding
tab at corners or on tight curves. The Z top is set separately as before.
The tree's tab count is the number of linked regions shown below the contour;
one region can produce several raised toolpath sections without increasing it.

Click a region once to select it. The first press/drag only selects; it cannot
change an unselected region's geometry. Once selected, drag its outline/interior
to move it, or a corner handle to resize it. Double-click opens the region dialog.
Measurement fields appear only while a selected region is at rest. They are hidden
during drawing, moving and resizing and reappear on release. Each
completed gesture is one undo action. Regions follow whole-drawing transforms.
Editing uses 2D; starting from the 3D canvas opens a separate 2D editing window.
In tab-editing mode, measurement fields sit at the midpoints of the upper and right
edges. They show only the number and project unit, without width/height captions,
and are shown only for the resting selection. Hover highlights a measurement; click it to
enter a positive size. **Enter** confirms, **Escape** cancels. A typed change keeps
the centre and the other edge length fixed and creates one undo entry. Entering
a value switches that region from automatic to manual, including explicitly
typing its existing value again; simply opening/cancelling the field does not.
Display
precision follows the configured mm/in settings; input and stored values keep
their full precision.

Hold **Ctrl** while dragging (including drawing or resizing) to align the rectangle
with two intersections of an original contour. The rectangle is centred between
those contacts, with its width axis along their connecting line; its current width
and height are retained. This uses original geometry, independently of cutter
compensation. With several eligible original contours, choose one on release;
cancelling that choice keeps the unsnapped drag result. Repeated machining uses
of the same original contour count as one alignment target. With no unambiguous
pair of contacts, alignment is skipped with a message. There is no automatic
placement; region creation and subsequent editing remain separate.

Effective tab
movements remain part of the shared plan and export; pass selection belongs to the
machining contour. Projects now save as **.d2g 2.1**. Versions 2.0 and legacy projects
remain readable, but older program versions cannot open the new files.

Use a **closed polygon**, for example a rectangle, for a tab region. Tab boundaries
are determined on the **original contour**. With software cutter compensation,
the corresponding points are transferred to the tool-centre path along line
normals or arc radii. With machine compensation, those same original contour
points are programmed. A region therefore does not have to reach the offset path.
There is no additional tangential allowance for the cutter radius: the region
does not guarantee a particular remaining material width.

A tab spanning a corner keeps the entire connecting offset curve raised, without
a plunge between its pieces. Arc portions remain arcs. If a tab boundary has
vanished or has multiple possible counterparts, the affected connected tab is
**omitted with a warning** and export continues. Other valid tabs remain. A boundary
exactly at a round offset join can also be ambiguous. Open or non-polygonal regions
are omitted with a warning. Review these warnings and the resulting paths before use.

Pocket boundary contours use this same reference; pocket raster passes retain
their existing spatial-region behaviour because they have no one-to-one original
contour counterpart. Drag-knife tab processing is unchanged. Existing project files
remain readable. Previously generated G-code is unchanged: export again to obtain
the new behaviour. Physical controller compensation still needs separate acceptance.

### Select machining contours

Selecting original geometry marks every linked operation. When several
operations use a contour, this does not arbitrarily activate one. Click an
operation in Machining, or its path/label in the canvas, to activate its editing
context. Its row is bold. There is no additional context line between the tree
and the parameters; context and selection hints remain available as tooltips.
With multiple selected assignments, the parameter area shows the complete
editing selection rather than only the active contour's values.
All linked previews remain visible when the original contour is selected,
including each operation's actual leads, start/end and depth information.
Ctrl-click adds or removes operations. Overlapping paths offer a chooser;
cancelling it leaves the selection unchanged. Partial selection dots the
original outline and shows a count such as **1/2**. Paths keep the established
movement colours; active/hovered operations use thicker lines. There are no
colour changes for selection. Unselected operations use thin dashed 0.6-pixel lines
and marker outlines; selected operations retain their normal line widths. There are no
artificial offsets to separate overlapping operations. Disabled previews follow
**Show disabled paths**; export-route display remains a separate action.

Canvas labels use **step name · contour number · tool**, for example
**7 · Contour 0 · T5**. The contour number matches the machining tree;
it is not an additional export-position number. A rectangle selection updates
the linked views once for the whole selection.

Multiple original contours with one machining assignment each can be edited
together directly. If any selected original contour has multiple linked
operations, the parameters and tool selector stay read-only until you explicitly
select the intended assignments in Machining or through canvas paths/labels.

For a multiple selection, equal inherited values are grey; equal values with
own overrides use the normal text colour. Different values show an editable
**Different** placeholder. Editing a field sets that parameter for every selected
assignment in one undo action; other parameters and unselected assignments stay
unchanged. Confirming a placeholder or leaving an untouched field changes
nothing. Dropdowns follow the same rule. A parameter that is not supported by
the entire selection shows **Not jointly available** and only that field is
disabled. Provenance symbols show the counts and sources of own/inherited values.
**Use step default** removes selected operation overrides, restoring each
operation's own inherited default, which may differ between steps.

The familiar tool and contour parameter fields are located directly in
Machining. Select a step to edit its defaults, or activate a contour assignment
to edit its operation values. The former parameter table has been removed.

A small **chain** indicates an inherited value; a **pencil** indicates an own
value in the current editing context. Hover over the symbol for the parameter,
source and effective value, including the contour/step for own values. Hover
over the input field for an explanation of its function. Editing an operation
value creates an own value.
Open the symbol’s dropdown menu and choose **Use step default** to remove
an own operation value. Each value has one symbol button. The **Machining tool**
and contour fields share aligned group/unit columns and compact value areas. Refreshing or leaving
an unchanged field does not create an override. Changing step defaults leaves
explicit operation overrides intact. The default display uses **3 decimal places for mm** and **5 for inches**,
for lengths. **Feeds and angles each default to 1 decimal place**, with
separate configurable settings. Whole numbers remain whole numbers.
Change these under **Options → Configuration → General settings → Number display**.
The settings also apply to configuration fields, tool-table values and numeric
dialogs. Focusing a numeric input shows its full value. Confirming or leaving an
unchanged input retains the stored precision; entering extra places retains
those places in the floating-point value used for planning and export.

The left pane starts at a width derived from the compact rows. Drag the divider
to change its width. A shared scrolling form starts with the tool selector and
spindle speed, followed by four group boxes: **Z values**, **Feeds**,
**Lead in/out** and **Offset**. Two values are placed side by side in each row.
Short labels include their units directly. Every provenance button follows its
input immediately; the extra space comes after that button.

Numeric fields provide approximately eight visible characters and still accept
full-precision input, scrolling their text when necessary. Leads and overcut
settings edit machining values rather than the tool definition. An explicit,
distinct legacy start radius remains available as a legacy field. Knife angle
and swivel depth appear only for drag knives; standard milling leads/overcut
are hidden for lathe and drag-knife machines.

Drag the horizontal divider between the machining tree and the whole parameter
area to change their heights. There is no divider between tool and contour
parameters and no separate parameter collapse headers. The four group boxes
share one scrollbar and remain at the top, with unused space below. Resizing
does not change machining values or the undo history.

Retract height and safety margin always edit the step defaults, including
when an operation is active. Tool selection also belongs to the step. The
machining fields can show operation overrides for speed and lead dimensions.
The two clearance fields affect all contours of the selected steps; their symbol
help states this scope. Local start coordinates can be changed together, with
the other coordinate preserved separately for each selected operation.
Direction commands belong to the active operation. Selecting a step row
shows its defaults in this same form.

Old depths and feeds whose origin cannot be established are retained as own
values. Equality with a default does not prove inheritance.

## Change a selected operation's machining mode

Right-click a contour assignment in **Machining** for **Contour**, **Pocket
Mill**, **Drill Bore** and **Cutter compensation → G40 / G41 / G42**.
The drawing menu provides the applicable Pocket/Drill actions and compensation
for the active operation in its familiar grouping. Checkmarks
show the current state. Selecting original geometry with several references
requires an explicitly active operation before the drawing menu can edit it.

Changing kind first looks for an existing step with the target kind, the same
complete tool definition and exact stored step defaults. One match is reused;
several matches require you to choose the target. Entries append to that step,
retaining own values, identities and geometry references. Cancelling rejects the
whole action. A new step is created after the source only when there is no
compatible target. Different source steps may share a target when their tools
and defaults match. Other assignments stay in their source steps. One action
is one undo entry; existing target names and settings remain unchanged.

Drilling explicitly selects G40. Selecting compensation on a drilling circle
returns that assignment to a matching contour step, creating one if necessary. Clicking an already
checked Pocket/Drill action returns to Contour. Invalid selections are rejected
as a whole: drilling needs a point/circle, and pockets need closed contours in
milling mode with internal compensation. The original layer membership does
not change. Special holding-tab/ignored assignments retain their kind.

The drawing context menu keeps this order, with separators between groups:

1. Move workpiece zero here (available with or without selection).
2. Invert selection; disable/enable the selected machining assignments.
3. Reverse direction; set the contour start nearest the clicked point or at
   the sharpest corner.
4. Applicable pocket/drilling actions, followed by the compensation submenu.
5. Assign machining as a separate group at the bottom.

Contour starts and direction change only the active assignments. Original
geometry and other assignments of the same contour remain intact. Start
candidates respect entity transformations and the clicked plane in 3D. These
changes use the machining undo history; manually displayed export routes stay
manual. The workpiece zero action remains separate from contour-start actions.

## Move, copy, reorder and undo

- Drag operation rows into a target step or before/after a row. A line marks
  the insertion position. Hold **Ctrl** while dropping to copy.
- **Assign machining…** in the drawing/tree context menu combines copying,
  moving and new-step creation. It also assigns selected **Unassigned**
  contours. Mixed assigned/unassigned selections are one atomic action;
  an incompatible selection is rejected as a whole.
- The top toolbar separates creation, ordering, history and tree-view actions.
  Collapse/expand controls sit to the right; unavailable actions are disabled.
- **Reverse** and **Remove** are in the tree context menu. Profile updates and
  custom G-code are grouped under **Advanced**; double-click edits the step.
  **Move workpiece zero here…** belongs to the drawing context menu and is
  available with or without a selection. It changes the workpiece origin;
  it does not edit an individual contour’s machining start. **Delete** removes the selected entry while the tree has focus.
- Use **Up/Down** or **Alt + Up/Down** to reorder entries or steps.
- Use **Undo/Redo** in the tab, or **Ctrl + Z / Ctrl + Shift + Z** while it
  has keyboard focus. A multi-selection action is one undo entry; redo restores
  the same identities.

Own depths, feeds and leads are retained when moving or copying. Inherited
values, tool and machining kind come from the target. Changes are reported after execution in
the main window's message pane below the drawing. Available Undo/Redo actions
are indicated by their enabled toolbar buttons. There is no separate status
message area below the machining fields. An incompatible selection is rejected as a whole: for
example, open contours cannot enter a pocket step, and drilling requires a
point/circle and G40. Later planning errors remain visible and block export.

Removing an operation preserves its original contour and other assignments.
Removing a nonempty step offers cancellation, removal of its assignments, or
transfer to another step. Import/reload starts a new history; this undo feature
does not cover every historical CAD or configuration action.

## Export and optimize

The **Export** checkbox controls inclusion independently for each operation.
It is available only in Machining. Selecting geometry is not an export filter.
Imported or saved **Ignored** steps are a special exclusion: their rows show
**Excluded** instead of an Export checkbox and offer no optimization checkbox.
They remain selectable and retain their saved data, but cannot be enabled for
export. Ignored is not offered when creating normal steps; existing ignored
steps retain their kind when edited. Use a normal operation's Export checkbox
for temporary exclusion.
The drawing's disabled style/visibility reflects whether any linked operation
is enabled. Unassigned contours have no machining preview or export assignment.

Normal export follows the visible steps and rows. Optimization keeps steps
fixed and works within each step, retaining both existing relative constraint
modes. Custom G-code rows form boundaries that optimization cannot cross.
Add them through the context menu and double-click to edit their code.
Profiles declaring managed tool-change return states retain their existing
restriction against opaque custom G-code.

The existing tool-change contract is retained: a tool-change block is emitted
only when the output tool number changes. Different saved tool definitions
must first be resolved against the tool table before export. For consecutive
T1 steps, own spindle-speed overrides do not themselves cause another block
or spindle-speed command. Check the chosen profile and the generated program.

Route display is separate from preview and optimization. Its machining
endpoints come from the planned approach and final position, including leads
and overcut. Preview-only actions do not activate manual route display.

## Saved values and changed drawings

Projects retain saved tool/default values when external profiles change.
Before export, every tool used by an enabled machining step must match the
current tool table. A missing tool number or different definition blocks the
whole export, preserving an existing output file and leaving stdout empty.
Empty, disabled, ignored and holding-tab-only steps do not block export.

The diagnostic identifies the tool number and affected steps. For missing
numbers it lists the saved definition; for differing tools it compares the
project and table values. Add or correct the tool through the tool-table
configuration, or choose an existing table tool for the affected steps.
Selecting the matching table definition replaces the deviation in all steps
sharing it. Tools are not created automatically. Preview and project saving
remain available while the conflict is unresolved. The rule also applies to
CLI exports and historical project files.

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
