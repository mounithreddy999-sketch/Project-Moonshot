#!/bin/bash
# WSL Native Build Execution Script

echo "=========================================================="
echo " Starting Pure WSL Execution Environment"
echo "=========================================================="

export PDK_ROOT=$HOME/pdk
mkdir -p $PDK_ROOT

echo "[*] Assuming Python and Pip are installed in WSL..."

echo "[*] Installing Volare locally in WSL..."
pip install volare --break-system-packages || python3 -m pip install volare --break-system-packages

echo "[*] Downloading Skywater 130 PDK into WSL (~5GB)..."
~/.local/bin/volare enable --pdk sky130 c6d73a35f524070e85faff4a6a9eef49553ebc2b

echo "[*] Navigating to Windows Mount and Triggering Synthesis..."
cd /mnt/c/Users/mouni/Documents/GitHub/Project-Moonshot/open_silicon
make harden
