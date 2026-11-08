"""Active project tools must match the live table before file/stdout export."""

from copy import deepcopy
from dataclasses import replace
import contextlib
import io
from pathlib import Path

from dxf2gcode_leadmove_golden_test import GoldenTestBase, build_shape
from dxf2gcode_stmove_gcode_test import make_postpro
from dxf2gcode.application.machining import MachiningDrawing
from dxf2gcode.application.tool_table import project_tool_errors, table_tool
from dxf2gcode.domain.project.layercontent import Layers, Shapes
from dxf2gcode.domain.project.machining_project import new_id
import dxf2gcode.bootstrap.runtime_state as g


class TestToolTableExport(GoldenTestBase):
    def drawing(self):
        shape, layer = build_shape(cut_cor=40, done_by_machine=False)
        layer.shapes = Shapes([shape])
        layer.exp_order_complete = [0]
        binding = MachiningDrawing.capture(Layers([layer]), g.config)
        step = binding.project.steps[0]
        binding.project.tools[step.tool_id] = table_tool(g.config, 1, binding.project.units)
        return binding, step

    def test_full_definition_comparison_and_resolution(self):
        binding, step = self.drawing()
        project = binding.project
        self.assertEqual(project_tool_errors(project, g.config), [])
        original = project.tools[step.tool_id]
        for key in ('tool_diameter', 'speed', 'start_radius', 'lead_radius', 'lead_length', 'overcut_length'):
            with self.subTest(key=key):
                project.tools[step.tool_id] = replace(original, **{key: (getattr(original, key) or 0)+1e-9})
                errors = '\n'.join(project_tool_errors(project, g.config))
                self.assertIn('T1', errors)
                self.assertIn(step.name, errors)
                self.assertIn('table', errors)
        project.tools[step.tool_id] = original
        self.assertEqual(project_tool_errors(project, g.config), [])

    def test_missing_tool_names_steps_values_and_creation_guidance(self):
        binding, step = self.drawing()
        binding.project.tools[step.tool_id] = replace(binding.project.tools[step.tool_id], tool_nr=99)
        second = replace(deepcopy(step), id=new_id(), name='Finishing')
        second.entries[0].id = new_id()
        binding.project.steps.append(second)
        message = '\n'.join(project_tool_errors(binding.project, g.config))
        for expected in ('T99', step.name, 'Finishing', 'missing', 'Diameter', 'Add or correct'):
            self.assertIn(expected, message)

    def test_unused_disabled_ignored_and_break_steps_do_not_block(self):
        binding, step = self.drawing()
        binding.project.tools[step.tool_id] = replace(binding.project.tools[step.tool_id], tool_nr=99)
        for kind in ('ignored', 'break'):
            step.kind = kind
            self.assertEqual(project_tool_errors(binding.project, g.config), [])
        step.kind = 'contour'
        step.entries[0].enabled = False
        self.assertEqual(project_tool_errors(binding.project, g.config), [])
        step.entries.clear()
        self.assertEqual(project_tool_errors(binding.project, g.config), [])

    def test_unit_conversion_uses_actual_table_units_and_keeps_full_values(self):
        binding, step = self.drawing()
        project = binding.project
        original = table_tool(g.config, 1, 'mm')
        project.units = 'in'
        project.tools[step.tool_id] = original.scaled(1/25.4)
        # metric can change before the table itself has been converted.
        g.config.metric = 0
        self.assertEqual(project_tool_errors(project, g.config), [])
        project.tools[step.tool_id] = replace(project.tools[step.tool_id], tool_diameter=.07874)
        self.assertTrue(project_tool_errors(project, g.config))

    def test_whole_export_keeps_existing_file_and_stdout_empty(self):
        binding, step = self.drawing()
        bad = replace(deepcopy(step), id=new_id(), name='Unresolved tool', tool_id=new_id())
        bad.entries[0].id = new_id()
        binding.project.steps.append(bad)
        binding.project.tools[bad.tool_id] = replace(binding.project.tools[step.tool_id], tool_nr=99)
        output = Path(self.tmp) / 'existing.ngc'
        output.write_text('original program')
        for stdout in (False, True):
            g.config.vars.General['write_to_stdout'] = stdout
            pp = make_postpro()
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                pp.exportShapes('drawing.dxf', str(output), binding.materialize())
            self.assertTrue(pp.export_failed)
            self.assertIn('T99', '\n'.join(pp.export_errors))
            self.assertEqual(output.read_text(), 'original program')
            self.assertEqual(captured.getvalue(), '')

    def test_all_diagnostic_translations_are_compiled(self):
        import ast
        import xml.etree.ElementTree as ET
        from dxf2gcode.presentation.qt.qt_compat import QtCore
        root = Path(__file__).resolve().parents[1]
        tree = ast.parse((root/'source/dxf2gcode/application/tool_table.py').read_text(encoding='utf-8'))
        sources = {node.args[0].value for node in ast.walk(tree) if isinstance(node, ast.Call)
                   and isinstance(node.func, ast.Name) and node.func.id == 'tr'}
        for language in ('de', 'fr', 'ru'):
            translator = QtCore.QTranslator()
            self.assertTrue(translator.load(str(root/'source/i18n'/('dxf2gcode_'+language+'.qm'))))
            xml = ET.parse(root/'source/i18n'/('dxf2gcode_'+language+'.ts'))
            messages = {m.findtext('source'): m.findtext('translation') for c in xml.findall('context')
                        if c.findtext('name') == 'MyPostProcessor' for m in c.findall('message')}
            for source in sources:
                self.assertTrue(messages.get(source), (language, source))
                QtCore.QCoreApplication.installTranslator(translator)
                try:
                    self.assertEqual(QtCore.QCoreApplication.translate('MyPostProcessor', source), messages[source])
                finally:
                    QtCore.QCoreApplication.removeTranslator(translator)
