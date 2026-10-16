@echo off
cd /d "%~dp0"
if not exist ".venv-vivobook\Scripts\python.exe" (
    echo Run Setup.cmd first.
    pause
    exit /b 1
)
".venv-vivobook\Scripts\python.exe" prepare_tcl.py
if errorlevel 1 goto failed
set "TCL_LIBRARY=%~dp0.tcl-runtime\tcl_library"
set "TK_LIBRARY=%~dp0.tcl-runtime\tk_library"
".venv-vivobook\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 goto failed
".venv-vivobook\Scripts\python.exe" -m unittest -v test_audio test_settings
if errorlevel 1 goto failed
".venv-vivobook\Scripts\python.exe" build_exe.py
if errorlevel 1 goto failed
echo Built dist\MusicRGB-MusicWave.exe
pause
exit /b 0
:failed
echo Build failed. Check the error above.
pause
exit /b 1
