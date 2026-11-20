---
title: GAMS themes
status: reference
---

# GAMS themes

Themes for [GAMS](https://github.com/kkgams/gams).

## Themes

| Name | File | Screenshot | Original work |
| --- | --- | --- | --- |
| The98 | [the98.css](https://github.com/kkgams/theme.gams/blob/release/src/themes/the98.css) | Pending | [98.css by Jordan Scales](https://github.com/jdan/98.css) |
| orange | [orange.css](https://github.com/kkgams/theme.gams/blob/release/src/themes/orange.css) | Pending | [kkgams / GAMS](https://github.com/kkgams/gams) |
| Codecraft | `themes/codecraft.css` | Pending | [World of Codecraft by Kevin Pardo](https://github.com/kevinpardo/world-of-codecraft) |

Codecraft styles panel borders only. The original slices and the combined 2× atlas
ship under `art/codecraft/` in the ZIP.

## Development

Edit styles in `src/themes/` and list packaged files in Makefile's `ZIP_FILES`.
`orange` keeps the Host base styling with the GAMS promo accent (`#ec4e00`) and
square corners. `make open` passes the selected `gams_<theme>.json` filename through
`GAMS_CONFIG` and uses this repository as the Project root.

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
