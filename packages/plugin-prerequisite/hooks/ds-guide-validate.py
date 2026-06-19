#!/usr/bin/env python3
"""
ds-guide-validate.py
Trigger: ds-allowlist.md 저장 시
역할: DS 컴포넌트 목록의 형식·필수 필드 검증
"""

import sys
import re
from pathlib import Path

DESIGN_GUIDE_PATH = Path("foundation/design-system/ds-allowlist.md")

REQUIRED_FIELDS = ["name", "props", "description"]
OPTIONAL_FIELDS = ["usage", "variants", "slots"]

ERRORS = []
WARNINGS = []


def parse_components(text: str) -> list[dict]:
    """
    ds-allowlist.md에서 컴포넌트 블록을 파싱한다.
    예상 형식:
    ## ComponentName
    - **description**: ...
    - **props**: ...
    - **usage**: ...
    """
    components = []
    current = None
    for line in text.splitlines():
        h2 = re.match(r"^## (.+)$", line.strip())
        if h2:
            if current:
                components.append(current)
            current = {"name": h2.group(1).strip(), "_raw": []}
        elif current is not None:
            field_match = re.match(r"^[-*]\s+\*\*(\w+)\*\*:\s*(.+)$", line.strip())
            if field_match:
                current[field_match.group(1)] = field_match.group(2).strip()
            current["_raw"].append(line)
    if current:
        components.append(current)
    return components


def validate_component(cmp: dict) -> None:
    name = cmp.get("name", "UNKNOWN")
    for field in REQUIRED_FIELDS:
        if field not in cmp:
            ERRORS.append(f"[{name}] 필수 필드 누락: '{field}'")
    if "name" in cmp and not re.match(r"^[A-Z][A-Za-z0-9]+$", cmp["name"]):
        WARNINGS.append(f"[{name}] 이름이 PascalCase가 아닙니다.")
    if "props" in cmp:
        props_val = cmp["props"]
        if not props_val or props_val.strip() in ("없음", "none", "-"):
            pass  # no-prop 컴포넌트 허용
        elif not any(c in props_val for c in [":", ","]):
            WARNINGS.append(f"[{name}] props 형식을 확인하세요 (예: 'label: string, variant: primary|secondary')")


def main() -> int:
    if not DESIGN_GUIDE_PATH.exists():
        ERRORS.append(f"ds-allowlist.md 파일이 없습니다: {DESIGN_GUIDE_PATH}")
        report()
        return 1

    text = DESIGN_GUIDE_PATH.read_text(encoding="utf-8")

    if "# DS Allowlist" not in text and "# ds allowlist" not in text.lower():
        WARNINGS.append("ds-allowlist.md에 '# DS Allowlist' 헤더가 없습니다.")

    components = parse_components(text)
    if not components:
        ERRORS.append("ds-allowlist.md에서 컴포넌트 정의(## ComponentName)를 찾을 수 없습니다.")
    else:
        print(f"✓ 컴포넌트 {len(components)}개 발견: {[c['name'] for c in components]}")
        for cmp in components:
            validate_component(cmp)

    report()
    return 1 if ERRORS else 0


def report() -> None:
    for e in ERRORS:
        print(f"ERROR: {e}", file=sys.stderr)
    for w in WARNINGS:
        print(f"WARN:  {w}", file=sys.stderr)
    if not ERRORS and not WARNINGS:
        print("✓ ds-allowlist.md 검증 통과")
    elif not ERRORS:
        print(f"✓ 검증 통과 (경고 {len(WARNINGS)}개)")
    else:
        print(f"✗ 검증 실패 (오류 {len(ERRORS)}개, 경고 {len(WARNINGS)}개)")


if __name__ == "__main__":
    sys.exit(main())
