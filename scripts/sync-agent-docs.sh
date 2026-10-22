#!/usr/bin/env bash
# sync-agent-docs.sh [--check] [DIR]
# CLAUDE.md is generated from AGENTS.md (the source) in DIR (default templates/ of the kit;
# a repository that vendors the pair passes its root). --check writes nothing and fails when
# CLAUDE.md is not exactly what the generator would write.
set -eu
check=0
if [ "${1:-}" = --check ]; then check=1; shift; fi
dir=${1:-$(cd "$(dirname "$0")/.." && pwd)/templates}
src=$dir/AGENTS.md
dst=$dir/CLAUDE.md
[ -f "$src" ] || { echo "sync-agent-docs: $src is missing" >&2; exit 2; }
if [ "$check" -eq 1 ]; then
  if [ -f "$dst" ] && cmp -s "$src" "$dst"; then
    echo "sync-agent-docs: CLAUDE.md matches AGENTS.md"
  else
    echo "sync-agent-docs: CLAUDE.md differs from AGENTS.md; run scripts/sync-agent-docs.sh" >&2
    exit 1
  fi
else
  cp "$src" "$dst"
  echo "sync-agent-docs: wrote $dst"
fi
