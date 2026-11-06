# Publishing

`VERSION` in Makefile is the collection version, currently **1.0.1**. A matching
`v<version>` tag push publishes `theme.gams.zip` and `SHA256SUMS` through GitHub
Releases. Only the tag version changes in download URLs.

## Package

Requires Make and Python 3. Use a fresh output directory:

```sh
make package OUT=dist/new-candidate
make check-package OUT=dist/new-candidate
```

The ZIP contains `src/` files with that prefix removed, README, LICENSE, NOTICE
and `licenses/`. CSS is copied as-is, without parsing, linting or browser tests.
The98 credits Jordan Scales and keeps the full 98.css MIT license under
`licenses/98.css.MIT.txt`.

`check-package` checks the release ZIP and its generated checksum against the
current files. It does not validate CSS or license contents. Packaging refuses
to overwrite an existing output directory.

## Push a release

From a clean committed checkout with canonical
`git@github.com:kkgams/theme.gams.git` origin and authenticated GitHub CLI:

```sh
scripts/push-release.sh             # preflight only; no refs changed
scripts/push-release.sh --publish   # push current branch and matching tag
```

The helper checks repository/version/tag identity, remote tag/release absence
and a fresh package. `--publish` creates the local tag if absent, then pushes
branch and tag atomically. It never forces updates or creates the GitHub Release
itself; matching-tag CI publishes using the automatic GitHub token. Authentication
and API errors stop publication. Existing tags and releases cannot be replaced.
A failed push may leave a local tag; inspect it before retrying.

No special publication branch or manual approval/checksum variables are required.
Enable immutable releases in repository settings. Branch and PR CI package
without publishing. Creating tags, pushing or publishing still requires explicit
authorization.

## Documentation

`make serve-docs` previews docs, `make validate-docs` checks documentation and
`make docs` builds the portable site. Every push to `release` deploys it through
GitHub Pages independently of version tags. Pages must use GitHub Actions.
