#!/usr/bin/env bash
set -e

if [ ! -f ".venv/bin/activate" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt
python -m reflex run
