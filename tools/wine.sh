#!/bin/bash
# Run a Windows program with Proton Experimental's Wine in the tools prefix
# (kept separate from the game's own prefix, so it is safe while the game runs).
P="$HOME/.local/share/Steam/steamapps/common/Proton - Experimental/files"
export WINEPREFIX="$HOME/.local/share/hammerting-tools-prefix" WINEDEBUG=${WINEDEBUG:--all}
export WINEDLLOVERRIDES="mscoree,mshtml="
export PATH="$P/bin:$PATH" LD_LIBRARY_PATH="$P/lib/x86_64-linux-gnu:$P/lib/i386-linux-gnu"
exec systemd-run --user --scope -q -p MemoryMax=3G wine "$@"
