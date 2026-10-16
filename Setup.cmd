@echo off
cd /d "%~dp0"
python -m venv .venv-vivobook
if errorlevel 1 goto failed
".venv-vivobook\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv-vivobook\Scripts\python.exe" prepare_tcl.py
if errorlevel 1 goto failed
set "TCL_LIBRARY=%~dp0.tcl-runtime\tcl_library"
set "TK_LIBRARY=%~dp0.tcl-runtime\tk_library"
".venv-vivobook\Scripts\python.exe" -c "import numpy, pyaudiowpatch, tkinter; tkinter.Tcl()"
if errorlevel 1 goto failed
echo Ready. Open Launch.cmd to start Music RGB.
pause
exit /b 0
:failed
echo Setup failed. Check the error above.
pause
exit /b 1
