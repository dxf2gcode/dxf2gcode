# Machining parameters

Select the intended contour in **Layers** before editing machining values.
The fields describe the current selection; an enabled shape can be exported
without being selected. Start with [First DXF to G-code](../getting-started/first-dxf-to-gcode.md)
for a complete numeric example.

## Units and depths

Check the unit labels. Linear dimensions use the active mm/inch setting, feed
uses length per minute, and spindle speed uses rpm. Changing the unit setting
converts the current values; typing `1` still means one unit in the displayed
system, not an automatic conversion from millimetres.

| Field | Meaning |
| --- | --- |
| Z Retraction area | Layer's retract Z coordinate |
| Z Safety margin | Approach/retract distance above workpiece top; safe Z is top plus its magnitude |
| Z Workpiece top | Z coordinate of the top surface |
| Z Infeed depth | Step used to reach the final depth in successive cuts |
| Z Final mill depth | Final Z coordinate, rather than a positive thickness value |
| Feed rate XY / Z | Feed for planar cutting / axial movement |

For an illustrative millimetre setup, use top `0`, infeed `-0.5` and final
depth `-1.2`. The cutting depths are **-0.5, -1.0 and -1.2 mm**. The last step
is shortened to reach the final depth. With top `2 mm`, final depth `1 mm`
still means cutting 1 mm below that top, not cutting down to Z = -1 mm.

Use a nonzero infeed and a sensible depth interval. The planner reports zero
infeed, final depth above the top and an initial step deeper than the final
depth. Some depth diagnostics are warnings rather than hard export blocks;
correct the values instead of treating a produced file as validation.

Open contours can reverse direction on successive milling passes. Controller
profile options influence compensation cancellation and drilling repetitions;
the depth table alone does not specify every retract or drill cycle.

## Tools, defaults and contour values

Define tools through **Options → Configuration → Tools**. For milling, the
diameter is the cutter diameter; software compensation uses half of it as the
tool radius. The tool number selects an entry, while speed, lead radius,
straight lead length and overcut length are associated tool values.

| Selection/action | Scope to expect |
| --- | --- |
| Assign a tool to selected contour rows | Give those contours an explicit tool override |
| Assign a tool to an explicitly selected whole layer | Update its layer tool and clear the contours' tool overrides |
| Edit workpiece top, infeed, final depth or feeds on selected contours | Change those contours' values |
| Edit retraction or safety margin | Change the applicable layer values |
| Edit lead/overcut mode on selected contours | Change their applicable mode overrides |

Selecting a different tool can also set the additional milling offset from
that tool entry. Recheck the offset when changing tools. A deliberately stored
layer value from a parameterized DXF layer can take precedence over a tool
default; advanced layer naming belongs to the configuration chapter.

## Read shared and mixed values

An equal numeric value is displayed normally; a value matching its standard
can be shown in grey while remaining editable. Grey text alone is not proof
that a numeric value will track all future configuration changes.

**Different** means that the selection has mixed values or mixed applicability.
It is a display state, not a number. If the field remains enabled, entering a
value deliberately applies it across the supported selection. If it is disabled,
select a compatible subset first. Unchanged, rounded display text does not
request replacement of the stored exact value.

## Restore a standard deliberately

- For numeric depths and feeds, enter the intended standard value explicitly;
  there is no universal “reset every contour parameter” button in this panel.
- For tool inheritance, select the whole layer and assign its tool. This
  clears the individual tool overrides and can replace other tool-sourced values.
- Lead/overcut selectors show the effective method rather than a separate
  “Default” option. Selecting the current global standard clears the respective
  contour override, so the inherited setting applies again.

Save a D2G project after preparing the values. Opening the original DXF alone
does not reopen that saved preparation.

Continue with [Contours, pockets and drilling](contours-pockets-and-drilling.md)
and [Cutter compensation and lead moves](compensation-and-leads.md).
