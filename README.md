# ouikit

The parts shared by the Textual apps [ouie](https://github.com/jmoniatte/ouie),
[ouifi](https://github.com/jmoniatte/ouifi), flotte and yafyaf-tui: the base16 themes, the
terminal's own palette, the theme picker (`t`), the header and its messages, the Help panel,
dialogs, the startup check and the shortcut list the Help panel reads.

Not published anywhere. An app pulls it from the folder next to it:

```toml
dependencies = ["ouikit"]

[tool.uv.sources]
ouikit = { path = "../ouikit", editable = true }
```

## Development

```bash
uv run python -m unittest discover -s tests
uv run ruff check .
uv run python scripts/sync_themes.py   # refresh the themes from upstream
```
