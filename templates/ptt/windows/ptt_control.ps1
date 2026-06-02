# PTT control script -- start, stop, or status the push-to-talk daemon + hotkey.
# Invoked by the /ptt slash command.

param(
    [ValidateSet('start','stop','restart','status','')]
    [string]$Action = 'start'
)

if ([string]::IsNullOrWhiteSpace($Action)) { $Action = 'start' }

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PttDir    = Join-Path (Split-Path -Parent $ScriptDir) 'ptt'
$BatPath   = Join-Path $PttDir 'start_ptt.bat'
$LogPath   = Join-Path $PttDir 'ptt_daemon.log'

$Tmp       = $env:TEMP
$ReadyFlag = Join-Path $Tmp 'ptt_ready.flag'

function Get-PttProcesses {
    $py = Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -and $_.CommandLine -match 'ptt_daemon\.py' }
    $ahk = Get-CimInstance Win32_Process -Filter "Name='AutoHotkey64.exe' OR Name='AutoHotkey32.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -and $_.CommandLine -match 'ptt\.ahk' }
    [pscustomobject]@{ Daemon = @($py); Ahk = @($ahk) }
}

switch ($Action) {

    'start' {
        $procs = Get-PttProcesses
        if ($procs.Daemon.Count -gt 0 -and (Test-Path $ReadyFlag)) {
            Write-Output 'PTT already running and ready'
            return
        }
        if ($procs.Daemon.Count -gt 0 -and -not (Test-Path $ReadyFlag)) {
            Write-Output 'PTT daemon running but not ready yet (model still loading)'
            return
        }

        if (-not (Test-Path $BatPath)) {
            Write-Output "PTT launcher not found at $BatPath"
            return
        }

        Start-Process -FilePath $BatPath -WindowStyle Hidden | Out-Null

        $waited = 0
        while (-not (Test-Path $ReadyFlag) -and $waited -lt 8000) {
            Start-Sleep -Milliseconds 250
            $waited += 250
        }

        if (Test-Path $ReadyFlag) {
            Write-Output 'PTT ready -- hold Numpad+ to talk'
        } else {
            Write-Output 'PTT starting -- model still loading (first run downloads ~150 MB; check /ptt status in ~30 s)'
        }
    }

    'stop' {
        $procs = Get-PttProcesses
        $killed = 0
        foreach ($p in @($procs.Daemon) + @($procs.Ahk)) {
            if ($p -and $p.ProcessId) {
                try {
                    Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
                    $killed++
                } catch {}
            }
        }
        if (Test-Path $ReadyFlag) { Remove-Item $ReadyFlag -ErrorAction SilentlyContinue }
        Write-Output "PTT stopped ($killed process(es) killed)"
    }

    'restart' {
        # Stop + start, re-running this script so we pick up the existing logic
        # for each phase (kill processes, clear flag, relaunch, wait for ready)
        # without duplicating it inline. Daemon stays up across iterations of
        # the AHK script normally, but `restart` is the right verb when the
        # AHK file changed and you want hotkeys re-registered against new code.
        $stopOut    = & $PSCommandPath -Action stop
        Start-Sleep -Milliseconds 300
        $startOut   = & $PSCommandPath -Action start
        Write-Output "$stopOut → $startOut"
    }

    'status' {
        $procs = Get-PttProcesses
        $daemon = if ($procs.Daemon.Count -gt 0) { "daemon: running (pid $($procs.Daemon[0].ProcessId))" } else { 'daemon: not running' }
        $ahk    = if ($procs.Ahk.Count -gt 0)    { "hotkey: registered (pid $($procs.Ahk[0].ProcessId))" } else { 'hotkey: not registered' }
        $rdy    = if (Test-Path $ReadyFlag)      { 'ready: yes' } else { 'ready: no' }
        $tail   = if (Test-Path $LogPath)        { (Get-Content $LogPath -Tail 1 -ErrorAction SilentlyContinue) } else { 'log: absent' }
        Write-Output "$daemon | $ahk | $rdy | last: $tail"
    }
}
