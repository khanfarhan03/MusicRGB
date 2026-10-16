"""Build the portable Music wave executable with PyInstaller's default temp path."""
import subprocess
import sys
import os
from pathlib import Path

from prepare_tcl import configure_tcl

if __name__ == "__main__":
    environment = os.environ.copy()
    environment.update(configure_tcl())
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile",
        "--windowed", "--name", "MusicRGB-MusicWave", "--collect-all", "pyaudiowpatch",
        "--hidden-import", "pystray._win32", "music_rgb.py"],
        cwd=Path(__file__).resolve().parent, check=True, env=environment)
