@echo off
cd /d "%~dp0"
if not exist ".venv-vivobook\Scripts\python.exe" (
    echo Run Setup.cmd first.
    pause
    exit /b 1
)
set "TCL_LIBRARY=%~dp0.tcl-runtime\tcl_library"
set "TK_LIBRARY=%~dp0.tcl-runtime\tk_library"
".venv-vivobook\Scripts\python.exe" music_rgb.py
if errorlevel 1 pause
