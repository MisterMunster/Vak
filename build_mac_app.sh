#!/bin/bash
# Builds Vak.app for macOS. Run this ON A MAC (Terminal > cd into this folder > ./build_mac_app.sh)
# Mirrors the exact build used in .github/workflows/build.yml
set -e

echo "==> Checking Python 3..."
if ! command -v python3 &>/dev/null; then
  echo "Python 3 not found. Install it from https://www.python.org/downloads/ first."
  exit 1
fi

echo "==> Creating virtual environment (.venv)..."
python3 -m venv .venv
source .venv/bin/activate

echo "==> Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt pyinstaller

echo "==> Building Vak.app with PyInstaller..."
pyinstaller --noconfirm --windowed --onefile --name Vak \
  --collect-all tkinterdnd2 \
  --collect-all eng_to_ipa \
  --collect-all speech_recognition \
  --collect-all googleapiclient \
  --collect-all imageio_ffmpeg \
  --collect-all rapidfuzz \
  --collect-all jellyfish \
  main.py

echo "==> Smoke test..."
./dist/Vak.app/Contents/MacOS/Vak --selftest selftest_out.txt || true
if grep -q 'SELFTEST OK' selftest_out.txt 2>/dev/null; then
  echo "Selftest passed."
else
  echo "Selftest output:"
  cat selftest_out.txt 2>/dev/null || echo "(no selftest output produced)"
fi

echo ""
echo "==> Done. App is at: dist/Vak.app"
echo "    Double-click it in Finder, or run: open dist/Vak.app"
echo "    (First launch: right-click > Open, since it's unsigned.)"
