from pathlib import Path

STYLES_DIR = Path(__file__).parent / "styles"
# Joined before the app's own stylesheets, so an app changes a rule by writing it again
STYLE_FILES = tuple(STYLES_DIR / f"{name}.tcss" for name in ("base", "header", "panel", "modal_forms", "dialogs", "theme_picker"))
