import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Link, Static

from tui_kit import STYLE_FILES
from tui_kit.app_header import AppHeader
from tui_kit.base_app import COPY_BINDING, HELP_BINDING, THEME_BINDING, BaseApp
from tui_kit.header_notification import HeaderNotification
from tui_kit.help_screen import HelpScreen
from tui_kit.shortcuts import ACTIONS


class HeaderApp(BaseApp):
    CSS = "\n".join(path.read_text() for path in STYLE_FILES)

    def __init__(self, config_file: Path, header: bool = True) -> None:
        super().__init__("onedark", config_file)
        self._header = header

    def compose(self) -> ComposeResult:
        yield HeaderNotification() if self._header else Static("no header")


def shown(app: HeaderApp) -> str:
    header = app.query_one(HeaderNotification)
    return header.render().plain if header.display else ""


class NotificationTests(unittest.TestCase):
    def _run(self, body, header: bool = True):
        async def main():
            with tempfile.TemporaryDirectory() as tmp:
                app = HeaderApp(Path(tmp) / "config.yaml", header)
                async with app.run_test() as pilot:
                    await body(app, pilot)

        asyncio.run(main())

    def test_messages_go_to_the_header_as_plain_text_and_clear_after_the_timeout(self):
        async def body(app, pilot):
            app.notify("Playing on [Headphones]", severity="warning", timeout=0.2)
            await pilot.pause()
            header = app.query_one(HeaderNotification)
            self.assertEqual(shown(app), "Playing on [Headphones]")
            self.assertTrue(header.has_class("-warning"))
            self.assertEqual(len(app._notifications), 0)

            app.notify("[b]bold[/b]", markup=True)
            await pilot.pause()
            self.assertEqual(shown(app), "bold")
            self.assertTrue(header.has_class("-information"))

            app.notify("gone soon", timeout=0.1)
            await pilot.pause(0.3)
            self.assertEqual(shown(app), "")

        self._run(body)

    def test_without_a_header_a_message_is_a_toast(self):
        async def body(app, pilot):
            app.notify("no header here")
            await pilot.pause()
            self.assertEqual([n.message for n in app._notifications], ["no header here"])

        self._run(body, header=False)

    def test_a_theme_that_cannot_be_saved_is_a_warning_and_the_config_is_left_alone(self):
        async def body(app, pilot):
            app._config_file.write_text("- a list\n")
            app.set_theme("nord")
            await pilot.pause()
            self.assertIn("theme: not saved", shown(app))
            self.assertTrue(app.query_one(HeaderNotification).has_class("-warning"))
            self.assertEqual(app._config_file.read_text(), "- a list\n")

        self._run(body)


class ListView(Widget):
    BINDINGS = [Binding("m", "mute", "Mute", group=ACTIONS)]


class FullApp(BaseApp):
    CSS = "\n".join(path.read_text() for path in STYLE_FILES)
    TITLE = "demo"
    VERSION = "1.2.3"
    REPOSITORY_URL = "https://example.com/demo"
    HELP_BINDINGS = (ListView.BINDINGS,)
    BINDINGS = [HELP_BINDING, THEME_BINDING, COPY_BINDING, Binding("q", "quit", "Quit", group="General")]

    def compose(self) -> ComposeResult:
        yield AppHeader(Static("right side", id="extra"))


class HelpTests(unittest.TestCase):
    def test_the_title_and_question_mark_open_help_with_every_documented_key(self):
        async def main():
            with tempfile.TemporaryDirectory() as tmp:
                app = FullApp("onedark", Path(tmp) / "config.yaml")
                async with app.run_test() as pilot:
                    header = app.query_one(AppHeader)
                    self.assertEqual(app.query_one("#app-title").render().plain, "demo")
                    self.assertIs(app.query_one("#extra").parent, header)

                    await pilot.click("#app-title")
                    await pilot.pause()
                    self.assertIsInstance(app.screen, HelpScreen)
                    keys = [key.render().plain for key in app.screen.query(".shortcut-key")]
                    self.assertEqual(keys, ["m", "?", "t", "y", "q"])
                    self.assertEqual(app.screen.query_one("#panel-version").render().plain, "1.2.3")
                    self.assertEqual(app.screen.query_one(Link).url, "https://example.com/demo")

                    await pilot.press("escape", "question_mark")
                    await pilot.pause()
                    self.assertIsInstance(app.screen, HelpScreen)
                    # Every modal opens on the same row, and Help is as wide as its content, not 60
                    panel = app.screen.query_one("Vertical")
                    self.assertEqual(panel.region.y, 1)
                    self.assertLess(panel.region.width, 60)
                    await pilot.press("escape", "t")
                    await pilot.pause()
                    self.assertEqual(app.screen.query_one("#theme-picker").region.y, 1)

        asyncio.run(main())


class CopyTests(unittest.TestCase):
    def test_y_copies_the_selected_text_and_says_so(self):
        async def main():
            with tempfile.TemporaryDirectory() as tmp:
                app = FullApp("onedark", Path(tmp) / "config.yaml")
                async with app.run_test() as pilot:
                    with patch.object(app, "copy_to_clipboard") as copy:
                        await pilot.press("y")
                        await pilot.pause()
                        copy.assert_not_called()
                        self.assertEqual(shown(app), "Nothing selected")

                        # Drag across "right side" in the header, as a mouse would
                        extra = app.query_one("#extra")
                        await pilot.mouse_down(extra, offset=(0, 0))
                        await pilot.hover(extra, offset=(4, 0))
                        await pilot.mouse_up(extra, offset=(4, 0))
                        await pilot.press("y")
                        await pilot.pause()
                        copy.assert_called_once_with("right")
                        self.assertEqual(shown(app), "Selection copied")

        asyncio.run(main())


class QuitTests(unittest.TestCase):
    def test_quitting_stops_the_commands_still_running(self):
        async def main():
            with tempfile.TemporaryDirectory() as tmp, patch("tui_kit.base_app.processes.stop_all") as stop_all:
                app = FullApp("onedark", Path(tmp) / "config.yaml")
                async with app.run_test():
                    stop_all.assert_not_called()
            stop_all.assert_called_once()

        asyncio.run(main())


if __name__ == "__main__":
    unittest.main()
