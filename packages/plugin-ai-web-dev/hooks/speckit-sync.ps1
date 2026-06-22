# ────────────────────────────────────────────────────────────────────────
# PO-DEV-HARN — speckit 메커니즘 재동기화 (Windows / PowerShell)
# speckit-sync.sh 의 PowerShell 버전. 메커니즘만 덮어쓰고 상태는 보존.
# 덮어씀: scripts/ · templates/*.md · workflows/ · extensions/<ext>/{scripts,commands,extension.yml,config-template.yml}
# 보존:   memory/ · feature.json · templates/overrides/ · extensions/git/git-config.yml · extensions.yml · *.json 설정
# 사용:  powershell -File "$env:CLAUDE_PLUGIN_ROOT\hooks\speckit-sync.ps1" [-AppRepo C:\path]
# ────────────────────────────────────────────────────────────────────────
param([string]$AppRepo = (Get-Location).Path)
$ErrorActionPreference = "Stop"

$HooksSrcDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PluginRoot  = Split-Path -Parent $HooksSrcDir
$SpecifySrc  = Join-Path $PluginRoot ".specify"
$AppRepo     = (Resolve-Path $AppRepo).Path
$Dst         = Join-Path $AppRepo ".specify"

if (-not (Test-Path $Dst)) { Write-Error "$Dst 없음. 먼저 install-speckit.ps1 로 부트스트랩하세요."; exit 1 }
Write-Host "▶ speckit 메커니즘 재동기화: $SpecifySrc → $Dst"

# scripts/ · workflows/ 전체 덮어쓰기
foreach ($d in @("scripts","workflows")) {
  $src = Join-Path $SpecifySrc $d
  if (Test-Path $src) {
    $dd = Join-Path $Dst $d
    if (Test-Path $dd) { Remove-Item -Recurse -Force $dd }
    Copy-Item -Recurse $src $dd
  }
}
Write-Host "  ✔ scripts/ · workflows/ 갱신"

# templates/*.md 코어만 (overrides/ 보존)
$tdst = Join-Path $Dst "templates"; New-Item -ItemType Directory -Force -Path $tdst | Out-Null
Get-ChildItem (Join-Path $SpecifySrc "templates") -Filter *.md -File | ForEach-Object {
  Copy-Item $_.FullName (Join-Path $tdst $_.Name) -Force
}
Write-Host "  ✔ templates/ 코어 갱신 (overrides/ 보존)"

# extensions/<ext>/ scripts·commands·extension.yml·config-template.yml (git-config.yml 보존)
$extSrc = Join-Path $SpecifySrc "extensions"
if (Test-Path $extSrc) {
  Get-ChildItem $extSrc -Directory | ForEach-Object {
    $ext = $_.Name; $de = Join-Path (Join-Path $Dst "extensions") $ext
    New-Item -ItemType Directory -Force -Path $de | Out-Null
    foreach ($sub in @("scripts","commands")) {
      $s = Join-Path $_.FullName $sub
      if (Test-Path $s) { $dsub = Join-Path $de $sub; if (Test-Path $dsub) { Remove-Item -Recurse -Force $dsub }; Copy-Item -Recurse $s $dsub }
    }
    foreach ($f in @("extension.yml","config-template.yml","README.md")) {
      $sf = Join-Path $_.FullName $f
      if (Test-Path $sf) { Copy-Item $sf (Join-Path $de $f) -Force }
    }
  }
  Write-Host "  ✔ extensions/ 메커니즘 갱신 (git-config.yml 보존)"
}
Write-Host "✔ 재동기화 완료. git hook 변경 시 install-git-hooks.ps1 재실행 권장."
