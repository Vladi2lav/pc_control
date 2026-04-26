#!/usr/bin/env sh
set -eu

if [ -x "./venv/bin/python" ]; then
    ./venv/bin/python init.py
else
    python3 init.py
fi
