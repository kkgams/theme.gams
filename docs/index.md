---
title: GAMS themes
status: reference
---

# GAMS themes

The kkgams theme collection currently contains The98, a Windows 98-style theme
based on [98.css](https://github.com/jdan/98.css) by Jordan Scales. Its styles
and embedded SVG icons retain MIT terms in `licenses/98.css.MIT.txt`.
GAMS-authored additions are Apache-2.0.

## Select a theme

Set `ui.theme.url` in your Project's `gams.json` to a CSS source. For example,
`{"ui":{"theme":{"url":"themes/my-theme.css"}}}` selects a local stylesheet.
A published collection ZIP uses `#themes/the98.css` to select The98. Its asset
name is always `theme.gams.zip`; only the release tag changes between versions.
Version 1.0.1 is the next candidate, not a published-asset claim.

The Host also accepts CSS outside this collection. Omit `ui.theme` for Host
base styling. Existing theme.the98 release pins remain valid.

## Edit and open

Edit `src/themes/the98.css` or add another theme under `src/themes/`, with any
required assets and third-party license files. Follow the Host's documented
semantic UI elements rather than introducing a custom loader or View markup.
Each stylesheet deploys to its corresponding `themes/` path.

Run `make open` on macOS Apple Silicon to open the local Project with The98.
The Host downloads to ignored `tools/gams.app` only when absent; notices are
retained and an existing Host is never updated implicitly. The command sets
`GAMS_APP_CWD` and does not bypass Gatekeeper. Pinned released plugins, UI
Services and file Views supply the workspace; no sibling checkout is needed.

## Package and publish

```sh
make package OUT=dist/new-candidate
make check-package OUT=dist/new-candidate
```

Packaging requires Make and Python 3. Output must not already exist. CSS is
copied unchanged; there is no compilation or CSS test pipeline. The ZIP includes
README, LICENSE, NOTICE and `licenses/`. Generated checksums and package checking
concern release bytes, not CSS behavior or license auditing.

Makefile owns `VERSION`. A matching tag push publishes `theme.gams.zip` and
SHA256SUMS without overwriting existing releases.

## Clean generated files

`make clean` removes `build/`, `dist/`, downloaded Host/tools, installed Unit
caches in `gams_modules/` and Python bytecode caches. Downloads are recreated on
the next command that needs them. Source, configuration and unrelated untracked
files remain; tracked output files cause clean to stop rather than delete them.

## Documentation

- `make serve-docs DOCS_PORT=8080` previews these docs.
- `make validate-docs` validates documentation.
- `make docs` builds the portable site in `build/site/`.

Documentation uses pinned `justgook/wiki` v1.4.0 and Node.js 24, without npm
packages. First-time downloads need network access. Every push to `release`
publishes through GitHub Pages independently of version tags.
