#!/bin/sh
# Installs the mods in mods/recommended.txt into Hammerting. Close the game first.
# Any arguments replace the recommended list: ./install.sh natural_healing ground_pickup
cd "$(dirname "$0")" || exit 1
if [ $# -eq 0 ]; then set -- recommended; fi
python3 tools/hmod.py install "$@" || exit 1
echo
echo "Set Hammerting's Steam Launch Options to:"
echo "%command% --game-extra-archives danger_zone/hammerting_mods.wkz"
