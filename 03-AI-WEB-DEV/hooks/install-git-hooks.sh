#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────────────
# PO-DEV-HARN — git hook 설치기 (bash / Git Bash on Windows · Linux · macOS)
#
# hooks.json은 의미상 pre-commit/post-commit으로 선언돼 있으나, tdd-gate·commit-spine-id는
# 커밋 메시지 파일($1)이 필요하다([SCAFFOLD] 판정·스파인 ID 검사). git에서 메시지를 받는
# 단계는 commit-msg 이므로 둘을 commit-msg 훅으로 설치한다. manifest-sync는 post-commit.
#
# 사용: app_repo 루트(또는 강제할 git 저장소)에서
#   bash 03-AI-WEB-DEV/hooks/install-git-hooks.sh
# 환경변수:
#   PYTHON=python3            # 파이썬 실행기 지정 (기본: python → 없으면 python3)
#   HARNESS_TEST_CMD="..."    # tdd-gate가 실행할 테스트 명령(①/tech-stack.md 핀). 훅에 기록됨.
# ────────────────────────────────────────────────────────────────────────
set -euo pipefail

HOOKS_SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GIT_DIR="$(git rev-parse --git-dir 2>/dev/null || true)"
if [ -z "${GIT_DIR}" ]; then
  echo "✖ 현재 위치가 git 저장소가 아닙니다. app_repo 루트에서 실행하세요." >&2
  exit 1
fi
# 절대경로화
GIT_DIR="$(cd "${GIT_DIR}" && pwd)"
HOOK_DST="${GIT_DIR}/hooks"
mkdir -p "${HOOK_DST}"

PY="${PYTHON:-python}"
if ! command -v "${PY}" >/dev/null 2>&1; then PY=python3; fi
if ! command -v "${PY}" >/dev/null 2>&1; then
  echo "✖ python 실행기를 찾을 수 없습니다. PYTHON 환경변수로 지정하세요." >&2
  exit 1
fi

TEST_CMD_LINE=""
if [ -n "${HARNESS_TEST_CMD:-}" ]; then
  TEST_CMD_LINE="export HARNESS_TEST_CMD=$(printf '%q' "${HARNESS_TEST_CMD}")"
fi

backup() {
  local f="$1"
  if [ -f "$f" ] && ! grep -q "PO-DEV-HARN-HOOK" "$f" 2>/dev/null; then
    mv "$f" "$f.bak.$(date +%s)"
    echo "  기존 $(basename "$f") → 백업"
  fi
}

# ── commit-msg: tdd-gate → commit-spine-id (둘 다 blocking) ──────────────
backup "${HOOK_DST}/commit-msg"
cat > "${HOOK_DST}/commit-msg" <<EOF
#!/usr/bin/env bash
# PO-DEV-HARN-HOOK (commit-msg) — 자동 생성. 수정하지 말 것.
set -e
${TEST_CMD_LINE}
HOOKS_DIR="${HOOKS_SRC_DIR}"
"${PY}" "\${HOOKS_DIR}/tdd-gate.py" "\$1" || exit 1
"${PY}" "\${HOOKS_DIR}/commit-spine-id.py" "\$1" || exit 1
EOF
chmod +x "${HOOK_DST}/commit-msg"

# ── post-commit: manifest-sync (non-blocking) ───────────────────────────
backup "${HOOK_DST}/post-commit"
cat > "${HOOK_DST}/post-commit" <<EOF
#!/usr/bin/env bash
# PO-DEV-HARN-HOOK (post-commit) — 자동 생성. 수정하지 말 것.
HOOKS_DIR="${HOOKS_SRC_DIR}"
"${PY}" "\${HOOKS_DIR}/manifest-sync.py" || true
EOF
chmod +x "${HOOK_DST}/post-commit"

echo "✔ 설치 완료"
echo "  → ${HOOK_DST}/commit-msg   (tdd-gate + commit-spine-id, blocking)"
echo "  → ${HOOK_DST}/post-commit  (manifest-sync, non-blocking)"
echo "  python: ${PY}"
[ -n "${TEST_CMD_LINE}" ] && echo "  HARNESS_TEST_CMD 고정됨" || \
  echo "  HARNESS_TEST_CMD 미지정 — tdd-gate 자동 탐지 사용(①/tech-stack.md 권장)"
