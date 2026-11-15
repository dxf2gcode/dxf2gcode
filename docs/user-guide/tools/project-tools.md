# Resolve project-tool differences

A new DXF starts from the current tool table. A loaded project retains saved
definitions so that changing an external profile does not silently change a job.

## Read the combined selector

The selectors in Machining and the step dialogs combine saved tools and the
current tool table. Identical
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



## Resolve a missing number or deviation before export

Projects retain saved tool/default values when external profiles change.
Before export, every tool used by an enabled machining step must match the
current tool table. A missing tool number or different definition blocks the
whole export, preserving an existing output file and leaving stdout empty.
Empty or disabled steps and unassigned geometry do not block export.
Holding-tab regions do not export as separate machining steps.

The diagnostic identifies the tool number and affected steps. For missing
numbers it lists the saved definition; for differing tools it compares the
project and table values. Add or correct the tool through the tool-table
configuration, or choose an existing table tool for the affected steps.
Selecting the matching table definition replaces the deviation in all steps
sharing it. Tools are not created automatically. Preview and project saving
remain available while the conflict is unresolved. The rule also applies to
CLI exports and historical project files.



The tree's **Advanced → Update tool from profile** action is another explicit
update with undo. Own operation values remain own values. Editing or saving
the project stays available while a tool conflict is unresolved.

For initial table configuration, see [Maintain the tool table](tool-table.md).
For changing only selected assignments to another tool, see
[Assign and change tools](assignments.md).
