# self_test.ps1 -- prove an installed reader gate works before setup reports it built.
#
# Usage (from anywhere):
#   powershell -NoProfile -ExecutionPolicy Bypass -File self_test.ps1 -Gate <guide>/.claude/reader_gate.ps1 [-Tool Read|Bash]
#
# Feeds the gate fake PreToolUse payloads, exactly as the runtime would, and checks:
#   1. first read of <guide>/CHECKPOINT.md with no skill loaded  -> exit 2 and the deny text
#   2. the same read again in the same session                    -> exit 0 (block once)
#   3. a new session whose transcript shows a hintforge skill load -> exit 0
#   4. a read of README.md (a shim)                               -> exit 0
#   5. a read of a file outside the guide                         -> exit 0
# -Tool Bash sends shell commands (`cat <file>`) instead of Read calls, for runtimes that read
# files through the shell (Codex). Prints one PASS/FAIL line per check; exits 0 only when all pass.
# Cleans up its temporary transcripts and block-once flags.
param(
    [Parameter(Mandatory = $true)][string]$Gate,
    [ValidateSet('Read', 'Bash')][string]$Tool = 'Read'
)

if (-not (Test-Path -LiteralPath $Gate)) { Write-Output "FAIL gate script not found: $Gate"; exit 1 }
$gatePath = (Resolve-Path -LiteralPath $Gate).Path
$guide = Split-Path -Parent (Split-Path -Parent $gatePath)
$tmp = [System.IO.Path]::GetTempPath()
$run = 'hfselftest' + [guid]::NewGuid().ToString('N').Substring(0, 8)
$empty = Join-Path $tmp ($run + '_empty.jsonl')
$loaded = Join-Path $tmp ($run + '_loaded.jsonl')
Set-Content -LiteralPath $empty -Value '{"type":"user","message":"where was I?"}'
Set-Content -LiteralPath $loaded -Value '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Skill","input":{"skill":"hintforge-reader"}}]}}'

function Invoke-Gate([string]$session, [string]$transcript, [string]$file) {
    if ($Tool -eq 'Read') { $input_ = @{ file_path = $file } } else { $input_ = @{ command = "cat `"$file`"" } }
    $payload = @{ session_id = $session; transcript_path = $transcript; cwd = $guide; hook_event_name = 'PreToolUse'; tool_name = $Tool; tool_input = $input_ } | ConvertTo-Json -Compress
    $errFile = Join-Path $tmp ($run + '_err.txt')
    $payload | powershell -NoProfile -ExecutionPolicy Bypass -File $gatePath 2> $errFile | Out-Null
    $code = $LASTEXITCODE
    $err = if (Test-Path -LiteralPath $errFile) { Get-Content -LiteralPath $errFile -Raw } else { '' }
    Remove-Item -LiteralPath $errFile -ErrorAction SilentlyContinue
    return @{ Code = $code; Err = "$err" }
}

$checkpoint = Join-Path $guide 'CHECKPOINT.md'
$outside = Join-Path ([System.IO.Path]::GetTempPath()) 'not_a_guide_file.md'
$results = @()
$r = Invoke-Gate ($run + '_a') $empty $checkpoint
$results += ,@('1 first guide read is blocked', ($r.Code -eq 2 -and $r.Err -match 'HINTFORGE GATE'), "exit $($r.Code)")
$r = Invoke-Gate ($run + '_a') $empty $checkpoint
$results += ,@('2 second read in the same session is allowed', ($r.Code -eq 0), "exit $($r.Code)")
$r = Invoke-Gate ($run + '_b') $loaded $checkpoint
$results += ,@('3 read after a hintforge skill load is allowed', ($r.Code -eq 0), "exit $($r.Code)")
$r = Invoke-Gate ($run + '_c') $empty (Join-Path $guide 'README.md')
$results += ,@('4 shim read is allowed', ($r.Code -eq 0), "exit $($r.Code)")
$r = Invoke-Gate ($run + '_d') $empty $outside
$results += ,@('5 read outside the guide is allowed', ($r.Code -eq 0), "exit $($r.Code)")

foreach ($s in 'a', 'b', 'c', 'd') { Remove-Item -LiteralPath (Join-Path $tmp ('hintforge_guide_gate_' + $run + '_' + $s + '.flag')) -ErrorAction SilentlyContinue }
Remove-Item -LiteralPath $empty, $loaded -ErrorAction SilentlyContinue

$failed = 0
foreach ($x in $results) {
    if ($x[1]) { Write-Output "PASS $($x[0])" } else { Write-Output "FAIL $($x[0]) ($($x[2]))"; $failed++ }
}
if ($failed) { Write-Output "Reader gate self-test FAILED ($failed of $($results.Count)). Remove its registration; do not report it built."; exit 1 }
Write-Output "Reader gate self-test passed ($($results.Count) of $($results.Count))."
exit 0
