#!/bin/bash
# SPDX-FileCopyrightText: 2026 Project Moonshot
# Licensed under the Apache License, Version 2.0
#
# SETUP SCRIPT FOR PROJECT MOONSHOT PHYSICAL TAPE-OUT
# WARNING: This script will download approximately 20GB of data.

# This flow requires a Linux environment (WSL/Ubuntu). Under Git Bash / MSYS on
# Windows, $HOME ("C:\Users\you") gets mangled into a literal "C:Usersyou"
# directory when tools (volare/mkdir) create paths. Refuse early so we never
# create that stray PDK folder again.
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    echo "ERROR: Do not run this under Git Bash / MSYS on Windows."
    echo "       Open WSL (run 'wsl') and re-run, or use ./run_wsl_build.sh."
    exit 1
    ;;
esac

echo "================================================================"
echo "    PROJECT MOONSHOT: SKYWATER 130NM PDK & OPENLANE SETUP       "
echo "================================================================"
echo "[*] Ensuring Docker is running..."
if ! docker info > /dev/null 2>&1; then
  echo "ERROR: Docker is not running. Please start Docker Desktop first."
  exit 1
fi

echo "[*] Pulling OpenLane Docker Image..."
# We use a stable, universally available OpenLane tag. 
docker pull efabless/openlane:2022.02.23_1

echo "[*] Setting up Volare (PDK Version Manager)..."
# Using --break-system-packages to bypass PEP 668 on managed Linux environments (WSL/Ubuntu)
pip install volare --break-system-packages || python3 -m pip install volare --break-system-packages

echo "[*] Downloading SkyWater 130nm PDK (~5GB)..."
export PDK_ROOT=$HOME/pdk
mkdir -p $PDK_ROOT
# Volare automatically fetches the exact git commit used by Caravel MPW-9
~/.local/bin/volare enable --pdk sky130 e029fbf99c670b89ebcbf12edb95f2d5731b81e4

echo "================================================================"
echo " SETUP COMPLETE!                                                "
echo "================================================================"
echo " You are now ready for the physical tape-out."
echo " To run the 8-hour synthesis, placement, and routing flow:"
echo "   $ cd open_silicon/"
echo "   $ make harden"
echo "================================================================"
