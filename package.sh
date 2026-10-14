#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
mkdir -p "$project_dir/dist"
package_dir=$(mktemp -d "${TMPDIR:-/tmp}/macos-tmux-ime.XXXXXX")
trap 'rm -rf "$package_dir"' EXIT HUP INT TERM
mkdir "$package_dir/macos-tmux-ime"
for package_file in tmux-ime.c build.sh install.sh package.sh README.md COPYING examples tests; do
    cp -R "$project_dir/$package_file" "$package_dir/macos-tmux-ime/"
done
# macOS resource forks and personal extended attributes are not source files.
COPYFILE_DISABLE=1 tar -czf "$project_dir/dist/macos-tmux-ime-src.tar.gz" \
    -C "$package_dir" macos-tmux-ime
printf '%s\n' "$project_dir/dist/macos-tmux-ime-src.tar.gz"
