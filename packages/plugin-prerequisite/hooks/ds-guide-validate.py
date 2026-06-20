#!/usr/bin/env python3
"""
ds-guide-validate.py
Trigger: Claude Code PostToolUse(Write|Edit) hook — ds-allowlist.md 저장 직후.
역할: DS 컴포넌트 목록의 형식·필수 필드 검증.

호출 규약(현행 Claude Code 훅):
  - 훅 payload(JSON)가 stdin 으로 들어온다: {"tool_input": {"file_path": "...", ...}, ...}
  - settings.json 은 matcher 로 도구명(Write|Edit)만 거른다. 파일 경로 필터는 이 스크립트가 한다.
  - PostToolUse 이므로 파일은 이미 디스크에 기록됨(=새 내용 검증 가능).
종료코드: 0 = 통과/대상아님, 2 = 검증 실패(모델에 stderr 피드백, 수정 유도).
"""

import sys
import re
import json
from pathlib import Path

# Windows 콘솔(cp949 등) 유니코드 출력 크래시 방지
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

DEFAULT_GUIDE_PATH = Path("foundation/design-system/ds-allowlist.md")
ALLOWLIST_BASENAME = "ds-allowlist.md"


def resolve_target() -> Path | None:
    """검증 대상 경로 결정. 우선순위: 훅 stdin JSON > argv > 기본.
    대상이 ds-allowlist.md 가 아니면 None(검증 스킵)."""
    file_path = None
    # 1) 훅 stdin payload
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            if raw.strip():
                payload = json.loads(raw)
                file_path = (payload.get("tool_input") or {}).get("file_path")
        except Exception:
            file_path = None
    # 2) argv 폴백
    if not file_path:
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        if args:
            file_path = args[0]
    # 3) 기본
    if not file_path:
        return DEFAULT_GUIDE_PATH if DEFAULT_GUIDE_PATH.exists() else None
    p = Path(file_path)
    if p.name != ALLOWLIST_BASENAME:
        return None  # 다른 파일 저장 — 이 훅의 관심사 아님
    return p

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
    target = resolve_target()
    if target is None:
        return 0  # 대상 파일 아님 — 조용히 통과
    if not target.exists():
        ERRORS.append(f"ds-allowlist.md 파일이 없습니다: {target}")
        report()
        return 2

    text = target.read_text(encoding="utf-8")

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
    return 2 if ERRORS else 0


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
