#!/bin/bash
echo "[INFO] Creating project dir..."
# Make project dir
make -p /Development/Assistant
cd ~/Development/Assistant
echo "[INFO] Cloning snowboy repo..."
# Clone repo
git clone https://github.com/Makerspot/snowboy.git

echo "[INFO] Compiling swig for Raspbian Stretch."
# Recompile for Raspbian Stretch
sudo ln -s /usr/bin/swig3.0 /usr/local/bin/swig
cd ~/Development/Assistant/snowboy/swig/Python3
make
cd /
