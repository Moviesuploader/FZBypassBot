#!/bin/sh
set -eu

mkdir -p "${DATA_DIR:-data}"
exec python3 -m FZBypass
