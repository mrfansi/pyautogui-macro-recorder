#!/bin/bash

# Install requirements
pip install -r requirements.txt
pip install pyinstaller

# Run PyInstaller
python setup.py

# Set executable permissions for macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    chmod -R +x ./dist/PyAutoGUI-Macro.app
    chmod +x ./dist/PyAutoGUI-Macro.app/Contents/MacOS/PyAutoGUI-Macro
else
    chmod +x ./dist/PyAutoGUI-Macro
fi