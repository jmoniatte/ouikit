# ouikit

The code shared by the Textual apps ouie, ouifi, flotte and yafyaf-tui, so they look the same
and offer the same themes. It is not published: each app depends on the folder next to it
(`[tool.uv.sources] ouikit = { path = "../ouikit", editable = true }`), so a change here reaches
every app at once. Run an app's tests after changing something here.

Only code that is the same in every app belongs here. What one app does (its own widgets, its
own stylesheets, its config fields) stays in that app.

## Rules

- Do not git commit unless asked
- Never hardcode a color in a `.tcss` file

## Test

Run both from the git root.

```bash
uv run python -m unittest discover -s tests
uv run ruff check .
```

There is no pytest. `ruff` is pinned in the `dev` dependency group, so use `uv run ruff`.

## Structure

```
ouikit/                 # git root + pyproject.toml
  ouikit/
    __init__.py         # STYLE_FILES: the stylesheets an app joins before its own
    base_app.py         # BaseApp: the theme (t opens the picker, the choice is saved), messages in the header, Help,
                        # and the commands still running stopped on quit
    processes.py        # run() for every command an app starts, so stop_all() can kill them on quit
    app_header.py       # AppHeader: the app's name (opens Help), the messages, then the app's own widgets
    header_notification.py  # HeaderNotification: the message area in the header
    help_screen.py      # HelpScreen: the shortcuts, the version and the repository link
    dialog.py           # Dialog (a title, a message and a row of DialogButtons) and ConfirmDialog
    start.py            # start(): refuses to run without a terminal, reads its colors, runs the app
    theme.py            # base16 scheme loading, palette derivation
    terminal_theme.py   # OSC queries that read the terminal's own palette before Textual starts
    config.py           # The theme line of an app's config.yaml: read_theme, save_theme
    theme_picker.py     # The picker screen
    panel.py            # PanelScreen, the base of Help
    shortcuts.py        # Help screen contents, read off the bindings
    styles/             # base, header, modal_forms, dialogs, panel, tabs, theme_picker .tcss (in STYLE_FILES order);
                        # themes/*.yaml (base16 schemes)
  scripts/sync_themes.py
```

## Using it in an app

The app subclasses `BaseApp` and passes the theme from its config and the config file to save
it to: `super().__init__(config.theme, CONFIG_FILE)`. `read_theme` turns the config's `theme`
value into a theme and maybe a warning. The app also sets:

- `TITLE`, `VERSION` and `REPOSITORY_URL`, shown in the header and on Help
- `HELP_BINDINGS`: the `BINDINGS` of its widgets whose keys Help lists, before the app's own
- `HELP_BINDING` and `THEME_BINDING` in its `BINDINGS`, where `?` and `t` should sit on Help

It yields `AppHeader(...)` first in `compose`, passing the widgets it wants on the right of the
header, if any. Help opens from `?` or a click on the app's name.

The app joins `ouikit.STYLE_FILES` before its own stylesheets, so it changes one of ouikit's
rules by writing the same selector again in its own files.

Every modal (panels, dialogs, the picker) opens on the same row: `base.tcss` gives the box
(`ModalScreen > Vertical`) a one-row top margin. Do not set another top margin on a modal's box
in an app, or that app's modals open lower than the others. Setting only `margin-bottom` on a
box resets its top margin to 0 in Textual, so a box that needs a bottom margin sets
`margin: 1 0` (the picker does). Padding on the screen would do the
same without the box running one row past the bottom, but Textual paints that row solid instead
of letting the app show through.

`__main__` parses its own arguments, then calls `start("<name>", make_app)`. `start` exits
with an error when stdin or stdout is not a terminal (Textual spins at 100% CPU on a pipe at end
of file), then asks the terminal for its colors before Textual takes the tty, and only then calls
`make_app`, since the app loads its theme when it is built.

The theme is not a setting in any panel: `t` is the only way to change it from the app.

## Dialogs

`Dialog` is a title, a message, an optional one-line detail and a row of `DialogButton`s; each
button returns its `result` and has a `kind` (`plain`, `danger` or `action`) that
`dialogs.tcss` colors. The first button, or the one named by `focus`, starts focused, so Enter
is never a surprise. Escape returns `escape`, or does nothing when the choice must be
deliberate. `ConfirmDialog` is yes or no, with focus on the cancel button and Escape as no. An
app builds its own dialogs on `Dialog` (yafyaf-tui's not-saved dialog does).
`modal_forms.tcss` styles the box, title, inputs and buttons of every modal form.

## Help, tabs and commands

Help looks the same in every app: as wide as its two columns of shortcuts (`#shortcuts-sections`
is `width: auto` and the footer `width: 100%` of the panel), the whole window height when needed,
and no blank line under the title. `panel.tcss` comes after `modal_forms.tcss` in `STYLE_FILES`
so its `width: auto` wins over every modal's `width: 60`. Apps do not resize it.

`tabs.tcss` gives every `TabbedContent` the same look: the active tab bold over a blue bar, the
rest dimmed, a thin rule across.

An app that starts commands runs them with `processes.run` (like `subprocess.run` with captured
text, plus an optional `input`). `BaseApp.on_unmount` calls `processes.stop_all`, so quitting
never waits for a slow command a worker thread is still on.

## Messages

`BaseApp.notify` shows every message, errors included, in the `HeaderNotification` of the
topmost screen that has one, instead of as a toast; a screen with no header falls back to a
toast. Markup is off unless the caller passes `markup=True`, since messages carry device names,
file paths and errors that may contain brackets. The message stays for its timeout
(`App.NOTIFICATION_TIMEOUT` by default), then the area clears. `header_notification.tcss` keeps
it on one line in the middle of the header, cut with "…"; errors wrap onto up to three lines,
since the end of an error is often the useful part.

## Themes

`ouikit/styles/themes/` holds the whole
[base16 catalogue](https://github.com/tinted-theming/schemes), one scheme file
per theme, copied in unmodified - never hand-edit one. `theme.py` maps 11 of
the 16 slots straight onto the TCSS variables the stylesheets use and derives the
other two (`$bg-dark`, `$gutter`) from the scheme's greyscale ramp, so adding a
theme means adding a file and nothing else. `read_theme` rejects a `theme` that
does not name one of them.

`theme: terminal` (the default) is not a file. `terminal_theme.py` asks the
terminal for its colours with OSC 10, 11 and 4 before Textual starts, maps the
ANSI palette onto base16 slots and derives the rest, and the app's `__main__` registers
the result with `theme.register_terminal_scheme`. A terminal that stays silent,
or whose `$fg` on `$bg` fails `MIN_TEXT_CONTRAST`, registers no scheme: the app
then shows `theme.default_theme()` and the picker does not list `terminal`. That
default is `one-light` when the terminal reported a light background and
`onedark` otherwise, so a rejected light terminal never gets a dark app. The
surfaces ANSI has no slot for (`base01`, `base02`) are placed by contrast
against the background rather than by a fixed RGB step, which lands the same
distance out on light and dark ramps.
`theme.effective_theme` is the name to compare against or show as current.

Filenames are the upstream scheme slugs verbatim, and that is exactly what
`config.yaml` sets -- no aliases, no renaming. Upstream is inconsistent about
hyphens (`onedark` but `one-light`); follow it rather than tidying it.

`scripts/sync_themes.py` refreshes the directory from upstream. It is the only
place the editorial rule lives: a scheme whose own `$fg` on `$bg` falls below
`MIN_TEXT_CONTRAST` (WCAG AA) is skipped, since the stylesheets cannot rescue it.
Do not hand-add a scheme the script would reject.

The picker previews as the cursor moves (`BaseApp.apply_theme`); `enter` keeps the theme
through `BaseApp.set_theme`, which persists it, and `esc` restores the one it opened on. The
palette is served from `BaseApp.get_css_variables` rather than baked into `CSS`, and
`refresh_css` repaints everything, so an app's widgets should take their colors from TCSS
(component classes for anything drawn by hand) to follow a theme change. What an app bakes into
Rich text instead reads `BaseApp.palette`, and the app repaints it by overriding `apply_theme`
(ouifi's network list does).
