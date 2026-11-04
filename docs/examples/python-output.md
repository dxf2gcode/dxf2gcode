# Python text output example

Download [python-events.cfg.example](../assets/examples/postprocessors/python-events.cfg.example).
Copy it as `python-events.cfg` into the active `postpro_config` folder and select
**Python - event-list demonstration**. This profile writes text containing an
`events` list; DXF2GCODE does not execute it as a plugin or machine program.

## Output contract

The profile uses `output_type = text`, `.py`, absolute coordinates, a decimal
point and no line numbers. Opening text starts `events = [` and ending text
closes the list. Movement templates append tuples such as:

```python
events = [
    ('rapid_xy', 0.0, 0.0),
    ('feed', 200),
    ('line', 0.0, 0.0, 20.0, 0.0),
]
```

This is a hand-written illustration of the record format, not an exported
golden file. The download also has records for Z, arcs, tool/feed changes and
cut boundaries. It deliberately disables free comment insertion to avoid
treating arbitrary comment text as Python syntax.

Use [the simple rectangle](../assets/examples/first-dxf/rectangle-20x10-mm.dxf)
with milling/G40 and without custom tree G-code for the initial review. Unlike
DXF-type output, text output can include repeated depth-pass events. This is
an action log, not a standalone geometry serializer or Python API contract.

## Checks and limits

The complete configuration was loaded with the current schema and representative
formatted records parsed as Python syntax. No complete application export was
run for this chapter, and the generated text was not executed. Inspect generated
files as text before using them in another program, especially after modifying
templates or adding custom actions.

The old “Python postprocessor” title does not mean the application loads an
arbitrary Python postprocessor module. Adaptations here are configuration-driven
text templates. See [Postprocessor reference](../reference/postprocessors.md).
