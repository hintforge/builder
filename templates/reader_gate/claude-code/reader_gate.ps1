# Hintforge reader gate -- PreToolUse hook for one guide folder.
#
# Blocks (exit 2) the FIRST read of this guide's files in a session until a hintforge-family
# skill (hintforge-reader, or the hintforge builder) has loaded, then allows every later call
# (block-once). Without the reader skill the AI answers from guide files with no spoiler rules;
# this gate makes it load the skill first.
#
# Contract (every port keeps it):
#   - block only the first read of a guide file in a session with no hintforge skill loaded;
#   - never block CLAUDE.md, AGENTS.md, README.md or DISCLAIMER.md (reading a shim is how the
#     skill gets loaded);
#   - block once per session, then allow;
#   - fail open (exit 0) on any error, so a gate problem never stops a session.
#
# Lives at <guide>/.claude/reader_gate.ps1 (Claude Code) or <guide>/.codex/reader_gate.ps1
# (Codex). The guide root is the parent of this script's folder. Registered in that folder's
# settings.json / hooks.json, so it only ever runs for this guide.
#
# Shell commands cannot be parsed for intent perfectly, so the shell branch is deliberately
# conservative: it needs a read VERB and a guide TARGET together. A missed shell read costs
# nothing; a spurious block teaches the AI to re-issue past the gate, which is the expensive
# failure. When in doubt the shell branch stays silent.

try {
    $raw = [Console]::In.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
    $j = $raw | ConvertFrom-Json
    $tool = "$($j.tool_name)"
    $cwd  = "$($j.cwd)"
    $tp   = "$($j.transcript_path)"
    $sid  = "$($j.session_id)"

    $readClass  = @('Read','Grep','Glob')
    $shellClass = @('Bash','PowerShell')
    if (($readClass -notcontains $tool) -and ($shellClass -notcontains $tool)) { exit 0 }

    $root = (Split-Path -Parent $PSScriptRoot) -replace '\\', '/'
    $root = $root.TrimEnd('/') + '/'
    function Test-InGuide([string]$p) {
        $q = $p -replace '\\', '/'
        $isAbs = ($q -match '^[A-Za-z]:/') -or ($q -match '^/')
        if (-not $isAbs) { return $true }   # relative paths resolve inside the session folder
        return $q.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase) -or ($q.TrimEnd('/') + '/').Equals($root, [System.StringComparison]::OrdinalIgnoreCase)
    }

    # Reading a shim IS the activation path, so gating it would be circular. CHECKPOINT.md is
    # deliberately NOT here: the first CHECKPOINT read is where unguarded answers start.
    $exclude = @('CLAUDE.md','AGENTS.md','README.md','DISCLAIMER.md')

    if ($shellClass -contains $tool) {
        $cmd = "$($j.tool_input.command)"
        if ([string]::IsNullOrWhiteSpace($cmd)) { exit 0 }

        # (1) Read VERB: the ways a shell prints file contents. Listing commands are left alone.
        $readVerb = '(?i)(^|[|;&(]\s*|\s)(cat|bat|head|tail|less|more|nl|strings|sed|awk|grep|egrep|fgrep|rg|ack|type|gc|Get-Content|Select-String|sls|Import-Csv)\s'
        $gitShow  = '(?i)\bgit\s+show\s'
        if (($cmd -notmatch $readVerb) -and ($cmd -notmatch $gitShow)) { exit 0 }

        # (2) Guide TARGET: a guide-shaped file token inside this guide, a known guide subfolder,
        #     or a recursive sweep from inside the guide.
        $tokens = @([regex]::Matches($cmd, '(?i)[A-Za-z0-9_.:\\/-]+\.(md|json|csv|txt|yml|yaml)') | ForEach-Object { $_.Value } | Where-Object { Test-InGuide $_ })
        $guideDir  = $cmd -match '(?i)(^|[\s"''\\/])(nav|sections|items|reference|npcs|factions|crew|reputation|_overflow|artifacts)[\\/]'
        $recursive = (($cmd -match '(?i)\s-{1,2}[A-Za-z]*r[A-Za-z]*(\s|$)') -or ($cmd -match '(?i)\s-Recurse\b')) -and (Test-InGuide $cwd)
        if (($tokens.Count -eq 0) -and (-not $guideDir) -and (-not $recursive)) { exit 0 }

        # (3) Shim-only: every named file is a shim and nothing broader is being swept.
        if (($tokens.Count -gt 0) -and (-not $guideDir) -and (-not $recursive)) {
            $sawGuideFile = $false
            foreach ($t in $tokens) {
                $leaf = Split-Path -Leaf ($t -replace '\\', '/')
                if ($exclude -notcontains $leaf) { $sawGuideFile = $true }
            }
            if (-not $sawGuideFile) { exit 0 }
        }
    }
    else {
        # Read -> file_path; Grep/Glob -> path (defaults to the session folder).
        $target = "$($j.tool_input.file_path)"
        if ([string]::IsNullOrWhiteSpace($target)) { $target = "$($j.tool_input.path)" }
        if ([string]::IsNullOrWhiteSpace($target)) { $target = $cwd }
        if (-not (Test-InGuide $target)) { exit 0 }
        $base = Split-Path -Leaf $target
        if ($exclude -contains $base) { exit 0 }
    }

    # Block once per session: a session already blocked once goes through (checked first, as it
    # is the cheaper test and either way the call is allowed).
    $safeSid = ($sid -replace '[^A-Za-z0-9_-]', '_')
    $flag = Join-Path ([System.IO.Path]::GetTempPath()) ('hintforge_guide_gate_' + $safeSid + '.flag')
    if (Test-Path -LiteralPath $flag) { exit 0 }

    # Satisfied-if: the hintforge or hintforge-reader skill loaded this session. Every transcript
    # line that mentions hintforge is parsed as JSON, and only a recorded tool call counts:
    #   - a Skill call naming hintforge or hintforge-reader (a plugin prefix like "x:" is allowed);
    #   - a Read whose file_path is a hintforge SKILL.md;
    #   - a Codex shell call (function_call, local_shell_call, custom_tool_call) whose command
    #     reads that file with a read verb (cat, Get-Content, ...), for runtimes that load skills
    #     through the shell.
    # Text that names the path -- the player's or the AI's own -- and a shell call that only
    # echoes it have loaded nothing. A /hintforge slash command, which the runtime writes into the
    # transcript as the player's message, also counts.
    $skillName = '(?i)^([A-Za-z0-9_-]+:)?hintforge(-reader)?$'
    $skillPath = '(?i)(^|[\\/])hintforge(-reader)?[\\/]+SKILL\.md$'
    $slash     = '<command-name>/([A-Za-z0-9_-]+:)?hintforge(-reader)?</command-name>'
    $sk        = 'hintforge(-reader)?[\\/]+SKILL\.md'
    $arg       = '("[^"]*' + $sk + '"|''[^'']*' + $sk + '''|[^\s"'';|&<>]*' + $sk + ')'
    $shellRead = '(?i)(^\s*|[;&|(]\s*)(cat|type|more|less|head|tail|bat|nl|gc|Get-Content|sed\s+-n\s+(''[^'']*''|"[^"]*"|\S+))(\s+-{1,2}[A-Za-z]+(\s+\d+)?)*\s+' + $arg + '(\s|$|[;|&)])'
    function Get-ShellCommands($it) {
        $out = @()
        $ty = "$($it.type)"
        $nm = "$($it.name)"
        if ($ty -eq 'local_shell_call') {
            $out += @($it.action.command | ForEach-Object { "$_" })
        }
        elseif (($ty -eq 'function_call') -and ($nm -match '(?i)shell|exec')) {
            $a = $null
            try { $a = "$($it.arguments)" | ConvertFrom-Json } catch {}
            if ($a) { foreach ($k in 'cmd', 'command') { if ($null -ne $a.$k) { $out += @($a.$k | ForEach-Object { "$_" }) } } }
        }
        elseif (($ty -eq 'custom_tool_call') -and ($nm -match '(?i)shell|exec')) {
            $src = "$($it.input)"
            $ms = [regex]::Matches($src, '\b(cmd|command)\s*:\s*"((?:[^"\\]|\\.)*)"')
            if ($ms.Count -eq 0) { $out += $src }
            foreach ($m in $ms) { $out += ($m.Groups[2].Value -replace '\\(["\\])', '$1') }
        }
        return , $out
    }
    if (-not [string]::IsNullOrEmpty($tp) -and (Test-Path -LiteralPath $tp)) {
        foreach ($m in @(Select-String -LiteralPath $tp -Pattern 'hintforge' -SimpleMatch -ErrorAction SilentlyContinue)) {
            $o = $null
            try { $o = $m.Line | ConvertFrom-Json } catch { continue }
            if ($null -eq $o) { continue }
            $content = $o.message.content
            if (("$($o.type)" -eq 'user') -and ($content -is [string]) -and ($content -match $slash)) { exit 0 }
            if (("$($o.type)" -eq 'assistant') -and ($null -ne $content) -and ($content -isnot [string])) {
                foreach ($b in @($content)) {
                    if ("$($b.type)" -ne 'tool_use') { continue }
                    if (("$($b.name)" -eq 'Skill') -and ("$($b.input.skill)" -match $skillName)) { exit 0 }
                    if (("$($b.name)" -eq 'Read') -and ("$($b.input.file_path)" -match $skillPath)) { exit 0 }
                }
            }
            # Codex rollouts wrap each item in "payload"; older ones put it at the top level.
            foreach ($it in @($o, $o.payload)) {
                if ($null -eq $it) { continue }
                foreach ($c in (Get-ShellCommands $it)) { if ($c -match $shellRead) { exit 0 } }
            }
        }
    }

    try { Set-Content -LiteralPath $flag -Value '1' -ErrorAction SilentlyContinue } catch {}

    $shellNote = ''
    if ($shellClass -contains $tool) {
        $shellNote = ' (This read came through the shell; the same rule applies to any tool that opens guide files.)'
    }
    [Console]::Error.WriteLine("HINTFORGE GATE: this is a hintforge guide folder and no hintforge skill has loaded this session. Do not answer a game question or change the guide from a direct file read. FIRST load the hintforge skill that matches the task -- hintforge-reader for play help, or the hintforge builder for guide maintenance (doctor, ingestion, stitch, fixing or updating the guide) -- then proceed." + $shellNote + " If the Skill tool reports that no hintforge skill is installed, re-issue this call to proceed. Deciding that this task is not a hintforge task is not a reason to skip: any read of this guide's files needs the matching skill first.")
    exit 2
}
catch {
    exit 0
}
