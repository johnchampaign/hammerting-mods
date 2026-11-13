#!/bin/sh
# Removes the mods and restores the original game DLLs. Close the game first.
cd "$(dirname "$0")" || exit 1
python3 tools/hmod.py uninstall || exit 1
echo
echo "Now clear Hammerting's Steam Launch Options."
