# theme.gams

The kkgams-maintained theme collection for GAMS. Each theme is a separate CSS
stylesheet; the collection shares one version and release ZIP.

## Themes

| Theme | Source | Release path |
| --- | --- | --- |
| The98 | `src/themes/the98.css` | `themes/the98.css` |

The98 provides a compact Windows 98-style interface. It adapts MIT-licensed
98.css; GAMS-authored additions are Apache-2.0. See [LICENSING.md](LICENSING.md).

## Use a theme

The Host still loads any CSS source configured in `gams.json`; this collection
is not a required registry or a restriction on custom themes. For local CSS:

```json
{
  "ui": {
    "theme": { "url": "themes/my-theme.css" }
  }
}
```

For a published collection, select the stylesheet inside its release ZIP:

```json
{
  "ui": {
    "theme": {
      "url": "https://github.com/kkgams/theme.gams/releases/download/v1.0.0/theme.gams-1.0.0.zip#themes/the98.css"
    }
  }
}
```

Version 1.0.0 is the initial collection candidate, not a publication claim. The
release URL becomes usable after publication. Existing `theme.the98` release
URLs remain valid; update Project pins only after the new release is available.
Omit `ui.theme` to use Host base styling without a theme.

## Develop

Requires Node.js 24, Python 3 and Make.

```sh
make check                  # source, packaging and release safety tests
make open                   # open the local Project with The98 selected
make serve-docs DOCS_PORT=8080
make validate-docs
make docs
```

`make open` uses the local CSS in `gams.json` and downloads the released macOS
Apple Silicon Host to ignored `tools/gams.app` when absent. It sets
`GAMS_APP_CWD`, preserves accompanying notices and never updates an existing
Host implicitly. Pinned released dependencies require network access on first
launch; no sibling checkout is needed.

[Development documentation](docs/index.md) covers adding and checking themes.
[Publishing](PUBLISHING.md) covers matching-tag releases and documentation Pages.
