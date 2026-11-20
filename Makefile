.DEFAULT_GOAL := package
.DELETE_ON_ERROR:
CODECRAFT_SLICES := $(addprefix src/art/codecraft/,$(addsuffix .png,\
	$(foreach frame,baguette cadre plaque-frame,$(addprefix $(frame)-,tl t tr l r bl b br)) \
	bandeau-l bandeau-m bandeau-r medaillon poutre-ornament poutre-strap poutre-plain \
	$(foreach face,btn btn-or,$(foreach state,n h p,$(addprefix $(face)-$(state)-,l m r)))))
CODECRAFT_ART := $(CODECRAFT_SLICES) src/art/codecraft/baguette-9slice.png
CODECRAFT_CSS := build.nosync/themes/codecraft.css
ZIP_FILES := README.md LICENSE NOTICE licenses/98.css.MIT.txt licenses/world-of-codecraft.MIT.txt src/themes/the98.css src/themes/orange.css $(CODECRAFT_ART)
export TMPDIR := $(abspath build.nosync/tmp)
export PYTHONPYCACHEPREFIX := $(abspath build.nosync/pycache)
PYTHON ?= python3
CURL ?= curl
GAMS_RELEASE_API ?= https://api.github.com/repos/kkgams/gams/releases/latest
UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)
THEME ?= orange
GAMS_CONFIG ?= gams_$(THEME).json
DOCS_PORT ?= 8080
WIKI_VERSION := v1.4.0
WIKI_REPOSITORY := https://github.com/justgook/wiki
WIKI_MAKEFILE := build.nosync/wiki-$(WIKI_VERSION).mk
WIKI_ENGINE := $(abspath build.nosync/wiki-$(WIKI_VERSION))

.PHONY: package clean open serve-docs validate-docs build-docs docs
package: build.nosync/SHA256SUMS build.nosync/theme.gams.zip

$(CODECRAFT_CSS): src/themes/codecraft.css.in $(CODECRAFT_SLICES) Makefile
	@mkdir -p "$(@D)"
	$(PYTHON) -c 'from base64 import b64encode; from pathlib import Path; import re, sys; images = {p.stem: b64encode(p.read_bytes()).decode() for p in map(Path, sys.argv[2:])}; print(re.sub(r"\{\{([a-z-]+)\}\}", lambda m: images[m[1]], Path(sys.argv[1]).read_text()), end="")' "$<" $(CODECRAFT_SLICES) > "$@"

build.nosync/theme.gams.zip: $(ZIP_FILES) $(CODECRAFT_CSS) Makefile | build.nosync/tmp
	rm -f "$@"
	cd src && zip -q -X "../$@" $(patsubst src/%,%,$(filter src/%,$(ZIP_FILES)))
	zip -q -X "$@" $(filter-out src/%,$(ZIP_FILES))
	cd build.nosync && zip -q -X "../$@" "$(patsubst build.nosync/%,%,$(CODECRAFT_CSS))"

build.nosync/SHA256SUMS: build.nosync/theme.gams.zip
	cd build.nosync && shasum -a 256 theme.gams.zip > SHA256SUMS

clean:
	$(PYTHON) -B scripts/clean.py

# Retain an existing app; never update it implicitly.
tools/gams.app: | build.nosync/tmp
	@test "$(UNAME_S)" = Darwin && test "$(UNAME_M)" = arm64 || \
		{ echo 'GAMS release download requires macOS Apple Silicon' >&2; exit 1; }
	@test ! -e tools/gams-release-notices || \
		{ echo 'tools/gams-release-notices already exists; move it aside before reinstalling GAMS' >&2; exit 1; }
	@mkdir -p tools
	@set -eu; stage=$$(mktemp -d "$(TMPDIR)/gams-download.XXXXXX"); \
		trap 'rm -rf "$$stage"' EXIT; \
		$(CURL) --fail --location --silent --show-error "$(GAMS_RELEASE_API)" --output "$$stage/release.json"; \
		url=$$($(PYTHON) -c 'import json, sys; release = json.load(open(sys.argv[1])); assets = [a for a in release["assets"] if a["name"].startswith("GAMS-") and a["name"].endswith("-macos-aarch64.zip")]; assert len(assets) == 1, "Expected exactly one GAMS macOS Apple Silicon ZIP asset"; print(assets[0]["browser_download_url"])' "$$stage/release.json"); \
		$(CURL) --fail --location --silent --show-error "$$url" --output "$$stage/gams.zip"; \
		unzip -q "$$stage/gams.zip" -d "$$stage/unpacked"; \
		test -f "$$stage/unpacked/GAMS.app/Contents/Info.plist"; \
		test -x "$$stage/unpacked/GAMS.app/Contents/MacOS/gams"; \
		mv "$$stage/unpacked/GAMS.app" "$$stage/GAMS.app"; \
		mv "$$stage/unpacked" tools/gams-release-notices; \
		mv "$$stage/GAMS.app" "$@"

open: $(GAMS_CONFIG) $(if $(filter gams_codecraft.json,$(notdir $(GAMS_CONFIG))),$(CODECRAFT_CSS)) tools/gams.app
	GAMS_APP_CWD="$(CURDIR)" GAMS_CONFIG="$(GAMS_CONFIG)" ./tools/gams.app/Contents/MacOS/gams

build.nosync/tmp:
	@mkdir -p "$@"

$(WIKI_MAKEFILE): | build.nosync/tmp
	@mkdir -p "$(@D)"
	@set -eu; trap 'rm -f "$@.tmp"' EXIT; \
		$(CURL) --fail --location --retry 3 "$(WIKI_REPOSITORY)/raw/$(WIKI_VERSION)/Makefile" -o "$@.tmp"; \
		mv "$@.tmp" "$@"

docs: build-docs

serve-docs validate-docs build-docs: $(WIKI_MAKEFILE) | build.nosync/tmp
	$(MAKE) -f "$(WIKI_MAKEFILE)" "$(patsubst %-docs,%,$@)" WIKI_REPOSITORY="$(WIKI_REPOSITORY)" WIKI_VERSION="$(WIKI_VERSION)" WIKI_ENGINE="$(WIKI_ENGINE)" WIKI_SOURCE="$(abspath docs)" WIKI_OUTPUT="$(abspath build.nosync/site)" PORT="$(DOCS_PORT)"
