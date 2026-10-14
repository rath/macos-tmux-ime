#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
if [ "$(uname -s)" != Darwin ]; then
    echo 'tmux-ime requires macOS.' >&2
    exit 1
fi
if ! xcrun --find clang >/dev/null 2>&1; then
    echo 'Install Apple Command Line Tools first: xcode-select --install' >&2
    exit 1
fi
mkdir -p "$project_dir/build"
build_file=$(mktemp "$project_dir/build/tmux-ime.XXXXXX")
trap 'rm -f "$build_file"' EXIT HUP INT TERM
xcrun --sdk macosx clang -std=c11 -O2 -Wall -Wextra -Werror \
    "$project_dir/tmux-ime.c" -framework Carbon -o "$build_file"
chmod 755 "$build_file"
mv "$build_file" "$project_dir/build/tmux-ime"
printf 'Built %s (%s)\n' "$project_dir/build/tmux-ime" "$(uname -m)"
