# Voice control script -- start, stop, toggle, or status the TTS hook.
# Invoked by the /voice slash command. Models its action interface on
# ptt_control.ps1 so /voice and /ptt have symmetric verbs.
#
# State is encoded by the presence/absence of tts_disabled.flag in this
# script's directory. The Stop hook (tts_hook.ps1) checks for that flag
# and no-ops if present.
#
# All actions silence any in-progress speech as a side effect (kills the
# PID recorded in tts_hook.pid). That doubles as a "shut up now" button
# regardless of whether you're toggling the flag.

param(
    [ValidateSet('start','stop','toggle','status','')]
    [string]$Action = 'toggle'
)

if ([string]::IsNullOrWhiteSpace($Action)) { $Action = 'toggle' }

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$flagPath  = Join-Path $ScriptDir "tts_disabled.flag"
$pidFile   = Join-Path $ScriptDir "tts_hook.pid"
$logPath   = Join-Path $ScriptDir "tts_hook.log"

function Stop-InProgressSpeech {
    if (-not (Test-Path $pidFile)) { return }
    $oldPid = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($oldPid -match '^\d+$') {
        try {
            $proc = Get-Process -Id ([int]$oldPid) -ErrorAction SilentlyContinue
            if ($proc) { Stop-Process -Id ([int]$oldPid) -Force -ErrorAction SilentlyContinue }
        } catch {}
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

function Enable-Voice {
    Stop-InProgressSpeech
    if (Test-Path $flagPath) { Remove-Item $flagPath -Force -ErrorAction SilentlyContinue }
    "$(Get-Date -Format o) /voice: enabled" | Out-File -FilePath $logPath -Append -Encoding utf8
}

function Disable-Voice {
    Stop-InProgressSpeech
    if (-not (Test-Path $flagPath)) {
        "$(Get-Date -Format o) disabled by /voice" | Out-File -FilePath $flagPath -Encoding utf8
    }
    "$(Get-Date -Format o) /voice: disabled" | Out-File -FilePath $logPath -Append -Encoding utf8
}

switch ($Action) {

    'start' {
        if (-not (Test-Path $flagPath)) {
            Stop-InProgressSpeech  # still kill any current speech for consistency with stop/toggle
            Write-Output 'Voice already on'
            return
        }
        Enable-Voice
        Write-Output 'Voice ON'
    }

    'stop' {
        if (Test-Path $flagPath) {
            Stop-InProgressSpeech  # still kill in case a hook fired between toggle and now
            Write-Output 'Voice already off'
            return
        }
        Disable-Voice
        Write-Output 'Voice OFF'
    }

    'toggle' {
        if (Test-Path $flagPath) {
            Enable-Voice
            Write-Output 'Voice ON'
        } else {
            Disable-Voice
            Write-Output 'Voice OFF'
        }
    }

    'status' {
        if (Test-Path $flagPath) {
            Write-Output 'Voice OFF'
        } else {
            Write-Output 'Voice ON'
        }
    }
}
