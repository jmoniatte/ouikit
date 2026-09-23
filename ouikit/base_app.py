from pathlib import Path

from textual import on
from textual.app import App
from textual.binding import Binding
from textual.notifications import Notification, SeverityLevel

from .app_header import HelpRequested
from .config import save_theme
from .header_notification import HeaderNotification
from .help_screen import HelpScreen
from .shortcuts import GENERAL
from .theme import effective_theme, load_palette
from .theme_picker import ThemePicker

# Apps list these in their own BINDINGS, where they should sit on the Help panel
HELP_BINDING = Binding("question_mark", "help", "Help", key_display="?", group=GENERAL)
THEME_BINDING = Binding("t", "show_themes", "Change theme", group=GENERAL)


class BaseApp(App):
    """What every app shares: a base16 theme picked with t, messages shown in the header, and Help.

    The palette is served from get_css_variables rather than baked into CSS, so
    apply_theme can swap it without restarting.
    """

    # Shown on the Help panel, next to TITLE
    VERSION = ""
    REPOSITORY_URL = ""
    # The BINDINGS of the widgets whose keys Help lists, before the app's own
    HELP_BINDINGS: tuple = ()

    def __init__(self, theme_name: str, config_file: Path) -> None:
        self.theme_name = theme_name
        self._config_file = config_file
        self._palette = load_palette(theme_name)
        super().__init__()

    # -- theme

    @property
    def palette(self) -> dict[str, str]:
        """The theme's colors by TCSS variable name, for what an app draws with Rich rather than TCSS."""
        return self._palette

    def get_css_variables(self) -> dict[str, str]:
        """Serve the base16 palette to the stylesheet alongside Textual's own."""
        return {**super().get_css_variables(), **self._palette}

    def action_show_themes(self) -> None:
        """Browse themes, applying each one as the cursor moves."""
        self.push_screen(ThemePicker(effective_theme(self.theme_name)), callback=self._theme_chosen)

    def _theme_chosen(self, theme_name: str | None) -> None:
        if theme_name is not None:
            self.set_theme(theme_name)

    def set_theme(self, theme_name: str) -> None:
        """Apply a theme and remember it for next launch."""
        if effective_theme(theme_name) == effective_theme(self.theme_name):
            return
        self.apply_theme(theme_name)
        self.theme_name = theme_name
        save_theme(theme_name, self._config_file)
        self.notify(f"Theme set to {theme_name}")

    def apply_theme(self, theme_name: str) -> None:
        """Swap the palette and repaint in place."""
        self._palette = load_palette(theme_name)
        self.refresh_css()

    # -- notifications

    def notify(
        self,
        message: str,
        *,
        title: str = "",
        severity: SeverityLevel = "information",
        timeout: float | None = None,
        markup: bool = False,
    ) -> None:
        """Show the message in the header instead of as a toast.

        Markup is off unless asked for: messages carry names and errors, which may contain brackets.
        """
        notification = Notification(
            message, title, severity, self.NOTIFICATION_TIMEOUT if timeout is None else timeout, markup=markup
        )
        self.call_later(self._show_notification, notification)

    def _show_notification(self, notification: Notification) -> None:
        for screen in reversed(self.screen_stack):
            headers = list(screen.query(HeaderNotification))
            if headers:
                headers[0].show_notification(notification)
                return
        super().notify(
            notification.message,
            title=notification.title,
            severity=notification.severity,
            timeout=max(notification.time_left, 0),
            markup=notification.markup,
        )

    # -- help

    @on(HelpRequested)
    def action_help(self) -> None:
        self.push_screen(HelpScreen())
