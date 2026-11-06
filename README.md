# theme.gams

Themes for [GAMS](https://github.com/kkgams/gams).

## Themes

| Name | File | Screenshot | Licenses | Original work |
| --- | --- | --- | --- | --- |
| The98 | [the98.css](https://github.com/kkgams/theme.gams/blob/release/src/themes/the98.css) | Pending | [MIT — 98.css](licenses/98.css.MIT.txt), [Apache-2.0 — GAMS additions](LICENSE) | [98.css by Jordan Scales](https://github.com/jdan/98.css) |
| orange | [orange.css](https://github.com/kkgams/theme.gams/blob/release/src/themes/orange.css) | Pending | [Apache-2.0](LICENSE) | [kkgams / GAMS](https://github.com/kkgams/gams) |

## Development

Edit styles in `src/themes/` and list packaged files in Makefile's `ZIP_FILES`.
`orange` keeps the Host base styling with the GAMS promo accent (`#ec4e00`) and
square corners. The preview Projects are `projects/orange/gams.json` and
`projects/the98/gams.json`. Each links to the canonical `src/` directory;
`make open` selects the Project folder without copying configuration or styles.
Both use the repository's shared `gams_modules/` cache.

| Command | Description |
| --- | --- |
| `make` / `make package` | Build `build.nosync/theme.gams.zip` and `build.nosync/SHA256SUMS`; rebuild only when inputs change. |
| `make open` | Open orange (default) in the released GAMS Host; download the Host when absent. |
| `THEME=the98 make open` | Open The98; `THEME=orange make open` selects orange explicitly. |
| `make tools/gams.app` | Download the Host and its notices without opening it; keep an existing download. |
| `make clean` | Remove generated output, downloaded tools and installed Unit caches; preserve tracked files and unrelated untracked files. |
| `make serve-docs DOCS_PORT=8080` | Serve the documentation locally. |
| `make docs` / `make build-docs` | Build the portable documentation site in `build.nosync/site/`. |
| `make validate-docs` | Check the documentation. |

Packaging needs Make, `zip` and `shasum`. Opening the Project requires macOS
Apple Silicon; the Host downloader uses Python 3, curl and unzip. Documentation
uses Node.js 24 and pinned `justgook/wiki` v1.4.0. Initial downloads need network
access; no sibling checkout is required.

Generated files live in `build.nosync/`; finished Host tools and installed Units
live in `tools/` and `gams_modules/`.
