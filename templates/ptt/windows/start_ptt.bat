@echo off
REM Launches the PTT daemon and AHK hotkey script. Double-click to start.
REM Both run in the background; close them via Task Manager or Ctrl+Alt+Q (AHK).

set SCRIPT_DIR=%~dp0

REM Start the daemon (windowless via pythonw on PATH). If your Python lives in
REM a non-PATH location, set the PYTHONW env var or edit this line.
start "" /B pythonw "%SCRIPT_DIR%ptt_daemon.py"

REM Give the daemon a moment to start (model load happens in the background;
REM the AHK script gates on the ready-flag so this is just to avoid a race).
timeout /t 1 /nobreak >nul

REM Start the AHK hotkey script.
start "" "%SCRIPT_DIR%ptt.ahk"

echo PTT starting. Whisper model loads in the background (~2s on first run).
echo Hold your configured PTT key to talk. Ctrl+Alt+Q exits the AHK script.
echo (Close the daemon via Task Manager: pythonw.exe running ptt_daemon.py)
timeout /t 3 /nobreak >nul
