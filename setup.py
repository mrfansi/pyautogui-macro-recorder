import os
import sys
from PyInstaller.__main__ import run

def run_build():
    separator = os.pathsep  # Automatically handle OS separator
    
    opts = [
        'main.py',
        '--name=PyAutoGUI-Macro',
        '--clean',
        '--noconfirm',
        '--icon=resources/icon.ico',
        f'--add-data=gui{separator}gui',
        f'--add-data=libs{separator}libs',
    ]
    
    # Use '--onefile' except for macOS
    if sys.platform != 'darwin':
        opts.append('--onefile')
    else:
        opts.extend([
            '--windowed',
            '--codesign-identity=-',
            '--osx-bundle-identifier=com.pyautoguimacro.app',
        ])

    # Add console for debugging
    opts.append('--console')  

    run(opts)

if __name__ == '__main__':
    run_build()