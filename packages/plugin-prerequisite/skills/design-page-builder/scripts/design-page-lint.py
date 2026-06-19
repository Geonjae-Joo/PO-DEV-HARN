#!/usr/bin/env python3
"""
design-page-lint.py
Trigger: design-pages/*.yaml 저장 시
역할: design page 템플릿의 DS 폐쇄 검증 + 스파인 ID(DP-*) 존재 확인
"""

import sys
import re
import yaml
from pathlib import Path

# ── 공용 DS 폐쇄 라이브러리 (harness-core/lib) 단일 출처 ─────────────────────────
# 시스템 모노레포에서는 packages/harness-core/lib 에 위치
# (이 스크립트: packages/plugin-prerequisite/skills/design-page-builder/scripts/).
# 런타임 레이아웃이 달라 import 실패 시 동치 로컬 구현으로 폴백한다.
_CORE_LIB = Path(__file__).resolve().parents[4] / "harness-core" / "lib"
if _CORE_LIB.exists() and str(_CORE_LIB) not in sys.path:
    sys.path.insert(0, str(_CORE_LIB))
try:
    from ds_closure import allowed_names as _core_allowed_names  # type: ignore
except Exception:
    _core_allowed_names = None

DESIGN_GUIDE_PATH = Path("foundation/design-system/ds-allowlist.md")
DESIGN_PAGES_DIR = Path("foundation/design-pages")
DP_ID_PATTERN = re.compile(r"^DP-[A-Z0-9]+(-[A-Z0-9]+)*$")

ERRORS = []
WARNINGS = []


def load_allowed_components(guide_path: Path) -> set:
    """ds-allowlist.md에서 허용된 컴포넌트 이름 집합을 추출한다.
    공용 harness-core/lib/ds_closure.py 를 단일 출처로 사용, 실패 시 동치 폴백."""
    if not guide_path.exists():
        ERRORS.append(f"ds-allowlist.md 없음: {guide_path}. ds-guide-validate.py 먼저 실행하세요.")
        return set()
    if _core_allowed_names is not None:
        return _core_allowed_names(guide_path)
    text = guide_path.read_text(encoding="utf-8")
    return {m.group(1) for m in re.finditer(r"^##\s+(\w+)", text, re.MULTILINE)}


def lint_page(page_path: Path, allowed: set[str]) -> None:
    try:
        data = yaml.safe_load(page_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        ERRORS.append(f"[{page_path.name}] YAML 파싱 오류: {e}")
        return

    # 1. 스파인 ID 확인
    dp_id = data.get("id", "")
    if not dp_id:
        ERRORS.append(f"[{page_path.name}] 'id' 필드 없음. DP-* 형식의 스파인 ID가 필요합니다.")
    elif not DP_ID_PATTERN.match(dp_id):
        ERRORS.append(f"[{page_path.name}] id='{dp_id}' — DP-* 형식이 아닙니다. (예: DP-MAIN, DP-POPUP)")

    # 2. slots 정의 확인
    slots = data.get("slots", [])
    if not slots:
        WARNINGS.append(f"[{page_path.name}] 'slots' 정의 없음. 슬롯 목록을 명시하세요.")

    # 3. 컴포넌트 DS 폐쇄 검증
    components = data.get("components", []) or data.get("layout", [])
    for cmp in components:
        ref = cmp.get("ref") or cmp.get("source", {}).get("ref", "")
        if not ref:
            continue
        if allowed and ref not in allowed:
            ERRORS.append(
                f"[{page_path.name}] DS 폐쇄 위반: '{ref}'는 ds-allowlist.md 허용 목록에 없습니다. "
                f"허용: {sorted(allowed)}"
            )

    # 4. raw HTML 직접 작성 금지
    raw_text = page_path.read_text(encoding="utf-8")
    html_tags = re.findall(r"<(?!--|!)[a-zA-Z][^>]*>", raw_text)
    if html_tags:
        ERRORS.append(
            f"[{page_path.name}] raw HTML 직접 작성 금지 (constitution 원칙 1). "
            f"발견된 태그: {html_tags[:5]}"
        )


def main() -> int:
    allowed = load_allowed_components(DESIGN_GUIDE_PATH)

    pages = list(DESIGN_PAGES_DIR.glob("*.yaml"))
    if not pages:
        WARNINGS.append(f"{DESIGN_PAGES_DIR} 에서 YAML 파일을 찾을 수 없습니다.")
    else:
        print(f"✓ design page {len(pages)}개 검사: {[p.name for p in pages]}")
        for page in pages:
            lint_page(page, allowed)

    for e in ERRORS:
        print(f"ERROR: {e}", file=sys.stderr)
    for w in WARNINGS:
        print(f"WARN:  {w}", file=sys.stderr)

    if not ERRORS:
        print(f"✓ design-page lint 통과 (경고 {len(WARNINGS)}개)")
        return 0
    else:
        print(f"✗ design-page lint 실패 (오류 {len(ERRORS)}개)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
