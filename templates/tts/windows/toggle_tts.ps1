# Toggle the TTS hook on/off and silence any in-progress speech.
# Invoked by the /voice slash command.
#
# Path-relative: this script lives in <game>/.claude/ and writes flag/pid/log
# files to its own directory. Move the per-game folder anywhere; this script
# follows. No hardcoded paths.

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$flagPath  = Join-Path $ScriptDir "tts_disabled.flag"
$pidFile   = Join-Path $ScriptDir "tts_hook.pid"
$logPath   = Join-Path $ScriptDir "tts_hook.log"

# Always silence anything currently speaking, regardless of the toggle direction.
if (Test-Path $pidFile) {
    $oldPid = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($oldPid -match '^\d+$') {
        try {
            $proc = Get-Process -Id ([int]$oldPid) -ErrorAction SilentlyContinue
            if ($proc) { Stop-Process -Id ([int]$oldPid) -Force -ErrorAction SilentlyContinue }
        } catch {}
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

if (Test-Path $flagPath) {
    Remove-Item $flagPath -Force
    "$(Get-Date -Format o) /voice: enabled" | Out-File -FilePath $logPath -Append -Encoding utf8
    Write-Output "TTS ON"
} else {
    "$(Get-Date -Format o) disabled by /voice" | Out-File -FilePath $flagPath -Encoding utf8
    "$(Get-Date -Format o) /voice: disabled" | Out-File -FilePath $logPath -Append -Encoding utf8
    Write-Output "TTS OFF"
}
