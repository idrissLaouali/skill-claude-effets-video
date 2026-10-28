#!/usr/bin/env bash
# Prépare les effets vidéo (une seule fois). Affiche PRET quand tout est bon.
set -e
cd "$(dirname "$0")/.."
command -v ffmpeg >/dev/null 2>&1 || { echo "BESOIN_FFMPEG"; exit 1; }
PY=""
for c in python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if (3,9)<=sys.version_info[:2]<=(3,12) else 1)' 2>/dev/null; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "BESOIN_PYTHON"; exit 1; }
[ -d .venv ] || "$PY" -m venv .venv
if [ -x .venv/bin/python ]; then V=.venv/bin/python; else V=.venv/Scripts/python.exe; fi
"$V" -m pip install -q --upgrade pip
"$V" -m pip install -q -r requirements.txt
"$V" scripts/effets.py --liste >/dev/null && echo "PRET"
