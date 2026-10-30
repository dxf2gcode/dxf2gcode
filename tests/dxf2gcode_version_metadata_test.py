"""Fast provenance tests using disposable repositories and build trees."""

from dataclasses import asdict
import ast
import json
import os
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parent.parent / "source"
sys.path.insert(0, str(SOURCE))

from dxf2gcode.bootstrap import version_metadata as metadata


class TestBuildProvenance(unittest.TestCase):
    def test_build_commands_prefer_source_to_older_installed_package(self):
        with tempfile.TemporaryDirectory() as directory:
            shadow = Path(directory) / "dxf2gcode"
            shadow.mkdir()
            (shadow / "__init__.py").write_text("__version__ = 'old'\n")
            environment = os.environ.copy()
            environment["PYTHONPATH"] = directory
            command = SOURCE / "tools/build/setuptools_commands.py"
            # This test isolates source selection, not setuptools internals.
            # It must also run where no modern build backend is installed.
            script = """
import pathlib, runpy, sys, types
for name in ('setuptools', 'setuptools.command',
             'setuptools.command.build_py', 'setuptools.command.sdist'):
    sys.modules[name] = types.ModuleType(name)
sys.modules['setuptools.command.build_py'].build_py = object
sys.modules['setuptools.command.sdist'].sdist = object
helper = runpy.run_path(sys.argv[1])
import dxf2gcode
assert pathlib.Path(dxf2gcode.__file__).resolve() == pathlib.Path(sys.argv[2]).resolve()
assert helper['capture_build_info'](pathlib.Path(sys.argv[2]).parent).version == sys.argv[3]
"""
            result = subprocess.run(
                [sys.executable, "-c", script, str(command),
                 str(SOURCE / "dxf2gcode/__init__.py"), metadata.__version__],
                cwd=directory, env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="d2g_metadata_")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.package = self.root / "site-packages" / "dxf2gcode"
        self.package.mkdir(parents=True)

    def save(self, **changes):
        info = metadata.VersionInfo(
            "1.2.3", revision="a" * 40, branch="develop",
            commit_date="2026-10-30T08:00:00+01:00", dirty=False)
        data = dict(asdict(info), schema=1)
        data.update(changes)
        (self.package / metadata.METADATA_FILE).write_text(json.dumps(data), encoding="utf-8")

    def test_installed_build_does_not_query_git(self):
        self.save(build_date="2026-10-30T07:01:00+00:00")
        # Even if installed below a repository, its Git is irrelevant.
        (self.root / ".git").mkdir()
        with patch.object(subprocess, "run", side_effect=AssertionError("Git called")):
            info = metadata.get_version_info(self.package, "1.2.3")
        self.assertEqual(info.branch, "develop")
        self.assertEqual(info.origin, "build")
        self.assertFalse(info.dirty)

    def test_absent_invalid_or_mismatched_build_data_is_unknown(self):
        path = self.package / metadata.METADATA_FILE
        for text in (None, "not JSON", "[]", '{"schema": 2}',
                     '{"schema": 1, "version": "other"}',
                     '{"schema": 1, "version": "1.2.3", "dirty": "false"}'):
            with self.subTest(text=text):
                if text is not None:
                    path.write_text(text, encoding="utf-8")
                info = metadata.get_version_info(self.package, "1.2.3")
                self.assertEqual(info, metadata.VersionInfo("1.2.3"))

    def test_build_inherits_sdist_provenance_and_timestamp(self):
        self.save(build_date="2026-10-30T07:01:00+00:00", dirty=True)
        destination = self.root / "wheel" / metadata.METADATA_FILE
        info = metadata.write_build_metadata(destination, self.package, "1.2.3")
        self.assertEqual(info.build_date, "2026-10-30T07:01:00+00:00")
        self.assertEqual(info.revision, "a" * 40)
        self.assertTrue(info.dirty)
        self.assertFalse((self.root / "wheel" / ".git").exists())
        saved = metadata.get_version_info(destination.parent, "1.2.3")
        self.assertEqual(saved, info)

    def test_source_date_epoch_controls_build_time_without_inventing_revision(self):
        destination = self.root / "build" / metadata.METADATA_FILE
        with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "0"}):
            info = metadata.write_build_metadata(destination, self.package, "1.2.3")
        self.assertEqual(info.build_date, "1970-01-01T00:00:00+00:00")
        self.assertIsNone(info.revision)
        self.assertIsNone(info.dirty)

    def test_runtime_uses_package_resources_for_saved_data(self):
        self.save()
        with patch.object(metadata.resources, "files", return_value=self.package), \
                patch.object(sys, "frozen", True, create=True), \
                patch.object(metadata, "__version__", "1.2.3"), \
                patch.object(subprocess, "run", side_effect=AssertionError("Git called")):
            info = metadata.get_version_info()
        self.assertEqual(info.revision, "a" * 40)


@unittest.skipUnless(shutil.which("git"), "Git is required for checkout tests")
class TestCheckoutProvenance(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="d2g_git_metadata_")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.package = self.root / "source" / "dxf2gcode"
        self.package.mkdir(parents=True)
        (self.package.parent / "pyproject.toml").write_text("[project]\nname='dxf2gcode'\n")
        (self.package / "_version.py").write_text("__version__ = '1.2.3'\n")
        self.git("init", "--initial-branch=develop")
        self.git("config", "user.name", "Metadata Test")
        self.git("config", "user.email", "metadata@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", str(self.root / ".git" / "hooks"))
        self.git("add", ".")
        self.git("commit", "-m", "test(meta): create source fixture")

    def git(self, *arguments):
        return subprocess.check_output(["git", "-C", str(self.root), *arguments],
                                       stderr=subprocess.STDOUT, text=True).strip()

    def info(self):
        return metadata.get_version_info(self.package, "1.2.3")

    def test_clean_checkout_branch_changes_commits_and_dirty_state(self):
        first = self.info()
        self.assertEqual(first.origin, "checkout")
        self.assertEqual(first.branch, "develop")
        self.assertFalse(first.dirty)
        self.assertTrue(first.commit_date)
        self.git("switch", "-c", "feature/metadata")
        (self.package / "change.py").write_text("changed = True\n")
        self.assertTrue(self.info().dirty)
        self.git("add", ".")
        self.git("commit", "-m", "test(meta): update source fixture")
        second = self.info()
        self.assertFalse(second.dirty)
        self.assertEqual(second.branch, "feature/metadata")
        self.assertNotEqual(second.revision, first.revision)
        self.assertEqual(second.version, first.version)

    def test_detached_head_has_revision_but_no_branch(self):
        self.git("checkout", "--detach")
        info = self.info()
        self.assertTrue(info.revision)
        self.assertIsNone(info.branch)

    def test_git_failure_does_not_reuse_stale_saved_metadata(self):
        data = dict(asdict(metadata.VersionInfo("1.2.3", revision="old", dirty=False)), schema=1)
        (self.package / metadata.METADATA_FILE).write_text(json.dumps(data))
        with patch.object(subprocess, "run", side_effect=FileNotFoundError("Git missing")):
            self.assertEqual(self.info(), metadata.VersionInfo("1.2.3"))

    def test_source_archive_copies_build_metadata_without_consulting_enclosing_git(self):
        destination = self.root / "archive" / "source" / "dxf2gcode"
        info = metadata.write_build_metadata(destination / metadata.METADATA_FILE,
                                              self.package, "1.2.3")
        (destination.parent / "pyproject.toml").write_text("[project]\nname='dxf2gcode'\n")
        with patch.object(subprocess, "run", side_effect=AssertionError("Enclosing Git queried")):
            saved = metadata.get_version_info(destination, "1.2.3")
        self.assertEqual(saved, info)

    def test_build_captures_checkout_without_writing_into_source_package(self):
        target = self.root / "build" / "dxf2gcode" / metadata.METADATA_FILE
        info = metadata.write_build_metadata(target, self.package, "1.2.3")
        self.assertEqual(info.origin, "build")
        self.assertEqual(info.branch, "develop")
        self.assertFalse(info.dirty)
        self.assertFalse((self.package / metadata.METADATA_FILE).exists())

    def test_generated_release_tree_does_not_mark_the_captured_source_dirty(self):
        info = metadata.capture_build_info(self.package, "1.2.3")
        self.assertFalse(info.dirty)
        destination = self.root / "release-tree" / "dxf2gcode" / metadata.METADATA_FILE
        destination.parent.mkdir(parents=True)
        (destination.parent / "generated.py").write_text("generated = True\n")
        self.assertTrue(self.info().dirty)
        metadata.write_build_metadata(destination, info=info)
        saved = metadata.get_version_info(destination.parent, "1.2.3")
        self.assertFalse(saved.dirty)
        self.assertEqual(saved.revision, info.revision)


class TestVersionPresentation(unittest.TestCase):
    def test_html_escapes_branch_names_and_distinguishes_dirty_state(self):
        from dxf2gcode.presentation.qt.versioninfo import version_details_html
        info = metadata.VersionInfo("1.2.3", revision="a" * 40,
                                    branch="feature/<demo>&", dirty=True,
                                    origin="checkout")
        html = version_details_html(info)
        self.assertIn("1.2.3", html)
        self.assertIn("feature/&lt;demo&gt;&amp;", html)
        self.assertNotIn("feature/<demo>", html)
        self.assertIn("aaaaaaaaaaaa", html)
        self.assertIn("Local changes", html)
        self.assertNotIn("$Date", html)

    def test_missing_branch_and_missing_provenance_have_distinct_labels(self):
        from dxf2gcode.presentation.qt.versioninfo import version_details_html
        detached = metadata.VersionInfo("1.2.3", revision="a" * 40, origin="build")
        self.assertIn("No active branch", version_details_html(detached))
        unknown = version_details_html(metadata.VersionInfo("1.2.3"))
        self.assertNotIn("No active branch", unknown)
        self.assertIn("Not available", unknown)

    def test_compiled_catalogs_contain_every_new_label(self):
        from dxf2gcode.presentation.qt.qt_compat.QtCore import QTranslator
        import xml.etree.ElementTree as ET

        application = ast.parse((SOURCE / "dxf2gcode/presentation/qt/application.py").read_text(encoding="utf-8"))
        template = next(node.args[0].value for node in ast.walk(application)
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "tr" and node.args
                        and isinstance(node.args[0], ast.Constant)
                        and isinstance(node.args[0].value, str)
                        and node.args[0].value.startswith("<html><h2><center>You are using"))

        for language in ("de", "fr", "ru"):
            with self.subTest(language=language):
                catalog = SOURCE / "i18n" / ("dxf2gcode_" + language)
                translator = QTranslator()
                self.assertTrue(translator.load(str(catalog.with_suffix(".qm"))))
                about = translator.translate("MainWindow", template)
                self.assertTrue(about, "Updated About template is untranslated")
                self.assertEqual(about.count("%s"), 1)
                tree = ET.parse(catalog.with_suffix(".ts"))
                context = next(c for c in tree.getroot().findall("context")
                               if c.findtext("name") == "VersionInfo")
                self.assertEqual(len(context.findall("message")), 14)
                for message in context.findall("message"):
                    text = translator.translate("VersionInfo", message.findtext("source"))
                    self.assertEqual(text, message.findtext("translation"))
                    self.assertNotIn("?", text)


if __name__ == "__main__":
    unittest.main()
