# theme.gams

Themes for [GAMS](https://github.com/kkgams/gams).

## Themes

| Name | File | Screenshot | Licenses | Original work |
| --- | --- | --- | --- | --- |
| The98 | [the98.css](https://github.com/kkgams/theme.gams/blob/release/src/themes/the98.css) | Pending | [MIT — 98.css](licenses/98.css.MIT.txt), [Apache-2.0 — GAMS additions](LICENSE) | [98.css by Jordan Scales](https://github.com/jdan/98.css) |
| orange | [orange.css](https://github.com/kkgams/theme.gams/blob/release/src/themes/orange.css) | Pending | [Apache-2.0](LICENSE) | [kkgams / GAMS](https://github.com/kkgams/gams) |
| Codecraft | `themes/codecraft.css` | Pending | [MIT — panel art](licenses/world-of-codecraft.MIT.txt), [Apache-2.0 — CSS](LICENSE) | [World of Codecraft by Kevin Pardo](https://github.com/kevinpardo/world-of-codecraft) |

Codecraft styles panel borders only. [The original slices and atlas](src/art/codecraft/)
ship under `art/codecraft/` in the ZIP. The atlas uses 28 px source slices at 2×
(14 CSS px). The four corners are unchanged in size; the four strips use the
first 480 px of each original edge. The build embeds the atlas in the CSS so it
works without separate asset URLs.

## Development

Edit styles in `src/themes/` and list packaged files in Makefile's `ZIP_FILES`.
`orange` keeps the Host base styling with the GAMS promo accent (`#ec4e00`) and
square corners. `make open` passes the selected `gams_<theme>.json` filename through
`GAMS_CONFIG` and uses this repository as the Project root. An existing environment
or command-line `GAMS_CONFIG` overrides the theme selection.

| Command | Description |
| --- | --- |
| `make` / `make package` | Build `build.nosync/theme.gams.zip` and `build.nosync/SHA256SUMS`; rebuild only when inputs change. |
| `make open` | Open orange (default) in the released GAMS Host; download the Host when absent. |
| `make open THEME=the98` / `make open THEME=codecraft` | Preview the selected theme. |
| `make tools/gams.app` | Download the Host and its notices without opening it; keep an existing download. |
| `make clean` | Remove entire `build.nosync/`, `tools/` and `gams_modules/`, including unmarked tools/caches; refuse tracked files and symlinks in all targets before deleting anything. |
| `make serve-docs DOCS_PORT=8080` | Serve the documentation locally. |
| `make docs` / `make build-docs` | Build the portable documentation site in `build.nosync/site/`. |
| `make validate-docs` | Check the documentation. |

Packaging needs Make, Python 3, `zip` and `shasum`. Opening the Project requires GAMS
2.2.0+ on macOS Apple Silicon; the Host downloader uses Python 3, curl and unzip.
Existing Host downloads are preserved; use `make clean` before `make open` to
replace an older Host (also removes the generated output and caches listed above). Documentation
uses Node.js 24 and pinned `justgook/wiki` v1.4.0. Initial downloads need network
access; no sibling checkout is required.

Generated files live in `build.nosync/`; finished Host tools and installed Units
live in `tools/` and `gams_modules/`.
