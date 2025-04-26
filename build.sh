#!/usr/bin/env bash
# Update package list and install ffmpeg
apt-get update && apt-get install -y ffmpeg

# Install Python dependencies
pip install -r requirements.txt
