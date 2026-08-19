; Push-to-talk for Claude Code. Hold Numpad+ to record; release to transcribe and send.
; Requires AutoHotkey v2. Pairs with ptt_daemon.py (must be running).
;
; Architecture: this script signals the Python daemon via flag files in %TEMP%.
; Daemon does the actual mic capture and Whisper transcription, leaving this
; script as a thin hotkey + window-management layer.

#Requires AutoHotkey v2.0
#SingleInstance Force
SetTitleMatchMode 2  ; substring matching for window titles

; --- Config ---
START_FLAG  := A_Temp . "\ptt_start.flag"
STOP_FLAG   := A_Temp . "\ptt_stop.flag"
RESULT_FILE := A_Temp . "\ptt_result.txt"
READY_FILE  := A_Temp . "\ptt_ready.flag"
TTS_PID_FILE := A_Temp . "\tts_active.pid"

; Window match candidates for Claude Code desktop app. First match wins.
; "Claude ahk_exe claude.exe" requires both: window title contains "Claude"
; AND process is claude.exe -- disambiguates the desktop app from the CLI
; (which is also named claude.exe but has no titled window).
CLAUDE_MATCHES := ["Claude ahk_exe claude.exe", "ahk_exe Claude.exe"]

; Exit hotkey
^!q::ExitApp()

; --- Hotkey: hold Numpad+ to record ---
; Uses KeyWait instead of separate Up/Down handlers so we ignore keyboard
; auto-repeat ticks -- the press handler runs once, blocks on KeyWait until
; physical release, then triggers transcription. This survives keyboards that
; emit synthetic up/down pairs during a hold.
KillTts() {
    global TTS_PID_FILE
    if !FileExist(TTS_PID_FILE)
        return
    try {
        pid := Trim(FileRead(TTS_PID_FILE, "UTF-8"))
        if (pid != "")
            Run('powershell -NoProfile -Command "Stop-Process -Id ' . pid . ' -Force -ErrorAction SilentlyContinue"',, "Hide")
        FileDelete(TTS_PID_FILE)
    }
}

*NumpadAdd:: {
    if !FileExist(READY_FILE) {
        return
    }

    KillTts()

    ; Clear stale result, signal daemon to start.
    if FileExist(RESULT_FILE)
        FileDelete(RESULT_FILE)
    FileAppend("", START_FLAG)

    ; Block until the key is physically released. KeyWait polls real key
    ; state, so auto-repeat down-events during a hold are ignored.
    KeyWait("NumpadAdd")

    ; Signal daemon to stop and transcribe.
    FileAppend("", STOP_FLAG)

    ; Wait for daemon to finish (max 10s).
    timeout := 10000
    elapsed := 0
    while (!FileExist(RESULT_FILE) && elapsed < timeout) {
        Sleep(50)
        elapsed += 50
    }
    if !FileExist(RESULT_FILE)
        return

    text := FileRead(RESULT_FILE, "UTF-8")
    FileDelete(RESULT_FILE)
    text := Trim(text)
    if (text = "")
        return

    ; Find Claude Code window.
    claudeHwnd := 0
    for match in CLAUDE_MATCHES {
        h := WinExist(match)
        if (h) {
            claudeHwnd := h
            break
        }
    }
    if (!claudeHwnd)
        return  ; Claude Code not running

    ; Save current foreground window so we can restore focus afterward.
    prevHwnd := WinGetID("A")

    ; Set clipboard for paste.
    A_Clipboard := text

    ; --- Defeat Windows foreground lock via AttachThreadInput ---
    ; Background: when another process (typically a fullscreen game) owns
    ; foreground, Windows' ForegroundLockTimeout policy refuses bare
    ; WinActivate/SetForegroundWindow calls from non-foreground processes --
    ; the call returns "success" but only flashes the taskbar; window never
    ; actually activates. Send("^v") then lands in the game.
    ;
    ; The standard workaround (documented Win32 lore for ~25 years): attach
    ; our input thread to the foreground window's thread for the duration of
    ; the activation. While threads are attached, our SetForegroundWindow
    ; call is treated as coming from the foreground thread itself and is not
    ; blocked. Detach immediately after.
    ;
    ; Tried 2026-05-16 and rejected: ControlSend("^v", "Chrome_RenderWidgetHostHWND1",...)
    ; bypasses foreground entirely but is a no-op because Blink ignores
    ; synthesized WM_KEYDOWN to non-focused widgets. Activation is required;
    ; we just need it to actually succeed.
    fgHwnd := DllCall("GetForegroundWindow", "Ptr")
    fgThread := DllCall("GetWindowThreadProcessId", "Ptr", fgHwnd, "Ptr", 0, "UInt")
    myThread := DllCall("GetCurrentThreadId", "UInt")
    attached := false
    if (fgThread && fgThread != myThread) {
        attached := DllCall("AttachThreadInput", "UInt", myThread, "UInt", fgThread, "Int", true)
    }

    try {
        WinActivate("ahk_id " . claudeHwnd)
        WinWaitActive("ahk_id " . claudeHwnd, , 0.7)
    } finally {
        if (attached) {
            DllCall("AttachThreadInput", "UInt", myThread, "UInt", fgThread, "Int", false)
        }
    }

    ; There is deliberately NO cursor-moving click-to-focus step here.
    ; An earlier version clicked the input field (SetCursorPos + Click at ~92%
    ; of window height) to force Electron DOM focus after activation. On a
    ; multi-monitor setup -- a game fullscreen on one screen, the assistant
    ; window on another -- that flings the cursor off-screen mid-session and
    ; is untrackable during gameplay, which is the exact context this module
    ; exists for. It was removed after testing showed WinActivate alone lands
    ; DOM focus reliably on current desktop-app builds, including the
    ; fullscreen-game case it was originally added to fix.
    ;
    ; If paste ever lands nowhere, capture the exact conditions BEFORE
    ; re-adding any cursor-moving fix. The escalation path is UIA SetValue
    ; against the Chromium input element (writes to the accessibility tree,
    ; sends no input events) -- not another click.

    Sleep(250)
    Send("^v")
    Sleep(150)
    Send("{Enter}")
    Sleep(150)

    ; Refocus whatever was in front before (usually the game). The 1px mouse
    ; nudge is empirical: kept because the refocus is more reliable with it.
    if (prevHwnd && prevHwnd != claudeHwnd) {
        WinActivate("ahk_id " . prevHwnd)
        Sleep(150)
        MouseMove(1, 0, , "R")
        MouseMove(-1, 0, , "R")
    }
}
