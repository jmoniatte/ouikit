import sys
from collections.abc import Callable

from textual.app import App

from .terminal_theme import query_terminal
from .theme import register_terminal_scheme


def start(name: str, make_app: Callable[[], App]) -> None:
    """Check for a terminal, read its colors, then build and run the app.

    make_app is called only after the terminal's colors are known, since the app loads its theme when built.
    """
    # Textual spins at 100% CPU reading a stdin that is a pipe at end of file.
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        print(f"{name}: needs a terminal on stdin and stdout", file=sys.stderr)
        raise SystemExit(1)

    # Must run before Textual takes the tty; a silent terminal just yields None.
    terminal = query_terminal()
    register_terminal_scheme(terminal.scheme, terminal.light_background)
    make_app().run()
