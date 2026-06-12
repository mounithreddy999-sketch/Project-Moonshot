#!/bin/bash
# SPDX-FileCopyrightText: 2026 Project Moonshot
# Licensed under the Apache License, Version 2.0
#
# SETUP SCRIPT FOR PROJECT MOONSHOT PHYSICAL TAPE-OUT
# WARNING: This script will download approximately 20GB of data.

echo "================================================================"
echo "    PROJECT MOONSHOT: SKYWATER 130NM PDK & OPENLANE SETUP       "
echo "================================================================"
echo "[*] Ensuring Docker is running..."
if ! docker info > /dev/null 2>&1; then
  echo "ERROR: Docker is not running. Please start Docker Desktop first."
  exit 1
fi

echo "[*] Pulling efabless/openlane:2023.05.01 Docker Image (~15GB)..."
docker pull efabless/openlane:2023.05.01

echo "[*] Setting up Volare (PDK Version Manager)..."
pip install volare

echo "[*] Downloading SkyWater 130nm PDK (~5GB)..."
export PDK_ROOT=$HOME/pdk
mkdir -p $PDK_ROOT
# Volare automatically fetches the exact git commit used by Caravel MPW-9
volare enable --pdk sky130 e029fbf99c670b89ebcbf12edb95f2d5731b81e4

echo "================================================================"
echo " SETUP COMPLETE!                                                "
echo "================================================================"
echo " You are now ready for the physical tape-out."
echo " To run the 8-hour synthesis, placement, and routing flow:"
echo "   $ cd open_silicon/"
echo "   $ make harden"
echo "================================================================"
