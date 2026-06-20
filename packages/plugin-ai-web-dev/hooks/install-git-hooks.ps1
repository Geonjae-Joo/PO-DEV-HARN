<#
  ───────────────────────────────────────────────────────────────────────
  PO-DEV-HARN — git hook 설치기 (Windows / PowerShell)

  git은 Windows에서도 훅을 번들된 sh로 실행하므로, 설치되는 훅 파일 본문은
  PowerShell이 아니라 셸 스크립트다(.sh 내용). 이 .ps1은 그 셸 훅을 써넣는
  '설치 편의 도구'일 뿐이다. tdd-gate·commit-spine-id는 메시지($1)가 필요하므로
  commit-msg 훅에, manifest-sync는 post-commit 훅에 설치한다.

  사용: app_repo 루트에서 플러그인 경로의 이 스크립트를 실행
    powershell -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\hooks\install-git-hooks.ps1"
  옵션:
    -Python "python"            # 파이썬 실행기 (기본 python → 없으면 py)
    -HarnessTestCmd "..."       # tdd-gate 테스트 명령(foundation/decisions/tech-stack.md 핀). 훅에 기록.
  ───────────────────────────────────────────────────────────────────────
#>
param(
  [string]$Python = "",
  [string]$HarnessTestCmd = ""
)
$ErrorActionPreference = "Stop"

$HooksSrcDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$gitDir = (& git rev-parse --git-dir 2>$null)
if (-not $gitDir) {
  Write-Error "현재 위치가 git 저장소가 아닙니다. app_repo 루트에서 실행하세요."
  exit 1
}
$gitDir = (Resolve-Path $gitDir).Path
$hookDst = Join-Path $gitDir "hooks"
New-Item -ItemType Directory -Force -Path $hookDst | Out-Null

# 파이썬 실행기 결정
$py = $Python
if (-not $py) {
  if (Get-Command python -ErrorAction SilentlyContinue) { $py = "python" }
  elseif (Get-Command py -ErrorAction SilentlyContinue) { $py = "py" }
  else { Write-Error "python 실행기를 찾을 수 없습니다. -Python 으로 지정하세요."; exit 1 }
}

# git Bash가 해석할 수 있도록 경로를 슬래시로
$srcUnix = $HooksSrcDir -replace '\\','/'

$testCmdLine = ""
if ($HarnessTestCmd) {
  $escaped = $HarnessTestCmd -replace "'","'\''"
  $testCmdLine = "export HARNESS_TEST_CMD='$escaped'"
}

function Backup-Hook($path) {
  if ((Test-Path $path) -and -not (Select-String -Path $path -Pattern "PO-DEV-HARN-HOOK" -Quiet)) {
    $stamp = [int][double]::Parse((Get-Date -UFormat %s))
    Move-Item $path "$path.bak.$stamp"
    Write-Host "  기존 $(Split-Path $path -Leaf) → 백업"
  }
}

# ── commit-msg (LF 줄바꿈으로 기록) ──────────────────────────────────────
$commitMsg = @"
#!/usr/bin/env bash
# PO-DEV-HARN-HOOK (commit-msg) — 자동 생성. 수정하지 말 것.
set -e
$testCmdLine
HOOKS_DIR="$srcUnix"
"$py" "`${HOOKS_DIR}/tdd-gate.py" "`$1" || exit 1
"$py" "`${HOOKS_DIR}/commit-spine-id.py" "`$1" || exit 1
"@
Backup-Hook (Join-Path $hookDst "commit-msg")
[IO.File]::WriteAllText((Join-Path $hookDst "commit-msg"), ($commitMsg -replace "`r`n","`n"))

# ── post-commit ─────────────────────────────────────────────────────────
$postCommit = @"
#!/usr/bin/env bash
# PO-DEV-HARN-HOOK (post-commit) — 자동 생성. 수정하지 말 것.
HOOKS_DIR="$srcUnix"
"$py" "`${HOOKS_DIR}/manifest-sync.py" || true
"@
Backup-Hook (Join-Path $hookDst "post-commit")
[IO.File]::WriteAllText((Join-Path $hookDst "post-commit"), ($postCommit -replace "`r`n","`n"))

Write-Host "✔ 설치 완료"
Write-Host "  → $hookDst\commit-msg   (tdd-gate + commit-spine-id, blocking)"
Write-Host "  → $hookDst\post-commit  (manifest-sync, non-blocking)"
Write-Host "  python: $py"
if ($testCmdLine) { Write-Host "  HARNESS_TEST_CMD 고정됨" }
else { Write-Host "  HARNESS_TEST_CMD 미지정 — tdd-gate 자동 탐지 사용(foundation/decisions/tech-stack.md 권장)" }
