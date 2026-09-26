import asyncio
import unittest

from textual.app import App, ComposeResult
from textual.widgets import Button, Static

from tui_kit import STYLE_FILES
from tui_kit.dialog import ConfirmDialog, Dialog, DialogButton
from tui_kit.theme import load_palette


class Host(App):
    CSS = "\n".join(path.read_text() for path in STYLE_FILES)

    def __init__(self) -> None:
        super().__init__()
        self.results: list[object] = []

    def get_css_variables(self) -> dict[str, str]:
        return {**super().get_css_variables(), **load_palette("onedark")}

    def compose(self) -> ComposeResult:
        yield Static("host")


class DialogTests(unittest.TestCase):
    def _run(self, dialog, keys):
        async def main():
            app = Host()
            async with app.run_test() as pilot:
                app.push_screen(dialog, callback=app.results.append)
                await pilot.pause()
                focused = app.focused.id if isinstance(app.focused, Button) else None
                await pilot.press(*keys)
                await pilot.pause()
            return focused, app.results

        return asyncio.run(main())

    def test_confirm_starts_on_no_and_escape_is_no(self):
        self.assertEqual(self._run(ConfirmDialog("Delete it?"), ["enter"]), ("cancel-btn", [False]))
        self.assertEqual(self._run(ConfirmDialog("Delete it?"), ["escape"]), ("cancel-btn", [False]))
        self.assertEqual(self._run(ConfirmDialog("Delete it?"), ["tab", "enter"]), ("cancel-btn", [True]))

    def test_a_dialog_returns_the_pressed_button_and_can_ignore_escape(self):
        buttons = [DialogButton("Discard", "discard", "discard-btn", kind="danger"), DialogButton("Keep", "keep", "keep-btn")]
        dialog = lambda: Dialog("Not saved", "What now?", buttons, focus="keep-btn")  # noqa: E731
        self.assertEqual(self._run(dialog(), ["escape"]), ("keep-btn", []))
        self.assertEqual(self._run(dialog(), ["enter"]), ("keep-btn", ["keep"]))


if __name__ == "__main__":
    unittest.main()
