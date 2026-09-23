import asyncio
import tempfile
import unittest
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Link, Static

from ouikit import STYLE_FILES
from ouikit.app_header import AppHeader
from ouikit.base_app import HELP_BINDING, THEME_BINDING, BaseApp
from ouikit.header_notification import HeaderNotification
from ouikit.help_screen import HelpScreen
from ouikit.shortcuts import ACTIONS


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


class ListView(Widget):
    BINDINGS = [Binding("m", "mute", "Mute", group=ACTIONS)]


class FullApp(BaseApp):
    CSS = "\n".join(path.read_text() for path in STYLE_FILES)
    TITLE = "demo"
    VERSION = "1.2.3"
    REPOSITORY_URL = "https://example.com/demo"
    HELP_BINDINGS = (ListView.BINDINGS,)
    BINDINGS = [HELP_BINDING, THEME_BINDING, Binding("q", "quit", "Quit", group="General")]

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
                    self.assertEqual(keys, ["m", "?", "t", "q"])
                    self.assertEqual(app.screen.query_one("#panel-version").render().plain, "1.2.3")
                    self.assertEqual(app.screen.query_one(Link).url, "https://example.com/demo")

                    await pilot.press("escape", "question_mark")
                    await pilot.pause()
                    self.assertIsInstance(app.screen, HelpScreen)
                    # Every modal opens on the same row
                    self.assertEqual(app.screen.query_one("Vertical").region.y, 1)
                    await pilot.press("escape", "t")
                    await pilot.pause()
                    self.assertEqual(app.screen.query_one("#theme-picker").region.y, 1)

        asyncio.run(main())


if __name__ == "__main__":
    unittest.main()
