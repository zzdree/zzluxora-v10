#!/usr/bin/env bash
# ==============================================================================
# ZZLUXORA v10.0.0 — One-Click Stage Lighting Console Launcher (Linux Mint / Debian)
# ==============================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Ensure Python 3 runs with UTF-8 encoding
export PYTHONUTF8=1
export PYTHONUNBUFFERED=1

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 tidak ditemukan di sistem!"
    exit 1
fi

echo "=================================================="
echo "🎛️  ZZLUXORA v10.0.0 — Next-Gen Lighting Console"
echo "=================================================="
echo "Memulai antarmuka konsol..."

exec python3 main.py "$@"
