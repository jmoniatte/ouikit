import tempfile
import unittest
from pathlib import Path

import yaml

from tui_kit.config import read_theme, save_setting
from tui_kit.theme import default_theme


class ReadThemeTest(unittest.TestCase):
    def test_known_themes_are_kept_and_a_missing_value_means_terminal(self) -> None:
        self.assertEqual(read_theme("one-light"), ("one-light", None))
        self.assertEqual(read_theme(" terminal "), ("terminal", None))
        self.assertEqual(read_theme(None), ("terminal", None))
        self.assertEqual(read_theme(42), ("terminal", None))

    def test_a_theme_that_is_not_installed_warns_with_a_near_miss(self) -> None:
        theme, warning = read_theme("onelight")
        self.assertEqual(theme, default_theme())
        self.assertIn("'onelight' is not installed", warning)
        self.assertIn("one-light", warning)


class SaveSettingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.path = Path(self.enterContext(tempfile.TemporaryDirectory())) / "app" / "config.yaml"

    def saved(self, before: str) -> str:
        """The file after saving units: imperial over before, checking it reads back as saved."""
        self.path.parent.mkdir(exist_ok=True)
        self.path.write_text(before)
        self.assertIsNone(save_setting("units", "imperial", self.path))
        self.assertEqual(yaml.safe_load(self.path.read_text())["units"], "imperial")
        return self.path.read_text()

    def test_replaces_only_the_value_whatever_the_style(self) -> None:
        self.assertEqual(self.saved("theme: nord  # mine\nunits: metric\nweek_start: sunday"), "theme: nord  # mine\nunits: imperial\nweek_start: sunday")
        self.assertEqual(self.saved("{theme: nord, units: metric}\n"), "{theme: nord, units: imperial}\n")
        self.assertEqual(self.saved("units: >-\n  metric\ntheme: nord\n"), "units: imperial\ntheme: nord\n")
        # yaml keeps the last of a key given twice, so that is the one to change
        self.assertEqual(self.saved("units: metric\nunits: metric\n"), "units: metric\nunits: imperial\n")

    def test_adds_the_key_at_the_end_when_missing(self) -> None:
        self.assertEqual(self.saved("theme: nord"), "theme: nord\nunits: imperial\n")
        self.assertEqual(self.saved("# only a comment\n"), "# only a comment\nunits: imperial\n")
        self.assertEqual(self.saved(""), "units: imperial\n")
        self.path.unlink()
        self.path.parent.rmdir()
        self.assertIsNone(save_setting("units", "imperial", self.path))
        self.assertEqual(self.path.read_text(), "units: imperial\n")

    def test_warns_and_leaves_the_file_alone_when_it_cannot_save_safely(self) -> None:
        self.path.parent.mkdir()
        for text in ("- a list\n", "{theme: nord}\n", "theme: [unclosed\n"):
            self.path.write_text(text)
            self.assertIn("units: not saved", save_setting("units", "imperial", self.path))
            self.assertEqual(self.path.read_text(), text)

    def test_writes_through_a_link_to_the_file_it_points_at(self) -> None:
        self.path.parent.mkdir()
        target = self.path.with_name("dotfiles.yaml")
        target.write_text("units: metric\n")
        self.path.symlink_to(target)
        self.assertIsNone(save_setting("units", "imperial", self.path))
        self.assertTrue(self.path.is_symlink())
        self.assertEqual(target.read_text(), "units: imperial\n")

    def test_save_setting_keeps_the_files_permissions(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("units: metric\n")
        self.path.chmod(0o600)
        self.assertIsNone(save_setting("units", "imperial", self.path))
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
