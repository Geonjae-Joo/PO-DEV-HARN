# ────────────────────────────────────────────────────────────────────────
# PO-DEV-HARN — speckit 부트스트랩 설치기 (Windows / PowerShell)
# install-speckit.sh 의 PowerShell 버전. app_repo 에 .specify vendoring + .source + git hook 설치.
# 사용:  powershell -File "$env:CLAUDE_PLUGIN_ROOT\hooks\install-speckit.ps1" [-AppRepo C:\path\to\app_repo]
# ────────────────────────────────────────────────────────────────────────
param(
  [string]$AppRepo = (Get-Location).Path,
  [string]$HarnessTestCmd = ""
)
$ErrorActionPreference = "Stop"

$HooksSrcDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PluginRoot  = Split-Path -Parent $HooksSrcDir
$SpecifySrc  = Join-Path $PluginRoot ".specify"
$AppRepo     = (Resolve-Path $AppRepo).Path

if (-not (Test-Path $SpecifySrc)) { Write-Error "플러그인 .specify 원본 없음: $SpecifySrc"; exit 1 }

Write-Host "▶ speckit 부트스트랩"
Write-Host "  플러그인(원본): $SpecifySrc"
Write-Host "  대상 app_repo : $AppRepo"

# 1) git 저장소 보장
Push-Location $AppRepo
git rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "  git init 실행"; git init -q }

# 2) .specify vendoring (기존 파일 보존)
$DstSpecify = Join-Path $AppRepo ".specify"
New-Item -ItemType Directory -Force -Path $DstSpecify | Out-Null
Get-ChildItem -Recurse -File $SpecifySrc | ForEach-Object {
  $rel = $_.FullName.Substring($SpecifySrc.Length).TrimStart('\','/')
  $dst = Join-Path $DstSpecify $rel
  if (-not (Test-Path $dst)) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    Copy-Item $_.FullName $dst
  }
}
Write-Host "  ✔ .specify vendoring 완료 (기존 파일 보존)"

# 3) .source 기록
$pv = (Select-String -Path (Join-Path $PluginRoot "plugin.json") -Pattern '"version"\s*:\s*"([^"]+)"' | Select-Object -First 1).Matches.Groups[1].Value
$sv = (Select-String -Path (Join-Path $SpecifySrc "init-options.json") -Pattern '"speckit_version"\s*:\s*"([^"]+)"' | Select-Object -First 1).Matches.Groups[1].Value
$now = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
@"
{
  "vendored_from": "plugin-ai-web-dev",
  "plugin_version": "$pv",
  "speckit_version": "$sv",
  "vendored_at": "$now",
  "_note": "메커니즘 단일 원본은 플러그인. 업그레이드는 speckit-sync. 상태(memory/feature.json/overrides)는 sync가 보존."
}
"@ | Set-Content -Encoding UTF8 (Join-Path $DstSpecify ".source")
Write-Host "  ✔ .specify/.source 기록 (plugin@$pv, speckit $sv)"

# 4) git hook 설치
$ghPs1 = Join-Path $HooksSrcDir "install-git-hooks.ps1"
if (Test-Path $ghPs1) {
  if ($HarnessTestCmd) { & $ghPs1 -HarnessTestCmd $HarnessTestCmd } else { & $ghPs1 }
} else {
  Write-Warning "install-git-hooks.ps1 없음 — Git Bash 에서 install-git-hooks.sh 를 실행하세요."
}
Pop-Location

Write-Host "✔ 부트스트랩 완료. 다음: /speckit-constitution → /speckit-specify PACK-<ID>"
