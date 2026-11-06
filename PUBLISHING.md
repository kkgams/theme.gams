# Publishing

The collection publishes `theme.gams.zip` and `SHA256SUMS` through
GitHub Releases, not npm or OCI. Every theme is included in that ZIP with its
own `themes/<name>.css` path. The ZIP filename is stable across versions; only
the release tag changes in download URLs. The next collection version is **1.0.1**.

## Validate a candidate

Requires Node.js 24 and Python 3. Candidate output must not already exist.

```sh
make check
python3 scripts/release.py stage --tag v1.0.1 --out dist/candidate
python3 scripts/release.py check --tag v1.0.1 --out dist/candidate
make validate-docs
make docs
```

Staging validates the complete source/evidence closure and produces deterministic
ZIP bytes and checksums. Independent checking requires the exact candidate files,
contents and metadata; it never substitutes source for missing artifacts. LICENSE,
NOTICE, README, evidence, comparison and third-party license files accompany the
stylesheets. The Host loads CSS directly; no `unit.json` or custom loader is needed.

`make check` does not run browser rendering. Before publishing changed CSS,
verify it in the real Host using `make open`, including disabled/focused/selected
states and the Host's documented UI elements. The existing browser regression
module checks The98 select arrows and enhanced native picker styling; run it in
the real Host cascade as described in `docs/index.md`.

## Publish a version

A matching `vMAJOR.MINOR.PATCH` tag push is the release authorization. No manual
checksum variables, extra approval flags or required publication branch apply.
Tests, exact tag/version/repository/checkout identity, source/licensing evidence,
artifact integrity and no-overwrite checks remain mandatory.

After an explicitly authorized version commit, use a clean checkout and the
canonical `git@github.com:kkgams/theme.gams.git` origin:

```sh
scripts/push-release.sh             # read-only remote preflight; no refs changed
scripts/push-release.sh --publish   # create local tag if needed; push branch/tag
```

The helper requires authenticated GitHub CLI with repository push access to see
drafts. It rejects existing remote tags/releases, checks local tag identity,
runs tests and fresh stage/check, then pushes the current branch and matching tag
atomically without force. API/authentication/network errors fail closed. A failed
push can leave a local tag; inspect it before retrying. The helper does not create
a GitHub Release; matching-tag CI verifies the candidate and creates it using the
automatic GitHub token. Existing releases and tags must never be replaced.

Branch and PR CI validate candidates without publishing. Enable immutable
releases in the repository settings before publication. Hosted CI, public artifact
consumption and native GUI checks must be reported separately from local tests.

## Documentation

Every push to `release` publishes `docs/` through GitHub Pages using `make docs`
and pinned `justgook/wiki` v1.4.0. Configure Pages to use GitHub Actions.
Documentation publication is independent of version tags and the default branch.
