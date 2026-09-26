"""The theme line of an app's hand-edited config.yaml; the app reads the rest itself."""

import re
from difflib import get_close_matches
from pathlib import Path

from .theme import TERMINAL_THEME, default_theme, is_known_theme, list_themes

_THEME_LINE = re.compile(r"^theme:.*$", re.MULTILINE)


def read_theme(value: object) -> tuple[str, str | None]:
    """The theme to use for a config value, and a warning when the value names no theme."""
    if not isinstance(value, str) or not value.strip():
        return TERMINAL_THEME, None
    value = value.strip()
    if is_known_theme(value):
        return value, None
    theme = default_theme()
    # Too many themes to list; a near-miss is the useful hint.
    near = get_close_matches(value, list_themes(), n=3)
    hint = f" Did you mean: {', '.join(near)}?" if near else ""
    return theme, f"theme: '{value}' is not installed, using '{theme}'.{hint}"


def save_theme(theme: str, path: Path) -> None:
    """Persist the theme, leaving the rest of a hand-written config untouched."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = f"theme: {theme}"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    updated, replaced = _THEME_LINE.subn(line, text, count=1)
    path.write_text(updated if replaced else f"{line}\n{text}", encoding="utf-8")
