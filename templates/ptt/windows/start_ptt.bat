@echo off
REM Launches the PTT daemon and AHK hotkey script. Double-click to start.
REM Both run in the background; close them via Task Manager or Ctrl+Alt+Q (AHK).

set SCRIPT_DIR=%~dp0

REM Start the daemon, windowless. Interpreter resolution order:
REM   1. %PYTHONW% -- set this to a full pythonw.exe path to force one interpreter.
REM   2. pyw -3    -- the Windows py launcher's registered default 3.x.
REM   3. pythonw   -- whatever is first on PATH.
REM Bare pythonw is LAST on purpose. A machine with more than one Python install
REM often has a different one first on PATH than the one the packages were pip
REM installed into; the daemon then exits instantly with ModuleNotFoundError, and
REM because it is windowless you see nothing at all -- PTT just never becomes
REM ready and the hotkey does nothing. If that happens, run
REM   python ptt_daemon.py
REM in a console from this folder: the traceback names the missing package, and
REM `py -0p` lists every interpreter so you can point %PYTHONW% at the right one.
if defined PYTHONW (
    start "" /B "%PYTHONW%" "%SCRIPT_DIR%ptt_daemon.py"
) else (
    where pyw >nul 2>&1
    if errorlevel 1 (
        start "" /B pythonw "%SCRIPT_DIR%ptt_daemon.py"
    ) else (
        start "" /B pyw -3 "%SCRIPT_DIR%ptt_daemon.py"
    )
)

REM Give the daemon a moment to start (model load happens in the background;
REM the AHK script gates on the ready-flag so this is just to avoid a race).
timeout /t 1 /nobreak >nul

REM Start the AHK hotkey script.
start "" "%SCRIPT_DIR%ptt.ahk"

echo PTT starting. Whisper model loads in the background (~2s on first run).
echo Hold your configured PTT key to talk. Ctrl+Alt+Q exits the AHK script.
echo (Close the daemon via Task Manager: pythonw.exe running ptt_daemon.py)
timeout /t 3 /nobreak >nul
