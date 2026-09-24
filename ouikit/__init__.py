from pathlib import Path

STYLES_DIR = Path(__file__).parent / "styles"
# Joined before the app's own stylesheets, so an app changes a rule by writing it again.
# panel comes after modal_forms so Help keeps its own width rather than every modal's
STYLE_FILES = tuple(STYLES_DIR / f"{name}.tcss" for name in ("base", "header", "modal_forms", "dialogs", "panel", "tabs", "theme_picker"))
