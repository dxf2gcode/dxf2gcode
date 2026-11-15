# Assign and change tools

Each machining step has one tool definition. Choose a tool in the selector
above the parameter groups. Selecting a step edits that whole step; selecting
contour assignments targets only those assignments.

## Change selected assignments

To change the tool for one or several selected machining contours, use the tool
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


## Change a whole step

Select its row and choose the tool, or double-click the step to edit its
name, kind and tool. A different tool number changes that step. Replacing a
saved definition with its matching table variant has a wider scope:
see [Resolve project-tool differences](project-tools.md).

Choosing a tool does not itself specify the controller's physical change
procedure. The emitted commands belong to
[Tool changes and macros](../../reference/tool-changes.md).

Continue with [machining parameters](../machining-parameters.md).
