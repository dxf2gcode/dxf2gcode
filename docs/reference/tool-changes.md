# Tool changes and macros

`Program.tool_change` is the actual tool-change template. It is emitted for
the first tool and when the **effective tool number** changes, including contour
overrides inside one layer. Consecutive operations with the same number do not
request another change. A sequence A → B → A requests three tool selections.

## Legacy or managed return state

| `Tool_Change.return_state` | Contract |
| --- | --- |
| `legacy` | Preserve the established template/output sequence; no managed position guarantee |
| `next_start_at_retract` | Macro ends with the new tip at the next operation's XY approach point and retract Z |

Legacy is the default, including migrated old profiles. The default G49 and
M6 template do not silently activate a new length-compensation policy.

The managed contract is a **profile author's assertion**. Its macro must leave
the correct units and work coordinate system, G40, the required tool length
correction, and the declared absolute position. The software cannot prove that
an arbitrary M6 subprogram really reaches that state.

```ini
[Tool_Change]
return_state = next_start_at_retract
end_distance_mode = G90
work_offset = G54
length_offset_mode = mapping
length_offset_mapping = "1:4,2:9"
```

This is a contract fragment, not a complete machine macro. It explicitly maps
tool 1 to length register H4 and tool 2 to H9; it does not measure those lengths.

## Macro parameters

| Parameter | Meaning |
| --- | --- |
| `%tool_nr`, `%speed`, `%nl` | New tool, speed and newline |
| `%next_start_x`, `%next_start_y` | First actual approach point, including lead/pocket entry |
| `%retract_z` | Next operation's retract coordinate |
| `%initial_retract_z` | Separate global initial retract coordinate |
| `%length_offset_nr` | Register according to the selected explicit policy |
| `%units_code` | G21 or G20 |
| `%distance_mode` | Configured output mode G90 or G91 |
| `%work_offset` | Declared G54–G59 or G59.1–G59.3 |
| `%previous_tool_nr` | Previous tool; unavailable on the first selection |

Managed target coordinates are absolute and in export units, even for G91
output. After the macro, the adapter restores G90/G91 if its declared final
mode differs, updates the internal position and explicitly reapplies the next
planned feed. Subsequent increments are calculated from that declared position.

`length_offset_mode` is `none`, `tool_number` or `mapping`. `none` provides no
H register and suits a macro that handles length correction independently.
`tool_number` explicitly assumes H = T; `mapping` uses the listed associations.
Missing/duplicate mappings and unavailable parameters are errors.

Direct scalar references such as `${post.Tool_Change.work_offset}` and
`${post.Number_Format.post_decimals}` can be used in the macro. Numeric values
use profile formatting and booleans become 0/1. Nested references and whole
sections are rejected. This is text expansion, not Python execution. Named
`Custom_GCode` macro blocks can participate; cyclic references are rejected.

## LinuxCNC manual-change example

The repository provides a newly authored
[LinuxCNC manual-change profile](https://github.com/dxf2gcode/dxf2gcode/blob/develop/doc/examples/linuxcnc-manual.cfg.example).
Save it as `linuxcnc-manual.cfg` in the active postprocessor folder and select
its description. It requires an installed manual M6 handshake, premeasured
tools and verified retract/work-offset coordinates. It performs no probing
and does not rewrite the tool table or workpiece origin.

Its sequence establishes absolute mode/units/work offset, retracts to the
global initial height, stops spindle/coolant, calls Tn M6, restores the modal
setup, applies G43, retracts using the next tool's correction, moves to the
actual XY approach and sets speed. G43 without H uses the loaded tool in
LinuxCNC; M6 alone does not activate that length correction. See the official
[G43 reference](https://linuxcnc.org/docs/stable/html/gcode/g-code.html#gcode:g43)
and [manual-change component](https://linuxcnc.org/docs/stable/html/man/man1/hal_manualtoolchange.1.html).

The order Z before XY and the initial uncorrected retract must fit the actual
setup. The example makes no G28/G30/G53 position assumption. An M0 pause alone
does not establish the same manual-change/length state. This is an existing
software-checked example, not a newly machine-accepted configuration.

## Restrictions and failure handling

The managed implementation supports **milling G-code**. Free custom G-code
rows in the machining tree are rejected because they can invalidate the state
contract; macro blocks inside the tool-change template are permitted. Other
machine modes and free tree rows can still use legacy profiles.

Invalid plans, empty managed templates, unknown parameters and missing mappings
are diagnosed before writing the destination; an existing output file is
preserved on these failures. Empty managed jobs emit no tool-change or positioning
movement. The next plan supplies both the macro targets and the cutting path.

Repository regression outputs include absolute/incremental LinuxCNC manual
changes and synthetic ATC/manual macros. They check software serialization,
not the real tool table, M6 handshake or clearance. See
[Tests](../developer/tests.md) and the [profile examples](../examples/index.md).
