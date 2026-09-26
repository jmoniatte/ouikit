import tempfile
import unittest
from pathlib import Path

from tui_kit.config import read_theme, save_theme
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


class SaveThemeTest(unittest.TestCase):
    def test_replaces_the_theme_line_and_leaves_the_rest_of_the_file_alone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app" / "config.yaml"
            save_theme("dracula", path)
            self.assertEqual(path.read_text(), "theme: dracula\n")

            path.write_text("# my config\ntheme: onedark\nsomething: else\n")
            save_theme("dracula", path)
            self.assertEqual(path.read_text(), "# my config\ntheme: dracula\nsomething: else\n")

            path.write_text("something: else\n")
            save_theme("nord", path)
            self.assertEqual(path.read_text(), "theme: nord\nsomething: else\n")


if __name__ == "__main__":
    unittest.main()
