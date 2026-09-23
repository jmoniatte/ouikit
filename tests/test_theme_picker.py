import asyncio
import tempfile
import unittest
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Input, Static

from ouikit import STYLE_FILES
from ouikit.theme import load_palette
from ouikit.theme_picker import ThemePicker
from ouikit.base_app import THEME_BINDING, BaseApp


class PickerApp(BaseApp):
    """Records every theme applied, so the tests can follow the picker."""

    CSS = "\n".join(path.read_text() for path in STYLE_FILES)
    BINDINGS = [THEME_BINDING]

    def __init__(self, config_file: Path) -> None:
        super().__init__("onedark", config_file)
        self.applied: list[str] = []
        self.result: str | None | object = "unset"

    def compose(self) -> ComposeResult:
        yield Static("host")

    def apply_theme(self, name: str) -> None:
        self.applied.append(name)
        super().apply_theme(name)


class ThemePickerTests(unittest.TestCase):
    def _run(self, body):
        async def main():
            with tempfile.TemporaryDirectory() as tmp:
                app = PickerApp(Path(tmp) / "config.yaml")
                async with app.run_test() as pilot:
                    app.push_screen(
                        ThemePicker("onedark"),
                        callback=lambda value: setattr(app, "result", value),
                    )
                    await pilot.pause()
                    await body(app, pilot)
            return app

        return asyncio.run(main())

    def test_highlighting_a_row_applies_it_and_enter_keeps_it(self):
        async def body(app, pilot):
            picker = app.screen
            # Opens on the configured theme, already applied.
            self.assertEqual(app.applied[-1], "onedark")
            table = picker.query_one("#theme-table", DataTable)
            self.assertEqual(table.row_count, len(picker._names))

            await pilot.press("down")
            await pilot.pause()
            moved = app.applied[-1]
            self.assertNotEqual(moved, "onedark")

            await pilot.press("enter")
            await pilot.pause()
            self.assertEqual(app.result, moved)

        self._run(body)

    def test_filtering_narrows_the_list_and_applies_the_first_match(self):
        async def body(app, pilot):
            picker = app.screen
            picker.query_one("#theme-filter", Input).focus()
            await pilot.press(*"dracula")
            await pilot.pause()
            self.assertEqual(picker._names, ["dracula"])
            self.assertEqual(app.applied[-1], "dracula")

        self._run(body)

    def test_escape_restores_the_theme_the_picker_opened_with(self):
        async def body(app, pilot):
            picker = app.screen
            surface = picker.query_one(Vertical).styles.background
            await pilot.press("down", "down")
            await pilot.pause()
            self.assertNotEqual(picker.query_one(Vertical).styles.background, surface)

            await pilot.press("escape")
            await pilot.pause()
            self.assertEqual(app.applied[-1], "onedark")
            self.assertIsNone(app.result)
            self.assertEqual(app._palette, load_palette("onedark"))

        self._run(body)


class BaseAppTests(unittest.TestCase):
    def test_t_opens_the_picker_and_the_chosen_theme_is_served_and_saved(self):
        async def main():
            with tempfile.TemporaryDirectory() as tmp:
                config_file = Path(tmp) / "config.yaml"
                app = PickerApp(config_file)
                self.assertEqual(app.get_css_variables()["bg"], load_palette("onedark")["bg"])
                self.assertNotIn("$bg:", app.CSS)  # variables must not be baked in
                async with app.run_test() as pilot:
                    await pilot.press("t")
                    await pilot.pause()
                    self.assertIsInstance(app.screen, ThemePicker)
                    await pilot.press(*"dracula", "enter")
                    await pilot.pause()
                self.assertEqual(app.theme_name, "dracula")
                self.assertEqual(app.get_css_variables()["bg"], load_palette("dracula")["bg"])
                self.assertEqual(config_file.read_text(), "theme: dracula\n")

        asyncio.run(main())


if __name__ == "__main__":
    unittest.main()
