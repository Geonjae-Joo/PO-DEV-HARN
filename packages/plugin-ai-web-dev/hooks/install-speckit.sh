#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────────────
# PO-DEV-HARN — speckit 부트스트랩 설치기 (bash / Git Bash on Windows · Linux · macOS)
#
# 목적(why):
#   speckit 스크립트(.specify/scripts/*.sh)는 cwd 에서 위로 .specify/ 를 찾아 프로젝트 루트를
#   정한다(common.sh: find_specify_root). 플러그인의 .specify/ 는 "원본(메커니즘)"일 뿐
#   app_repo 에는 없으므로, 이 스크립트가 app_repo 루트에 .specify/ 를 vendoring 해야
#   /speckit-specify·plan·tasks 가 비로소 동작한다. (없으면 v2처럼 명령 자체가 실행 불가)
#
# 무엇을(what):
#   1) app_repo 가 git 저장소가 아니면 git init
#   2) 플러그인 .specify/ 를 app_repo/.specify/ 로 복사(기존 파일은 덮지 않음 — 멱등)
#   3) .specify/.source 에 출처(플러그인@버전·speckit 버전·일시) 기록 → 이후 speckit-sync 기준
#   4) install-git-hooks.sh 호출로 commit-msg/post-commit 훅 설치
#
# 경계(boundary):
#   - 메커니즘(scripts/templates/workflows/extensions)은 플러그인이 단일 원본. 업그레이드는 speckit-sync.sh.
#   - 상태(memory/constitution.md·feature.json·templates/overrides/)는 app_repo 소유 — 여기서 덮지 않는다.
#
# 사용:
#   app_repo 루트에서:  bash "$CLAUDE_PLUGIN_ROOT/hooks/install-speckit.sh"
#   또는 대상 지정:      bash .../install-speckit.sh /path/to/app_repo
# 환경변수: PYTHON, HARNESS_TEST_CMD (install-git-hooks.sh 로 전달)
# ────────────────────────────────────────────────────────────────────────
set -euo pipefail

HOOKS_SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${HOOKS_SRC_DIR}/.." && pwd)"
SPECIFY_SRC="${PLUGIN_ROOT}/.specify"

APP_REPO="${1:-$(pwd)}"
APP_REPO="$(cd "${APP_REPO}" && pwd)"

if [ ! -d "${SPECIFY_SRC}" ]; then
  echo "✖ 플러그인 .specify 원본을 찾을 수 없습니다: ${SPECIFY_SRC}" >&2
  exit 1
fi

echo "▶ speckit 부트스트랩"
echo "  플러그인(원본): ${SPECIFY_SRC}"
echo "  대상 app_repo : ${APP_REPO}"

# ── 1) git 저장소 보장 ───────────────────────────────────────────────────
if ! git -C "${APP_REPO}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "  git 저장소가 아니므로 git init 실행"
  git -C "${APP_REPO}" init -q
fi

# ── 2) .specify vendoring (멱등: 기존 파일은 보존) ────────────────────────
DST_SPECIFY="${APP_REPO}/.specify"
mkdir -p "${DST_SPECIFY}"
# cp -n: 이미 존재하는 파일은 덮지 않음(상태 파일 보존). 누락 메커니즘만 채움.
cp -Rn "${SPECIFY_SRC}/." "${DST_SPECIFY}/" 2>/dev/null || cp -R "${SPECIFY_SRC}/." "${DST_SPECIFY}/"
echo "  ✔ .specify vendoring 완료 (기존 파일 보존)"

# ── 3) .source 기록 (출처·버전 핀) ───────────────────────────────────────
PLUGIN_VER="$(grep -m1 '"version"' "${PLUGIN_ROOT}/plugin.json" 2>/dev/null | sed -E 's/.*"version"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/' || true)"
SPECKIT_VER="$(grep -m1 '"speckit_version"' "${SPECIFY_SRC}/init-options.json" 2>/dev/null | sed -E 's/.*"speckit_version"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/' || true)"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
cat > "${DST_SPECIFY}/.source" <<EOF
{
  "vendored_from": "plugin-ai-web-dev",
  "plugin_version": "${PLUGIN_VER:-unknown}",
  "speckit_version": "${SPECKIT_VER:-unknown}",
  "vendored_at": "${NOW}",
  "_note": "메커니즘(scripts/templates/workflows/extensions)의 단일 원본은 플러그인이다. 업그레이드는 speckit-sync.sh 로. 이 파일과 memory/constitution.md·feature.json·templates/overrides/ 는 app_repo 상태이므로 sync가 덮지 않는다."
}
EOF
echo "  ✔ .specify/.source 기록 (plugin@${PLUGIN_VER:-unknown}, speckit ${SPECKIT_VER:-unknown})"

# ── 4) git hook 설치 ─────────────────────────────────────────────────────
( cd "${APP_REPO}" && bash "${HOOKS_SRC_DIR}/install-git-hooks.sh" )

echo "✔ 부트스트랩 완료. 확인:  ( cd '${APP_REPO}' && bash .specify/scripts/bash/check-prerequisites.sh --paths-only )"
echo "  다음: /speckit-constitution → /speckit-specify PACK-<ID>"
