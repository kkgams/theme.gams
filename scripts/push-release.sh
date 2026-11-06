#!/usr/bin/env bash
# User-operated release preflight; only --publish mutates local/remote refs.
set -euo pipefail
fail() { printf 'error: %s\n' "$*" >&2; exit 1; }
publish=false
case "${1-}" in
  '') ;;
  --publish) publish=true ;;
  *) fail 'usage: scripts/push-release.sh [--publish]' ;;
esac
[ "$#" -le 1 ] || fail 'usage: scripts/push-release.sh [--publish]'
cd "$(dirname "$0")/.."
repo=kkgams/theme.gams
for command in git gh python3 make; do command -v "$command" >/dev/null || fail "missing command: $command"; done
[ -z "$(git status --porcelain)" ] || fail 'checkout must be clean'
branch_ref=$(git symbolic-ref --quiet HEAD) || fail 'HEAD must be on a branch'
[[ $branch_ref == refs/heads/* ]] || fail 'HEAD must name a local branch'
branch=${branch_ref#refs/heads/}
head=$(git rev-parse HEAD)
canonical() {
  case "$1" in
    "git@github.com:$repo.git"|"https://github.com/$repo.git"|"https://github.com/$repo"|"ssh://git@github.com/$repo.git") ;;
    *) fail 'origin must be the canonical GitHub repository (one fetch/push URL)' ;;
  esac
}
canonical "$(git remote get-url --all origin)"
canonical "$(git remote get-url --push --all origin)"
if mirror=$(git config --bool --get remote.origin.mirror); then
  [ "$mirror" = false ] || fail 'mirror origin is forbidden'
else
  [ "$?" -eq 1 ] || fail 'cannot inspect origin mirror configuration'
fi
version=$(git show HEAD:Makefile | python3 -c '
import re, sys
lines = [line for line in sys.stdin.read().splitlines() if line.startswith("VERSION :=")]
if len(lines) != 1:
    sys.exit("expected exactly one canonical VERSION := line")
match = re.fullmatch(r"VERSION := ?((?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))", lines[0])
if not match:
    sys.exit("invalid version")
print(match[1])')
tag="v$version"
local_tag=false
if git show-ref --verify --quiet "refs/tags/$tag"; then
  local_tag=true
  [ "$(git rev-parse "refs/tags/$tag^{commit}")" = "$head" ] || fail 'existing local tag does not match HEAD'
else
  status=$?
  [ "$status" -eq 1 ] || fail 'cannot inspect local tag'
fi
gh auth status --hostname github.com
# Draft releases are visible only to push-capable callers; do not infer absence
# from a public/read-only listing.
[ "$(gh api --hostname github.com "repos/$repo" --jq '.permissions.push')" = true ] || fail 'GitHub token must have repository push access to inspect drafts'
remote_tags=$(git ls-remote --tags origin "refs/tags/$tag" "refs/tags/$tag^{}")
[ -z "$remote_tags" ] || fail 'remote tag already exists; use a new version'
# Listing releases succeeds only with working API access, includes drafts, and
# avoids treating an authentication/API failure as an absent tag endpoint.
releases=$(gh api --hostname github.com --paginate --slurp "repos/$repo/releases?per_page=100")
printf '%s\n' "$releases" | python3 -c '
import json, sys
pages = json.load(sys.stdin)
if not isinstance(pages, list) or not pages:
    sys.exit("invalid release API pages")
for page in pages:
    if not isinstance(page, list):
        sys.exit("invalid release API page")
    for release in page:
        if not isinstance(release, dict) or not isinstance(release.get("tag_name"), str) or not release["tag_name"]:
            sys.exit("invalid release API record")
        if release["tag_name"] == sys.argv[1]:
            sys.exit("GitHub Release already exists; use a new version")
' "$tag"
make package
[ -z "$(git status --porcelain)" ] || fail 'checkout changed during preflight'
[ "$(git rev-parse HEAD)" = "$head" ] || fail 'HEAD changed during preflight'
[ "$(git symbolic-ref --quiet HEAD)" = "$branch_ref" ] || fail 'branch changed during preflight'
if ! "$publish"; then
  printf 'Preflight passed: %s at %s on %s. No refs changed. Run with --publish to push.\n' "$tag" "$head" "$branch"
  exit 0
fi
if ! "$local_tag"; then git tag -a "$tag" "$head" -m "Release $tag"; fi
[ "$(git rev-parse "refs/tags/$tag^{commit}")" = "$head" ] || fail 'local tag changed during preflight'
git push --atomic --no-follow-tags origin "$head:refs/heads/$branch" "refs/tags/$tag:refs/tags/$tag"
printf 'Pushed %s and %s atomically; GitHub Actions creates the Release.\n' "$branch" "$tag"
