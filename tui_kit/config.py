"""An app's hand-edited config.yaml: the theme it names, and saving one setting at a time."""

import shutil
from difflib import get_close_matches
from pathlib import Path

import yaml

from .theme import TERMINAL_THEME, default_theme, is_known_theme, list_themes


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


def save_setting(key: str, value: str, path: Path) -> str | None:
    """Set key to value in a hand-written config, leaving the rest as it was; a warning when it cannot."""
    try:
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        updated = _with_setting(text, key, value)
        # Through a link, the file it points at (the config may live in a dotfiles repository)
        target = path.resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        # Written aside, then moved over the config, so a crash never leaves it half written
        temporary = target.with_name(f".{target.name}.tmp")
        temporary.write_text(updated, encoding="utf-8")
        if target.exists():
            # A config kept private stays private
            shutil.copymode(target, temporary)
        temporary.replace(target)
    except yaml.YAMLError:
        return f"{key}: not saved, {path} is not valid YAML"
    except (OSError, ValueError) as error:
        return f"{key}: not saved to {path}: {error}"
    return None


def _with_setting(text: str, key: str, value: str) -> str:
    """text with key's value replaced, or key added at the end; ValueError unless it reads back the same but for key."""
    root = yaml.compose(text)
    if root is None:
        updated = _add_line(text, key, value)
    elif not isinstance(root, yaml.MappingNode):
        raise ValueError("the file is not a mapping of settings")
    else:
        value_node = _last_value(root, key)
        if value_node is not None:
            updated = _replace_value(text, value_node, value)
        elif root.flow_style:
            raise ValueError("the file is not a mapping written one key per line")
        else:
            updated = _add_line(text, key, value)

    before = yaml.safe_load(text) or {}
    expected = {**before, key: value}
    if yaml.safe_load(updated) != expected:
        raise ValueError("the file is written in a way that cannot be changed safely")
    return updated


def _last_value(mapping: yaml.MappingNode, key: str) -> yaml.Node | None:
    found = None
    for key_node, value_node in mapping.value:
        # No break: yaml keeps the last one when a key is given twice
        if key_node.value == key:
            found = value_node
    return found


def _replace_value(text: str, value_node: yaml.Node, value: str) -> str:
    start = value_node.start_mark.index
    end = value_node.end_mark.index
    old = text[start:end]
    # A block scalar's span ends with its line breaks, which the next key needs
    line_breaks = old[len(old.rstrip()):]
    return text[:start] + value + line_breaks + text[end:]


def _add_line(text: str, key: str, value: str) -> str:
    line = f"{key}: {value}\n"
    if not text.strip():
        return line
    return f"{text.rstrip()}\n{line}"
