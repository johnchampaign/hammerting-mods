#!/bin/bash
# Build mods/<name>/data/** into mods/<name>/build/<name>.wkz with the game's own archiver.
# Inside the tools prefix the mods folder is C:/mods and the game is C:/hammerting
# (symlinks in drive_c), which keeps spaces out of the paths ninja sees.
set -e
name="$1"
here="$(cd "$(dirname "$0")" && pwd)"
cd "$here/../mods/$name"
cp "$HOME/.local/share/Steam/steamapps/common/Hammerting/SDK/build_rules.ninja" .
args=()
while IFS= read -r f; do g="$f"; [[ "$(basename "$f")" == *__*.bin ]] && { g="${f%.bin}"; g="${g/__/.}"; }; args+=(--wkz-file "data/$f|$g"); done < <(cd data && find . -type f | sed 's|^\./||' | sort)
B="build/$name"
"$here/wine.sh" 'C:/hammerting/boot.exe' -c -l wkz --wkz-intermediate-dir "$B/intermediate" \
  --wkz-working-dir "C:/mods/$name/" --wkz-rule-file build_rules.ninja --wkz-out "../../mods/$name/build/$name.wkz" \
  --wkz-sdk-dir 'C:/hammerting/SDK' --wkz-depfile 'C:/hammerting/game.wkz' "${args[@]}" 2>&1 | grep -v '^wineserver' || true
"$here/wine.sh" 'C:/hammerting/SDK/ninja.exe' -f "$B/build.ninja" 2>&1 | grep -v '^wineserver'
ls -la "build/$name.wkz"
