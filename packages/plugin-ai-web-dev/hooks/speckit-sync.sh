#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────────────
# PO-DEV-HARN — speckit 메커니즘 재동기화 (bash / Git Bash · Linux · macOS)
#
# 목적(why):
#   플러그인(메커니즘 단일 원본)이 업그레이드되면 app_repo 의 vendored .specify 가 뒤처진다(drift).
#   이 스크립트는 **메커니즘 디렉터리만** 플러그인에서 다시 덮어쓰고, app_repo 상태는 보존한다.
#
# 덮어씀(MECHANISM): scripts/ · templates/(overrides 제외) · workflows/ · extensions/<ext>/{scripts,commands,extension.yml,config-template.yml}
# 보존(STATE/CONFIG): memory/ · feature.json · templates/overrides/ · extensions/git/git-config.yml
#                     · extensions.yml · init-options.json · integration.json · .source(갱신)
#
# 사용: app_repo 루트에서  bash "$CLAUDE_PLUGIN_ROOT/hooks/speckit-sync.sh"  [/path/to/app_repo]
# ────────────────────────────────────────────────────────────────────────
set -euo pipefail

HOOKS_SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${HOOKS_SRC_DIR}/.." && pwd)"
SPECIFY_SRC="${PLUGIN_ROOT}/.specify"

APP_REPO="${1:-$(pwd)}"
APP_REPO="$(cd "${APP_REPO}" && pwd)"
DST="${APP_REPO}/.specify"

if [ ! -d "${DST}" ]; then
  echo "✖ ${DST} 가 없습니다. 먼저 install-speckit.sh 로 부트스트랩하세요." >&2
  exit 1
fi

echo "▶ speckit 메커니즘 재동기화: ${SPECIFY_SRC} → ${DST}"

# scripts/ 전체 덮어쓰기 (코어 스크립트)
rm -rf "${DST}/scripts"; cp -R "${SPECIFY_SRC}/scripts" "${DST}/scripts"
echo "  ✔ scripts/ 갱신"

# workflows/ 전체 덮어쓰기
rm -rf "${DST}/workflows"; cp -R "${SPECIFY_SRC}/workflows" "${DST}/workflows"
echo "  ✔ workflows/ 갱신"

# templates/ : *.md 코어만 덮고 overrides/ 는 보존
mkdir -p "${DST}/templates"
for f in "${SPECIFY_SRC}/templates"/*.md; do
  [ -e "$f" ] || continue
  cp "$f" "${DST}/templates/$(basename "$f")"
done
echo "  ✔ templates/ 코어 갱신 (overrides/ 보존)"

# extensions/<ext>/ : scripts·commands·extension.yml·config-template.yml 만 덮고 git-config.yml 보존
if [ -d "${SPECIFY_SRC}/extensions" ]; then
  for extdir in "${SPECIFY_SRC}/extensions"/*/; do
    [ -d "$extdir" ] || continue
    ext="$(basename "$extdir")"
    dstext="${DST}/extensions/${ext}"
    mkdir -p "$dstext"
    for sub in scripts commands; do
      if [ -d "${extdir}${sub}" ]; then
        rm -rf "${dstext}/${sub}"; cp -R "${extdir}${sub}" "${dstext}/${sub}"
      fi
    done
    for file in extension.yml config-template.yml README.md; do
      [ -f "${extdir}${file}" ] && cp "${extdir}${file}" "${dstext}/${file}"
    done
  done
  echo "  ✔ extensions/ 메커니즘 갱신 (git-config.yml 등 설정 보존)"
fi

# .source 갱신
PLUGIN_VER="$(grep -m1 '"version"' "${PLUGIN_ROOT}/plugin.json" 2>/dev/null | sed -E 's/.*"version"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/' || true)"
SPECKIT_VER="$(grep -m1 '"speckit_version"' "${SPECIFY_SRC}/init-options.json" 2>/dev/null | sed -E 's/.*"speckit_version"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/' || true)"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
cat > "${DST}/.source" <<EOF
{
  "vendored_from": "plugin-ai-web-dev",
  "plugin_version": "${PLUGIN_VER:-unknown}",
  "speckit_version": "${SPECKIT_VER:-unknown}",
  "synced_at": "${NOW}",
  "_note": "speckit-sync.sh 로 메커니즘만 재동기화됨. 상태(memory/feature.json/overrides/git-config) 보존."
}
EOF
echo "✔ 재동기화 완료 (plugin@${PLUGIN_VER:-unknown}). git hook 변경 시 install-git-hooks.sh 재실행 권장."
