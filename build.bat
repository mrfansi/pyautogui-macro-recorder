
@echo off

:: Install requirements
pip install -r requirements.txt
pip install pyinstaller

:: Run PyInstaller
python setup.py