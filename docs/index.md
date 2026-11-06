---
title: GAMS themes
status: reference
---

# GAMS themes

`theme.gams` contains the kkgams-maintained themes. The initial collection is
The98, a compact Windows 98-style theme. All themes share one release version;
each has a separate CSS entry and remains independently selectable.

## Select a theme

In a Project's `gams.json`, `ui.theme.url` points to a CSS source. For example,
`{"ui":{"theme":{"url":"themes/my-theme.css"}}}` selects a local stylesheet.
A published ZIP source can select an entry with `#themes/the98.css`.
The collection artifact is `theme.gams.zip`; release URLs become
available only after publication. Custom CSS from outside this collection still
works through the same Host configuration. Omit `ui.theme` for Host base styling.

## Open the local Project

Run `make open` on macOS Apple Silicon. The local `gams.json` selects
`src/themes/the98.css`, with no compilation or sibling checkout required. The
minimal workspace uses pinned released filesystem/layout plugins, UI Services
and file Views. First launch requires network access. Downloaded Units live in
ignored `gams_modules/`.

The released Host is downloaded to `tools/gams.app` only when absent; notices
remain in `tools/gams-release-notices/`. An existing Host is never updated
implicitly. The command sets `GAMS_APP_CWD`; it does not bypass Gatekeeper.

## Add or edit a theme

Put the theme's CSS and required assets under `src/themes/`. Follow the Host-owned
semantic UI contract in GAMS's `docs/gams-view-development-guide.md`; themes style
that contract rather than requiring View-specific markup or runtime changes.

List each deployable source in `package.json` under `files` and each selectable
stylesheet's deployed path in `release.json` under `entries`. Preserve license
attribution and maintain the source/license evidence for new or changed bytes.
Update the theme table in README and select the theme's local CSS in `gams.json`
while developing it. Do not add a custom theme loader or restrict outside CSS.

## Validate

Run `make check` with Node.js 24 and Python 3. It validates source references,
collection entries, source/licensing evidence, deterministic packaging, exact
artifact contents, tag identity and release safety. It does not render CSS.

Use the real Host to inspect labels, forms, buttons and mixed button/select
groups, tables, selectable cells, popup/tooltip styling and focused, selected and
disabled states. Check narrow windows and long labels. The manual browser module
`test/select-arrows.browser.js` exports `checkSelectArrows()` and
`checkSelectPicker()` for a browser running the real Host base CSS and The98.
The picker check reports a skip where customizable native pickers are unsupported
or forced colors are active. These browser checks are not part of `make check`.

The98 retains the inherited selectable-cell styling, mixed button/select groups,
select arrows and progressively enhanced native picker. The collection migration
changes packaging and ownership, not those CSS bytes.

## Build and publish

Stage and independently check the next candidate with:

```sh
python3 scripts/release.py stage --tag v1.0.1 --out dist/candidate
python3 scripts/release.py check --tag v1.0.1 --out dist/candidate
```

The output directory must not exist before staging. Matching version-tag pushes
publish the ZIP and SHA256SUMS; existing releases cannot be overwritten. See
PUBLISHING.md in the repository for the release helper and required checks.

## Documentation

- `make serve-docs DOCS_PORT=8080` previews these docs.
- `make validate-docs` validates the wiki.
- `make docs` builds the portable site in `build/site/`.

The engine is pinned to `justgook/wiki` v1.4.0. Every push to `release` publishes
through GitHub Pages, independently of version tags. Pages must use Actions.
