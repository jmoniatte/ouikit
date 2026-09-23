from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Link, Static

from . import shortcuts as shortcut_help
from .panel import PanelScreen


class HelpScreen(PanelScreen):
    """The documented shortcuts, read off the bindings so the two cannot drift, with the version and the repository.

    It reads the app's HELP_BINDINGS, BINDINGS, TITLE, VERSION and REPOSITORY_URL.
    """

    def _sections(self) -> list[tuple[str, tuple[shortcut_help.Shortcut, ...]]]:
        sources = (*self.app.HELP_BINDINGS, self.app.BINDINGS)
        return [(section, shortcut_help.for_section(section, *sources)) for section in shortcut_help.SECTIONS]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Help", id="dialog-title")
            with Horizontal(id="shortcuts-sections"):
                for section, shortcuts in self._sections():
                    with Vertical(id=f"shortcuts-{section.lower()}", classes="shortcuts-section"):
                        yield Static(section.upper(), classes="section-title")
                        for shortcut in shortcuts:
                            with Horizontal(classes="shortcut-row"):
                                yield Static(shortcut.key, classes="shortcut-key")
                                yield Static(shortcut.description, classes="shortcut-desc")
            yield Static("", id="panel-footer-spacer")
            with Horizontal(id="panel-footer"):
                yield Button("Close", id="btn-close")
                yield Static("", classes="spacer")
                link = Link(self.app.TITLE, url=self.app.REPOSITORY_URL, id="panel-repository")
                link.can_focus = False  # Close stays the only thing Tab can reach
                yield link
                yield Static(self.app.VERSION, id="panel-version")
