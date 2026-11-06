# theme.gams

The kkgams-maintained theme collection for GAMS. Each theme is a separate CSS
stylesheet; all themes share one version and release ZIP.

| Theme | Source | Release path |
| --- | --- | --- |
| The98 | `src/themes/the98.css` | `themes/the98.css` |

The98 is based on [98.css](https://github.com/jdan/98.css) by **Jordan Scales**,
copyright 2020. Its adapted styles and embedded SVG icons retain the
[MIT license](licenses/98.css.MIT.txt). GAMS-authored additions are
[Apache-2.0](LICENSE).

## Use a theme

Select a stylesheet in your Project's `gams.json`:

```json
{
  "ui": {
    "theme": {
      "url": "https://github.com/kkgams/theme.gams/releases/download/v1.0.1/theme.gams.zip#themes/the98.css"
    }
  }
}
```

The example URL works after that tag is published. ZIP names stay fixed, so
future upgrades change only the tag version. Existing
`theme.the98` release URLs remain valid.

Any local or external CSS is still supported, for example
`"theme": { "url": "themes/my-theme.css" }`. Omit `ui.theme` for Host base styling.

## Develop

Edit CSS under `src/themes/`. Add assets alongside it and keep any third-party
attribution and license files. List files to include in Makefile's `ZIP_FILES`.
No compilation is needed.

```sh
make open                    # open the local Project with The98 selected
make package                 # build theme.gams.zip and SHA256SUMS in build.nosync/
make clean                   # remove generated output and downloaded caches
make serve-docs DOCS_PORT=8080
make docs
```

Packaging requires Make, `zip` and `shasum`. Python 3 is used only by the
Host downloader. `make open` uses the released macOS Apple
Silicon Host in ignored `tools/gams.app`, downloading it only when absent,
retaining notices and setting `GAMS_APP_CWD`. Released Project dependencies are
pinned; no sibling checkout is needed. Documentation uses pinned
`justgook/wiki` v1.4.0 and requires Node.js 24. Initial downloads need network access.

`make package` depends on `build.nosync/SHA256SUMS` and
`build.nosync/theme.gams.zip`. Make rebuilds the ZIP when inputs change and
updates its checksum; otherwise it does nothing.

Build output, documentation, caches and temporary files live in `build.nosync/`.
Finished Host tools and installed Units stay in `tools/` and `gams_modules/`.

`make clean` removes `build.nosync/`, `tools/`, `gams_modules/` and Python
bytecode caches. It refuses tracked files in those output locations and leaves
other untracked files alone. The next open/docs commands download their tools
again when needed.
