#!/bin/bash

# Make project dir
echo "[INFO] Creating project dir..."
make -p /Development/Assistant
mkdir -p /Development/Assistant
cd /Development/Assistant

# Clone repo
echo "[INFO] Cloning snowboy repo..."
git clone https://github.com/Makerspot/snowboy.git

# Recompile for Raspbian Stretch
echo "[INFO] Compiling swig for Raspbian Stretch."
sudo ln -s /usr/bin/swig3.0 /usr/local/bin/swig
cd /Development/Assistant/snowboy/swig/Python3
make
cd /
