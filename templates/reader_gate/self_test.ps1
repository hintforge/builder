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
#   6. a new session where only the player's message names a hintforge SKILL.md -> exit 2
#      (asking for the skill is not loading it)
#   7. a new session whose transcript shows a tool call reading a hintforge SKILL.md -> exit 0
#   8. a new session where the AI's own text names a hintforge SKILL.md beside an unrelated
#      tool call                                                  -> exit 2
#   9. a new session whose only shell calls echo a hintforge SKILL.md path -> exit 2
#  10. a new session whose transcript shows a Codex shell call reading a hintforge SKILL.md -> exit 0
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
$asked = Join-Path $tmp ($run + '_asked.jsonl')
$readSkill = Join-Path $tmp ($run + '_readskill.jsonl')
Set-Content -LiteralPath $asked -Value '{"type":"user","message":{"role":"user","content":"please load .agents/skills/hintforge-reader/SKILL.md before answering"}}'
Set-Content -LiteralPath $readSkill -Value @(
    '{"type":"user","message":{"role":"user","content":"where was I?"}}',
    '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"C:\\guides\\.agents\\skills\\hintforge-reader\\SKILL.md"}}]}}'
)
$aiText = Join-Path $tmp ($run + '_aitext.jsonl')
$echoed = Join-Path $tmp ($run + '_echoed.jsonl')
$codexRead = Join-Path $tmp ($run + '_codexread.jsonl')
Set-Content -LiteralPath $aiText -Value '{"type":"assistant","message":{"content":[{"type":"text","text":"I should read .agents/skills/hintforge-reader/SKILL.md"},{"type":"tool_use","name":"Read","input":{"file_path":"CHECKPOINT.md"}}]}}'
Set-Content -LiteralPath $echoed -Value @(
    '{"type":"response_item","payload":{"type":"function_call","name":"shell","arguments":"{\"command\":[\"bash\",\"-lc\",\"echo .agents/skills/hintforge-reader/SKILL.md\"]}"}}',
    '{"type":"response_item","payload":{"type":"custom_tool_call","name":"exec","input":"text(await tools.exec_command({cmd:\"echo ''.agents/skills/hintforge-reader/SKILL.md''\"}))"}}'
)
Set-Content -LiteralPath $codexRead -Value '{"type":"response_item","payload":{"type":"custom_tool_call","name":"exec","input":"text(await tools.exec_command({cmd:\"Get-Content -Raw -LiteralPath ''.agents/skills/hintforge-reader/SKILL.md''\"}))"}}'

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
$r = Invoke-Gate ($run + '_e') $asked $checkpoint
$results += ,@('6 a player message naming SKILL.md does not count as a load', ($r.Code -eq 2 -and $r.Err -match 'HINTFORGE GATE'), "exit $($r.Code)")
$r = Invoke-Gate ($run + '_f') $readSkill $checkpoint
$results += ,@('7 read after a tool call that read a hintforge SKILL.md is allowed', ($r.Code -eq 0), "exit $($r.Code)")
$r = Invoke-Gate ($run + '_g') $aiText $checkpoint
$results += ,@('8 the AI naming SKILL.md beside an unrelated tool call does not count as a load', ($r.Code -eq 2 -and $r.Err -match 'HINTFORGE GATE'), "exit $($r.Code)")
$r = Invoke-Gate ($run + '_h') $echoed $checkpoint
$results += ,@('9 a shell call that only echoes a SKILL.md path does not count as a load', ($r.Code -eq 2 -and $r.Err -match 'HINTFORGE GATE'), "exit $($r.Code)")
$r = Invoke-Gate ($run + '_i') $codexRead $checkpoint
$results += ,@('10 read after a Codex shell call that read a hintforge SKILL.md is allowed', ($r.Code -eq 0), "exit $($r.Code)")

foreach ($s in 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i') { Remove-Item -LiteralPath (Join-Path $tmp ('hintforge_guide_gate_' + $run + '_' + $s + '.flag')) -ErrorAction SilentlyContinue }
Remove-Item -LiteralPath $empty, $loaded, $asked, $readSkill, $aiText, $echoed, $codexRead -ErrorAction SilentlyContinue

$failed = 0
foreach ($x in $results) {
    if ($x[1]) { Write-Output "PASS $($x[0])" } else { Write-Output "FAIL $($x[0]) ($($x[2]))"; $failed++ }
}
if ($failed) { Write-Output "Reader gate self-test FAILED ($failed of $($results.Count)). Remove its registration; do not report it built."; exit 1 }
Write-Output "Reader gate self-test passed ($($results.Count) of $($results.Count))."
exit 0
