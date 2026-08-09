#!/bin/bash
#
# Initialize and build the vendor/wspy submodule at its pinned commit
# (CLAUDE.md's "wspy dependency" section). Idempotent -- safe to re-run after a
# submodule bump (`git submodule update` fetches the newly-pinned commit) or after
# a plain `git clone` of this repo (submodules aren't checked out by a plain clone).
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "==> git submodule update --init --recursive"
git submodule update --init --recursive

if ! command -v gcc >/dev/null 2>&1; then
    echo "bootstrap_wspy.sh: gcc not found -- install a C toolchain first" >&2
    exit 1
fi

if [ ! -f /usr/include/sqlite3.h ] && ! find /usr/include -name 'sqlite3.h' 2>/dev/null | grep -q .; then
    echo "bootstrap_wspy.sh: sqlite3.h not found -- wspy-store/wspy-summary/wspy-archetype" >&2
    echo "  need libsqlite3-dev (or your distro's equivalent) to build. Install it, e.g.:" >&2
    echo "    sudo apt install libsqlite3-dev" >&2
    exit 1
fi

echo "==> make -C vendor/wspy"
make -C vendor/wspy

echo "==> vendor/wspy --version"
vendor/wspy/wspy --version

missing=0
for bin in wspy wspy-run wspy-store wspy-validate wspy-archetype; do
    if [ ! -e "vendor/wspy/$bin" ]; then
        echo "bootstrap_wspy.sh: $bin missing after build" >&2
        missing=1
    fi
done
[ "$missing" -eq 0 ] && echo "bootstrap_wspy.sh: all five wspy binaries present, ready to go."
exit "$missing"
