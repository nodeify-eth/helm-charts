#!/usr/bin/env bash
# Copy the landing page from this checkout onto gh-pages.
# chart-releaser commits index.yaml in its own worktree and does not
# stage this page. This script only adds the files listed below.

set -euo pipefail

branch="${PAGES_BRANCH:-gh-pages}"
remote="${PAGES_REMOTE:-origin}"

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

files=(
  index.html
  assets/nodeify-logo.svg
  assets/favicon.svg
  assets/favicon-32.png
  assets/apple-touch-icon.png
  assets/fonts/inter-latin.woff2
  assets/fonts/OFL.txt
)

for file in "${files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing landing page file: $file" >&2
    exit 1
  fi
done

work=$(mktemp -d)
cleanup() {
  git worktree remove --force "$work" >/dev/null 2>&1 || true
  rm -rf "$work"
}
trap cleanup EXIT

publish_once() {
  git fetch --force "$remote" "+refs/heads/${branch}:refs/remotes/${remote}/${branch}"
  git worktree remove --force "$work" >/dev/null 2>&1 || true
  rm -rf "$work"
  git worktree add --detach "$work" "${remote}/${branch}"

  mkdir -p "$work/assets/fonts"
  cp index.html "$work/index.html"
  cp assets/nodeify-logo.svg "$work/assets/nodeify-logo.svg"
  cp assets/favicon.svg "$work/assets/favicon.svg"
  cp assets/favicon-32.png "$work/assets/favicon-32.png"
  cp assets/apple-touch-icon.png "$work/assets/apple-touch-icon.png"
  cp assets/fonts/inter-latin.woff2 "$work/assets/fonts/inter-latin.woff2"
  cp assets/fonts/OFL.txt "$work/assets/fonts/OFL.txt"

  git -C "$work" add -- "${files[@]}"

  if git -C "$work" diff --cached --quiet; then
    echo "Landing page already matches this commit."
    return 0
  fi

  if [[ "${DRY_RUN:-}" == "1" ]]; then
    git -C "$work" diff --cached --stat
    return 0
  fi

  git -C "$work" \
    -c user.name="github-actions[bot]" \
    -c user.email="41898282+github-actions[bot]@users.noreply.github.com" \
    commit -m "Publish landing page"

  git -C "$work" push "$remote" "HEAD:refs/heads/${branch}"
  echo "Published landing page to ${branch}."
}

attempt=1
while [[ "$attempt" -le 3 ]]; do
  if publish_once; then
    exit 0
  fi
  echo "Push to ${branch} was rejected; retrying (${attempt})." >&2
  attempt=$((attempt + 1))
done

echo "Failed to publish the landing page to ${branch}." >&2
exit 1
