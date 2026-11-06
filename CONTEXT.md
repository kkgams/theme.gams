# GAMS theme collection

`theme.gams` owns the kkgams-maintained theme stylesheets and their local assets.
It does not own the Host, Views, UI Services or Host base styles.

Each theme deploys to its own `themes/<name>.css` entry. All themes share one
collection version and release ZIP. Projects select one CSS source using the
existing `ui.theme.url` configuration; arbitrary external or local CSS remains
supported. There is no collection-specific runtime loader or theme registry.

The current collection contains The98. Styling follows the Host-owned semantic
UI contract documented in GAMS's `docs/gams-view-development-guide.md`.
Third-party adaptations retain their original attribution and license terms.
