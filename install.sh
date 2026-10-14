#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
tmux_prefix=C-a
case $# in
    0) ;;
    2)
        if [ "$1" != --prefix ]; then
            echo 'Usage: ./install.sh [--prefix C-a|C-b]' >&2
            exit 2
        fi
        tmux_prefix=$2
        ;;
    *) echo 'Usage: ./install.sh [--prefix C-a|C-b]' >&2; exit 2 ;;
esac
case "$tmux_prefix" in
    C-a|C-b) ;;
    *) echo 'Supported prefixes: C-a, C-b' >&2; exit 2 ;;
esac

"$project_dir/build.sh"
# Optional staging root for packaging/tests; never changes the caller's HOME.
install_root=${TMUX_IME_DESTDIR:-$HOME}
bin_dir=$install_root/.local/bin
config_dir=$install_root/.config/tmux-ime
mkdir -p "$bin_dir" "$config_dir"

install_file() {
    file_mode=$1
    source_file=$2
    target_file=$3
    if [ -e "$target_file" ] && ! cmp -s "$source_file" "$target_file"; then
        cp -p "$target_file" "$target_file.bak.$(date +%Y%m%d%H%M%S).$$"
    fi
    install -m "$file_mode" "$source_file" "$target_file"
}
install_file 755 "$project_dir/build/tmux-ime" "$bin_dir/tmux-ime"
install_file 644 "$project_dir/examples/tmux-$tmux_prefix.conf" "$config_dir/tmux.conf"
install_file 644 "$project_dir/examples/ghostty-$tmux_prefix.conf" "$config_dir/ghostty.conf"

cat <<'EOF'
Installed. Existing tmux/Ghostty configuration has not been edited.

Add this AFTER your existing prefix settings in ~/.tmux.conf:
    source-file ~/.config/tmux-ime/tmux.conf

Add the following binding to your Ghostty configuration:
EOF
cat "$config_dir/ghostty.conf"
printf '\nReload both configurations. See README.md for verification and removal.\n'
