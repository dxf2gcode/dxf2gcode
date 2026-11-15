# Select geometry, entities and layers

The **Geometry** tab shows the original drawing in collapsible **Entities** and
**Layers** sections. Entities follows imported blocks/entities; Layers groups
contours by their source layer. Both refer to the same original geometry.

## Select an original contour or entire layer

Expand the tree and click a shape, or select its parent layer to select the
contained contours. Canvas selection is linked to these views. The expand/collapse
buttons change the tree display without changing machining assignments.

Original selection displays linked machining operations. If an original has
several operations, explicitly choose the intended assignments in **Machining**
or through their canvas paths/labels before editing their parameters. See
[selection and editing](machining-steps.md#select-machining-contours).

## Keep source geometry separate from operations

Entities and Layers select geometry; export checkboxes belong to Machining.
Moving/copying an operation changes its machining-step assignment while retaining
its reference to the original contour and original DXF layer.

Contours without assignments appear under **Unassigned** and have no toolpath
or export. Initial `IGNORE:` contours use this state unless omitted by the import
filter. Assign them later through the normal machining workflow.

Imported `BREAKS:` shapes represent holding-tab regions. They have distinct
names/icons and do not act as ordinary cutting contours. Their links and project
region catalogue are explained under [holding tabs](tabs-and-breaking-layers.md).

Continue with [Create steps and assign contours](machining-steps.md).
