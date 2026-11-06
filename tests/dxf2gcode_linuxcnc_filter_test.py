"""Real GUI filter processes: program output, profile selection and exit status."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestLinuxCNCFilter(unittest.TestCase):
    def run_filter(self, case, expected_status, marker=None):
        with tempfile.TemporaryDirectory(prefix='d2g_filter_') as folder:
            env = os.environ.copy()
            env.update(HOME=folder, USERPROFILE=folder,
                       QT_QPA_PLATFORM='offscreen')
            result = subprocess.run(
                [sys.executable, __file__, '--worker', case],
                cwd=folder, env=env, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, expected_status,
                         result.stderr.decode('utf-8', errors='replace'))
        if marker:
            self.assertIn(marker.encode(), result.stdout)
            self.assertNotIn(b'FILTER_OTHER', result.stdout)
            self.assertIn(b'G1 X', result.stdout)
            self.assertIn(b'M2 (Program end)', result.stdout)
            self.assertEqual(result.stdout.count(b'M2 (Program end)'), 1)
            self.assertNotIn(b'INFO', result.stdout)
            self.assertNotIn(b'ERROR', result.stdout)
            self.assertIn(b'STDOUT', result.stderr)
        else:
            self.assertEqual(result.stdout, b'', result.stdout)
            self.assertIn(b'ERROR', result.stderr)
        self.assertNotIn(b'Traceback', result.stderr)

    def test_explicit_description_selects_second_postprocessor(self):
        self.run_filter('success', 0, 'FILTER_SELECTED')

    def test_full_filter_text_selects_postprocessor(self):
        self.run_filter('full-name', 0, 'FILTER_SELECTED')

    def test_selection_does_not_depend_on_filename_order(self):
        self.run_filter('reverse-order', 0, 'FILTER_SELECTED')

    def test_legacy_default_is_preserved_without_postpro(self):
        self.run_filter('default', 0, 'FILTER_SELECTED')

    def test_unknown_postprocessor_fails_without_output(self):
        self.run_filter('unknown', 2)

    def test_duplicate_descriptions_are_rejected(self):
        self.run_filter('ambiguous', 2)

    def test_closing_window_without_export_is_cancellation(self):
        self.run_filter('cancel', 1)

    def test_planning_conflict_does_not_publish_partial_program(self):
        self.run_filter('conflict', 2)

    def test_unsupported_pocket_does_not_publish_partial_program(self):
        self.run_filter('unsupported-pocket', 2)

    def test_export_exception_does_not_publish_partial_program(self):
        self.run_filter('exception', 2)

    def test_missing_input_fails_without_opening_file_dialog(self):
        self.run_filter('missing', 2)

    def test_invalid_input_fails_without_output(self):
        self.run_filter('invalid', 2)

    def test_startup_export_exits_without_entering_closed_window_event_loop(self):
        self.run_filter('startup-export', 0, 'FILTER_SELECTED')


def worker(case):
    import runpy
    import shutil
    from unittest.mock import patch

    sys.path.insert(0, str(ROOT / 'source'))
    import dxf2gcode.bootstrap.runtime_state as g
    from dxf2gcode.domain import constants
    from dxf2gcode.adapters.config.runtime_config import MyConfig
    from dxf2gcode.adapters.postprocessor.postprocessorconfig import MyPostProConfig
    from dxf2gcode.presentation.qt.qt_compat import QtCore, QtWidgets

    g.folder = constants.DEFAULT_CONFIG_FOLDER + '.filter_test'
    config = MyConfig()
    config.var_dict['General']['write_to_stdout'] = True
    config.var_dict['General']['mode3d'] = False
    config.var_dict['Logging']['console_loglevel'] = 'INFO'
    config.save_varspace()
    for name, selected in (('a.cfg', case in ('reverse-order', 'default')),
                           ('z.cfg', case not in ('reverse-order', 'default'))):
        post = MyPostProConfig(filename=name)
        post.create_default_config()
        post.var_dict['General']['output_text'] = (
            'Filter chosen' if selected or case == 'ambiguous' else 'Other')
        post.var_dict['General']['code_begin'] += (
            ' (FILTER_SELECTED)' if selected else ' (FILTER_OTHER)')
        post.save_varspace()

    filename = Path.home() / 'drawing with spaces.dxf'
    if case == 'invalid':
        filename.write_text('not a DXF file\n', encoding='ascii')
    elif case != 'missing':
        shutil.copyfile(ROOT / 'docs/assets/examples/first-dxf/rectangle-20x10-mm.dxf',
                        filename)

    def finish():
        window = getattr(g, 'window', None)
        # Loading processes Qt events before the drawing is ready.
        if window is None or not window.shapes or window.canvas_scene is None:
            QtCore.QTimer.singleShot(10, finish)
            return
        if case == 'cancel':
            window.close()
            return
        if case == 'conflict':
            window.shapes[0].Drill = True
            window.shapes[0].Pocket = True
        if case == 'unsupported-pocket':
            window.shapes[0].Pocket = True
            g.config.machine_type = 'lathe'
        if case == 'exception':
            def fail(*args, **kwargs):
                print('PARTIAL PROGRAM MUST NOT ESCAPE')
                raise RuntimeError('deliberate export failure')
            with patch('dxf2gcode.application.exporting.ExportToolpath.execute', fail):
                window.exportShapes()
        else:
            window.exportShapes()

    class FilterApplication(QtWidgets.QApplication):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if case != 'startup-export':
                QtCore.QTimer.singleShot(0, finish)

    # Exercise the actual argument parser, startup, Qt event loop, closeEvent
    # and SystemExit. Only the user action is supplied by a timer.
    sys.argv = ['dxf2gcode', '--cfg', 'filter_test']
    if case != 'default':
        requested = 'Filter chosen (*.ngc)' if case == 'full-name' else 'Filter chosen'
        sys.argv += ['--postpro', 'Unknown' if case == 'unknown' else requested]
    if case == 'startup-export':
        sys.argv += ['--export', str(Path.home() / 'unused')]
    sys.argv += [str(filename)]
    with patch.object(QtWidgets, 'QApplication', FilterApplication):
        runpy.run_module('dxf2gcode.presentation.qt.application', run_name='__main__')


if __name__ == '__main__' and '--worker' in sys.argv:
    worker(sys.argv[-1])
elif __name__ == '__main__':
    unittest.main()
