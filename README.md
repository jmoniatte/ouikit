# tui-kit

The parts shared by the Textual apps [outils](https://github.com/jmoniatte/outils), flotte and
yafyaf-tui: the base16 themes, the
terminal's own palette, the theme picker (`t`), copying the selected text (`y`), the header and its messages, the Help panel,
dialogs, the startup check and the shortcut list the Help panel reads.

Not published on PyPI. An app installs it from GitHub, or from the folder next to it while
working on both:

```toml
dependencies = ["tui-kit"]

[tool.uv.sources]
tui-kit = { git = "ssh://git@github.com/jmoniatte/tui-kit.git", branch = "master" }
# tui-kit = { path = "../tui-kit", editable = true }
```

The package installs as `tui-kit` and imports as `tui_kit`, since Python names cannot hold a dash.

## Development

```bash
uv run python -m unittest discover -s tests
uv run ruff check .
uv run python scripts/sync_themes.py   # refresh the themes from upstream
```
