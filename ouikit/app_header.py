from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from .header_notification import HeaderNotification


class HelpRequested(Message):
    """The app's name in the header was clicked."""


class TitleLink(Static):
    """The app's name; clicking it opens Help, like ? does."""

    def on_click(self) -> None:
        self.post_message(HelpRequested())


class AppHeader(Horizontal):
    """The title bar, one line: the app's name, the messages in the middle, then the widgets passed in."""

    def __init__(self, *right: Widget) -> None:
        super().__init__(id="app-header")
        self._right = right

    def compose(self) -> ComposeResult:
        # The version is on the Help panel
        yield TitleLink(self.app.TITLE, id="app-title", markup=False)
        yield Static("", classes="header-notification-spacer")
        yield HeaderNotification()
        yield Static("", id="header-spacer")
        yield from self._right
