"""Declared manual/ATC macros, real export sequences and incremental resumption."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TEST_DIR = Path(__file__).resolve().parent
sys.path[:0] = [str(TEST_DIR), str(TEST_DIR.parent / 'source')]
import dxf2gcode_stmove_gcode_test as machining
import dxf2gcode.bootstrap.runtime_state as g
from dxf2gcode.domain.geometry.linegeo import LineGeo
from dxf2gcode.domain.geometry.point import Point
from dxf2gcode.domain.project.layercontent import Layers, LayerContent
from dxf2gcode.domain.project.tool_settings import ToolSettings
from dxf2gcode.domain.toolpath.customgcode import CustomGCode
from dxf2gcode.application.toolpath.tool_change import ToolChangeContext
from dxf2gcode.adapters.postprocessor.tool_change import ToolChangeMacro


ATC = ('(ATC %tool_nr)%nlG91 G28 Z0%nlT%tool_nr M6%nl'
       'G90 %units_code %work_offset%nlG0 X%next_start_x Y%next_start_y%nl'
       'G0 G43 H%length_offset_nr Z%retract_z%nlS%speed%nl')
MANUAL = ('(MANUAL %tool_nr)%nlM0%nlG90 %units_code %work_offset%nl'
          'G0 X%next_start_x Y%next_start_y%nlG0 Z%retract_z%nl')


class TestToolChange(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pp = machining.make_postpro()
        self.pp.postpro_file_used = 'macro-test.cfg'
        self.settings = self.pp.vars.Tool_Change
        self.settings.return_state = 'next_start_at_retract'
        self.settings.length_offset_mode = 'tool_number'
        self.pp.vars.Program.tool_change = ATC
        self.shapes = []
        self.layers = Layers([])
        for nr in range(2):
            shape = machining.make_shape(
                [LineGeo(Point(10 + nr * 10, 20), Point(11 + nr * 10, 20))],
                closed=False, nr=nr, cut_cor=40)
            shape.axis3_slice_depth = -1
            layer = shape.parentLayer
            layer.nr = nr
            layer.name = 'L%d' % nr
            layer.tool_nr = nr + 1
            layer.axis3_retract = 5 + nr * 2
            layer.exp_order_complete = [0]
            layer.lead_in_mode = layer.lead_out_mode = 'off'
            machining.build_stmove(shape)
            self.shapes.append(shape)
            self.layers.append(layer)

    def export(self):
        path = Path(self.temp.name) / 'output.ngc'
        with patch.dict(g.config.vars.General.__dict__, write_to_stdout=False), \
                patch.dict(g.config.vars.Plane_Coordinates.__dict__,
                           axis1_start_end=0.0, axis2_start_end=0.0), \
                patch.object(self.pp, 'write_gcode_be', return_value='G21\nG90\nG40 G49\n'):
            self.pp.exportShapes('macro.dxf', str(path), self.layers)
        return path.read_text() if path.exists() else None

    def test_atc_sequence_uses_next_layer_retract_and_plans_once(self):
        service = self.pp._get_shape_export_use_case()
        with patch.object(service, 'prepare', wraps=service.prepare) as prepare:
            code = self.export()
        self.assertEqual(prepare.call_count, 2)
        self.assertFalse(self.pp.export_errors)
        self.assertLess(code.index('T1 M6'), code.index('G0 X'))
        self.assertIn('G0 G43 H1 Z   5.000', code)
        self.assertIn('G0 G43 H2 Z   7.000', code)
        self.assertEqual(code.count('(ATC '), 2)
        self.assertNotIn('G0 Z  15.000', code.split('(ATC 1)')[0])
        expected = (TEST_DIR / 'golden/tool_change_atc.ngc').read_text()
        self.assertEqual(''.join(line.rstrip() + '\n' for line in code.splitlines()), expected)

    def test_manual_macro_resumes_incremental_from_declared_xyz(self):
        self.pp.vars.General.abs_export = False
        self.pp.vars.Program.tool_change = MANUAL
        code = self.export()
        self.assertFalse(self.pp.export_errors)
        self.assertEqual(code.count('M0\n'), 2)
        self.assertEqual(code.count('G91\n'), 2)
        self.assertIn('G91\n\n(* SHAPE Nr: 0 *)\nG0 X   0.000 Y   0.000', code)
        expected = (TEST_DIR / 'golden/tool_change_manual_incremental.ngc').read_text()
        self.assertEqual(''.join(line.rstrip() + '\n' for line in code.splitlines()), expected)

    def test_same_tool_does_not_repeat_change_even_between_layers(self):
        self.layers[1].tool_nr = 1
        code = self.export()
        self.assertEqual(code.count(' M6'), 1)

    def test_shape_overrides_change_a_b_a_inside_layer(self):
        third = machining.make_shape(machining.square_geos(), nr=2, cut_cor=40)
        layer = self.layers[0]
        layer.shapes = [self.shapes[0], self.shapes[1], third]
        layer.exp_order_complete = [0, 1, 2]
        self.layers = Layers([layer])
        for shape in layer.shapes:
            shape.parentLayer = layer
            machining.build_stmove(shape)
        self.shapes[1].tool_override = ToolSettings.from_profile(
            2, g.config.vars.Tool_Parameters['1'])
        code = self.export()
        self.assertEqual([line for line in code.splitlines() if line.endswith(' M6')],
                         ['T1 M6', 'T2 M6', 'T1 M6'])

    def test_empty_layers_emit_no_change_or_positioning(self):
        for layer in self.layers:
            layer.exp_order_complete = []
        code = self.export()
        self.assertNotIn('M6', code)
        self.assertNotIn('G0 ', code)

    def test_invalid_macro_preserves_existing_output_file(self):
        path = Path(self.temp.name) / 'output.ngc'
        for macro, message in (('', 'empty'), ('%not_available', 'Unavailable'),
                               ('T%previous_tool_nr', 'Unavailable')):
            with self.subTest(macro=macro):
                path.write_text('KEEP EXISTING FILE')
                self.pp.vars.Program.tool_change = macro
                self.assertEqual(self.export(), 'KEEP EXISTING FILE')
                self.assertTrue(self.pp.export_failed)
                self.assertIn(message, self.pp.export_errors[-1])

    def test_custom_gcode_rows_require_a_return_contract(self):
        self.layers[0].shapes = [CustomGCode('raw', 3, 'G91 Z-2', self.layers[0])]
        self.assertIsNone(self.export())
        self.assertIn('opaque Custom G-Code', self.pp.export_errors[-1])

    def test_legacy_empty_macro_keeps_initial_z(self):
        self.settings.return_state = 'legacy'
        self.pp.vars.Program.tool_change = ''
        code = self.export()
        self.assertFalse(self.pp.export_errors)
        self.assertTrue(code.split('G40 G49\n')[1].startswith('G0 Z'))

    def test_length_mapping_custom_macro_and_scalar_profile_values(self):
        self.settings.length_offset_mode = 'mapping'
        self.settings.length_offset_mapping = '1:4,2:9'
        self.pp.vars.Custom_GCode.__dict__['%change'] = {'gcode': ATC}
        self.pp.vars.Program.tool_change = '%change(Decimals ${post.Number_Format.post_decimals})%nl'
        code = self.export()
        self.assertIn('G0 G43 H4', code)
        self.assertIn('G0 G43 H9', code)
        self.assertIn('(Decimals 3)', code)

    def test_missing_length_mapping_is_a_diagnostic(self):
        self.settings.length_offset_mode = 'mapping'
        self.settings.length_offset_mapping = '1:4'
        self.assertIsNone(self.export())
        self.assertIn('mapping for tool 2', self.pp.export_errors[-1])

    def test_context_formats_units_and_previous_tool(self):
        self.pp.vars.Program.tool_change = '%units_code T%previous_tool_nr Z%initial_retract_z'
        context = ToolChangeContext(2, 1, 1000, (10, 20), 7, 15, False)
        self.assertEqual(ToolChangeMacro(self.pp).expand(context), 'G20 T1 Z  15.000\n')

    def test_macro_uses_lead_entry_instead_of_original_contour_start(self):
        shape = machining.make_shape(machining.square_geos(), nr=0, cut_cor=41)
        layer = shape.parentLayer
        layer.lead_in_mode = 'straight'
        layer.lead_length = 2.0
        layer.exp_order_complete = [0]
        machining.build_stmove(shape)
        self.layers = Layers([layer])
        self.assertEqual(shape.get_start_end_points(True), Point(0, 0))
        code = self.export()
        self.assertFalse(self.pp.export_errors)
        self.assertIn('G0 X  -1.000 Y  -2.000', code.split('(* SHAPE')[0])

    def test_length_offset_is_not_assumed_without_a_rule(self):
        self.settings.length_offset_mode = 'none'
        self.assertIsNone(self.export())
        self.assertIn('%length_offset_nr', self.pp.export_errors[-1])

    def test_invalid_scalar_custom_cycles_and_declarations_are_rejected(self):
        for template in ('${post.Missing.value}', '${post.General}',
                         '${post.General.__dict__}', '%ZE'):
            with self.subTest(template=template):
                self.pp.vars.Program.tool_change = template
                self.assertIsNone(self.export())
                self.assertTrue(self.pp.export_failed)
        self.pp.vars.Custom_GCode.__dict__['%loop'] = {'gcode': '%loop'}
        self.pp.vars.Program.tool_change = '%loop'
        self.assertIsNone(self.export())
        self.assertIn('Cyclic', self.pp.export_errors[-1])
        self.pp.vars.Program.tool_change = ATC
        self.settings.work_offset = 'G54.1'
        self.assertIsNone(self.export())
        self.assertIn('work offset', self.pp.export_errors[-1])

    def test_cli_reports_failure_instead_of_success_without_a_file(self):
        from dxf2gcode.application.cli_export import ExportDrawing
        from dxf2gcode.application.drawings import DrawingModel
        from unittest.mock import Mock
        self.pp.getPostProVars = Mock()
        self.pp.vars.Program.tool_change = '%undefined'
        path = Path(self.temp.name) / 'cli.ngc'
        with self.assertRaisesRegex(ValueError, 'Unavailable tool-change parameter'):
            ExportDrawing(None, None, self.pp, g.config).export_model(
                DrawingModel(None, self.layers, self.shapes), 'drawing.dxf', str(path))
        self.assertFalse(path.exists())

    def test_macro_form_and_compiled_translations(self):
        import xml.etree.ElementTree as ET
        from dxf2gcode.presentation.qt.qt_compat import QtCore
        from dxf2gcode.presentation.qt.qt_compat.QtWidgets import QApplication
        from dxf2gcode.adapters.postprocessor.postprocessorconfig import (
            MyPostProConfig, POSTPRO_SPEC)
        from dxf2gcode.presentation.qt.configwindow import ConfigWindow
        from configobj import ConfigObj
        from validate import Validator
        app = QApplication.instance() or QApplication([])
        values = ConfigObj(configspec=POSTPRO_SPEC, interpolation=False)
        values.validate(Validator(), copy=True)
        for language in ('de', 'fr', 'ru'):
            path = TEST_DIR.parent / 'source/i18n' / ('dxf2gcode_%s.ts' % language)
            messages = ET.parse(path).findall("./context[name='MyPostProConfig']/message")
            translations = {message.findtext('source'): message.findtext('translation')
                            for message in messages}
            translator = QtCore.QTranslator()
            self.assertTrue(translator.load(str(path.with_suffix('.qm'))))
            app.installTranslator(translator)
            try:
                form = ConfigWindow(MyPostProConfig.makeConfigWidgets(), values, values.configspec)
                settings = form.cfg_window_def['Tool_Change']
                self.assertEqual(settings['return_state'].getValue(), 'legacy')
                settings['return_state'].setValue('next_start_at_retract')
                self.assertEqual(settings['return_state'].getValue(), 'next_start_at_retract')
                for key, widget in settings.items():
                    if key.startswith('__'):
                        continue
                    expected = widget.label.text()
                    self.assertIn(expected, translations.values())
                    self.assertEqual(translator.translate('MyPostProConfig', next(
                        source for source, text in translations.items() if text == expected)), expected)
                errors = ET.parse(path).findall("./context[name='MyPostProcessor']/message")
                source = 'Unavailable tool-change parameter: %s'
                translated = next(message.findtext('translation') for message in errors
                                  if message.findtext('source') == source)
                self.pp.vars.Program.tool_change = '%undefined'
                self.assertIsNone(self.export())
                self.assertEqual(self.pp.export_errors[-1], translated % '%undefined')
                form.close()
            finally:
                app.removeTranslator(translator)


if __name__ == '__main__':
    unittest.main()
