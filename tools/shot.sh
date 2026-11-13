#!/bin/bash
# Screenshot the Hammerting window (an Xwayland window under Proton) to $1 (png).
# Optional $2: crop geometry for ImageMagick, e.g. 340x100+30+420.
set -e
id=$(DISPLAY=:0 xwininfo -root -tree | awk '/"Hammerting":/ {print $1; exit}')
[ -n "$id" ] || { echo "no Hammerting window" >&2; exit 1; }
DISPLAY=:0 import -window "$id" "$1"
[ -z "$2" ] || convert "$1" -crop "$2" +repage "$1"
