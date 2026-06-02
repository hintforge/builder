# Stop hook: speak the last assistant message using a Microsoft neural voice.
# Reads Claude Code Stop-hook JSON from stdin, extracts the last assistant
# message text from the transcript JSONL, strips markdown, synthesizes via
# edge-tts (en-US-AvaNeural -- Microsoft's Copilot voice), and plays the MP3.
#
# Falls back silently on any failure -- never blocks the session.

try {
    # Global log lives in user home so it captures decisions for sessions in any folder
    # (including ones we exit early from). Per-game folders are determined by the allowlist.
    $logPath = Join-Path $env:USERPROFILE ".claude\tts_hook.log"
    "$(Get-Date -Format o) hook fired" | Out-File -FilePath $logPath -Append -Encoding utf8
    $stdin = [Console]::In.ReadToEnd()
    "$(Get-Date -Format o) stdin len=$($stdin.Length)" | Out-File -FilePath $logPath -Append -Encoding utf8
    if ([string]::IsNullOrWhiteSpace($stdin)) { exit 0 }
    $j = $stdin | ConvertFrom-Json
    $tp = $j.transcript_path
    $cwd = $j.cwd
    "$(Get-Date -Format o) cwd=$cwd tp=$tp" | Out-File -FilePath $logPath -Append -Encoding utf8
    if (-not $tp -or -not (Test-Path -LiteralPath $tp)) { exit 0 }

    # Resolve cwd to canonical path so trailing slashes / case / symlinks don't break matching.
    $resolvedCwd = $null
    if ($cwd) {
        try { $resolvedCwd = (Resolve-Path -LiteralPath $cwd -ErrorAction SilentlyContinue).Path } catch { $resolvedCwd = $cwd }
    }

    # Allowlist: read game-folder paths from ~/.claude/tts_game_folders.txt (one per line, # for comments).
    # No fallback -- if the config is missing or empty, the hook is a no-op. The framework supports
    # multiple games, so no single hardcoded path makes sense as a default.
    $configPath = Join-Path $env:USERPROFILE ".claude\tts_game_folders.txt"
    $gameFolders = @()
    if (Test-Path $configPath) {
        $gameFolders = Get-Content $configPath -ErrorAction SilentlyContinue |
            Where-Object { $_ -and $_.Trim() -ne '' -and -not $_.Trim().StartsWith('#') } |
            ForEach-Object { $_.Trim() }
    }
    if ($gameFolders.Count -eq 0) {
        "$(Get-Date -Format o) skipped: no game folders in ~/.claude/tts_game_folders.txt" | Out-File -FilePath $logPath -Append -Encoding utf8
        exit 0
    }

    # Path guard: cwd must be inside one of the allowlisted game folders. Strict prefix
    # match (not substring), so sibling folders with similar name prefixes don't match.
    $activeGameFolder = $null
    if ($resolvedCwd) {
        foreach ($folder in $gameFolders) {
            try {
                $resolvedFolder = (Resolve-Path -LiteralPath $folder -ErrorAction SilentlyContinue).Path
                if (-not $resolvedFolder) { continue }
                if ($resolvedCwd.StartsWith($resolvedFolder, [System.StringComparison]::OrdinalIgnoreCase)) {
                    $rest = $resolvedCwd.Substring($resolvedFolder.Length)
                    if ($rest -eq '' -or $rest.StartsWith('\') -or $rest.StartsWith('/')) {
                        $activeGameFolder = $resolvedFolder
                        break
                    }
                }
            } catch { }
        }
    }
    if (-not $activeGameFolder) {
        "$(Get-Date -Format o) skipped: cwd not in any allowlisted game folder (cwd=$resolvedCwd)" | Out-File -FilePath $logPath -Append -Encoding utf8
        exit 0
    }
    "$(Get-Date -Format o) active game folder: $activeGameFolder" | Out-File -FilePath $logPath -Append -Encoding utf8

    # Disable flag: per-folder. /voice slash command toggles this file's existence.
    $flagPath = Join-Path $activeGameFolder ".claude\tts_disabled.flag"
    if (Test-Path $flagPath) {
        "$(Get-Date -Format o) skipped: disabled by /voice in $activeGameFolder" | Out-File -FilePath $logPath -Append -Encoding utf8
        exit 0
    }

    # Kill any prior in-progress speech so a new reply preempts the old one.
    $pidFile = Join-Path $activeGameFolder ".claude\tts_hook.pid"
    if (Test-Path $pidFile) {
        $oldPid = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
        if ($oldPid -match '^\d+$') {
            try {
                $proc = Get-Process -Id ([int]$oldPid) -ErrorAction SilentlyContinue
                if ($proc) {
                    "$(Get-Date -Format o) killing prior tts pid=$oldPid" | Out-File -FilePath $logPath -Append -Encoding utf8
                    Stop-Process -Id ([int]$oldPid) -Force -ErrorAction SilentlyContinue
                }
            } catch {}
        }
    }
    $PID | Out-File -FilePath $pidFile -Encoding ascii -Force
    $globalPidFile = Join-Path $env:TEMP "tts_active.pid"
    $PID | Out-File -FilePath $globalPidFile -Encoding ascii -Force

    # Find the most recent assistant message. Stop hook fires *after* the assistant
    # turn, so the message we want is almost always the very last line. Walk
    # backwards and break on the first match -- parsing every line forward (as the
    # original implementation did) was 10-20s on transcripts with multi-MB tool-call
    # lines. Tail 30 is plenty of slack for "last 1-2 lines might be hook events
    # rather than assistant messages."
    $parseStart = Get-Date
    $lines = Get-Content -LiteralPath $tp -Tail 30
    $last = $null
    for ($i = $lines.Count - 1; $i -ge 0; $i--) {
        try { $obj = $lines[$i] | ConvertFrom-Json } catch { continue }
        if ($obj.type -eq 'assistant' -or $obj.role -eq 'assistant') { $last = $obj; break }
    }
    $parseMs = [int]((Get-Date) - $parseStart).TotalMilliseconds
    "$(Get-Date -Format o) parsed transcript in ${parseMs}ms" | Out-File -FilePath $logPath -Append -Encoding utf8
    if (-not $last) { exit 0 }

    # Content shape varies: try $last.message.content, then $last.content.
    $content = $null
    if ($last.message -and $last.message.content) { $content = $last.message.content }
    elseif ($last.content) { $content = $last.content }
    if (-not $content) { exit 0 }

    # Concatenate all text-type blocks.
    $parts = @()
    foreach ($block in $content) {
        if ($block -is [string]) { $parts += $block }
        elseif ($block.type -eq 'text' -and $block.text) { $parts += $block.text }
    }
    $text = ($parts -join "`n").Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { exit 0 }

    # If the reply is long (>300 chars), only speak the first non-empty line --
    # the user can read the rest. Keeps voice as a quick lead-in, not a recital.
    if ($text.Length -gt 300) {
        $firstLine = ($text -split "`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
        if ($firstLine) { $text = $firstLine.Trim() }
        "$(Get-Date -Format o) long reply: speaking first line only" | Out-File -FilePath $logPath -Append -Encoding utf8
    }

    # Strip markdown noise that sounds awful when spoken.
    $text = [regex]::Replace($text, '```[\s\S]*?```', ' ')          # code fences
    $text = [regex]::Replace($text, '`[^`]*`', ' ')                  # inline code
    $text = [regex]::Replace($text, '\[([^\]]+)\]\([^\)]+\)', '$1')  # markdown links → label
    $text = [regex]::Replace($text, 'https?://\S+', ' ')             # bare URLs
    $text = [regex]::Replace($text, '[*_#>~]', '')                   # markdown emphasis chars
    # Defensive TTS-output strip: replace em/en dashes with commas. Neural voices read the
    # raw character as either an awkward overlong pause or the literal word "dash". Lower-effort
    # models don't always honor the persona's "no em dash" rule -- belt-and-suspenders.
    $text = [regex]::Replace($text, '[---]', ', ')          # en dash, em dash → comma
    $text = [regex]::Replace($text, '\s+', ' ').Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { exit 0 }

    # Cap length so a runaway message can't tie up the speech engine forever.
    if ($text.Length -gt 1500) { $text = $text.Substring(0, 1500) + '...' }

    # Select voice based on active persona (read from the active game folder's persona.md).
    # NORA → Ava (US neural female, Copilot voice).
    # Charles → Ryan (UK neural male, slowed for condescending pace).
    $persona = 'NORA'  # default
    $personaFile = Join-Path $activeGameFolder "persona.md"
    if (Test-Path $personaFile) {
        $personaContent = Get-Content $personaFile -Raw
        if ($personaContent -match '(?s)## Current active persona\s*\n+\s*\*\*(\w+)\*\*') {
            $persona = $Matches[1]
        }
    }
    $voice = 'en-US-AvaNeural'
    $rateArg = $null
    if ($persona -eq 'Charles') {
        $voice = 'en-GB-RyanNeural'
        $rateArg = '--rate=-8%'
    }
    "$(Get-Date -Format o) persona=$persona voice=$voice" | Out-File -FilePath $logPath -Append -Encoding utf8

    # Synthesize via edge-tts (Microsoft neural voice). Uses python on PATH;
    # if your Python lives in a non-PATH location, change $py to the full path.
    $audio = Join-Path $env:TEMP "tts_$($PID)_$([guid]::NewGuid().ToString('N')).mp3"
    $py = 'python'
    # Write text to a temp file and use edge-tts's -f flag instead of -t.
    # PowerShell's native-command argument parsing mangles strings containing
    # quotes, apostrophes, ampersands, parens, and other special chars -- the
    # mangled args caused edge-tts to receive an effectively-empty -t and
    # print its usage message (failure mode logged 2026-05-16 22:49 / 22:56,
    # was incorrectly attributed to "Microsoft endpoint blips" for weeks).
    # -f reads from a UTF-8 file and is immune to PowerShell quoting hell.
    $textFile = Join-Path $env:TEMP "tts_$($PID)_$([guid]::NewGuid().ToString('N')).txt"
    [System.IO.File]::WriteAllText($textFile, $text, [System.Text.UTF8Encoding]::new($false))
    # Capture stderr/stdout so failure diagnostics land in the log instead of being swallowed.
    if ($rateArg) {
        $ttsOut = & $py -m edge_tts -v $voice $rateArg -f $textFile --write-media $audio 2>&1
    } else {
        $ttsOut = & $py -m edge_tts -v $voice -f $textFile --write-media $audio 2>&1
    }
    Remove-Item $textFile -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $audio) -or (Get-Item $audio -ErrorAction SilentlyContinue).Length -eq 0) {
        $errSummary = if ($ttsOut) { ($ttsOut | Out-String).Trim() -replace "`r?`n", " | " } else { '<no output>' }
        if ($errSummary.Length -gt 500) { $errSummary = $errSummary.Substring(0, 500) + '...[truncated]' }
        "$(Get-Date -Format o) edge-tts failed to produce audio; stderr: $errSummary" | Out-File -FilePath $logPath -Append -Encoding utf8
        Remove-Item $audio -Force -ErrorAction SilentlyContinue
        exit 0
    }

    Add-Type -AssemblyName presentationCore
    $mp = New-Object System.Windows.Media.MediaPlayer
    $mp.Open([System.Uri]::new($audio))
    # Wait for NaturalDuration to load (cap 3s).
    $waited = 0
    while (-not $mp.NaturalDuration.HasTimeSpan -and $waited -lt 3000) {
        Start-Sleep -Milliseconds 50
        $waited += 50
    }
    $dur = if ($mp.NaturalDuration.HasTimeSpan) { $mp.NaturalDuration.TimeSpan.TotalSeconds } else { 60 }
    $mp.Volume = 1.0
    $mp.Play()
    Start-Sleep -Seconds ([math]::Ceiling($dur + 0.3))
    $mp.Stop()
    $mp.Close()
    Remove-Item $audio -Force -ErrorAction SilentlyContinue

    try {
        if (Test-Path $pidFile) {
            $cur = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
            if ($cur -eq "$PID") { Remove-Item $pidFile -Force -ErrorAction SilentlyContinue }
        }
        if (Test-Path $globalPidFile) {
            $cur = (Get-Content $globalPidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
            if ($cur -eq "$PID") { Remove-Item $globalPidFile -Force -ErrorAction SilentlyContinue }
        }
    } catch {}
}
catch {
    # Never block the session on TTS errors.
    exit 0
}
