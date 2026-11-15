# Postprocessors

A postprocessor defines the output dialect and controller capabilities.
It is separate from the application profile, tool table and machining mode.
Choose its description in the export dialog or explicitly in command-line use.

| Task | Guide |
| --- | --- |
| Understand profile files, settings, placeholders and output templates | [Configuration and templates](postprocessors.md) |
| Define emitted tool-change commands and return-state contracts | [Tool changes and macros](tool-changes.md) |
| Explore complete profiles with a defined scope | [Examples and their limits](../examples/index.md) |

The examples include [laser](../examples/laser.md), [hot-wire](../examples/hot-wire.md),
[lathe](../examples/lathe.md), [DXF](../examples/dxf-output.md) and
[Python text output](../examples/python-output.md). They describe their own
validation limits and are not universal machine configurations.

For selecting tools within machining operations, return to
[Tools](../user-guide/tools/index.md). For the file-export workflow, use
[Preview and export](../user-guide/preview-and-export.md).
