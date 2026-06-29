#!/usr/bin/env python3
"""harness-core/lib/ds_closure.py

DS 폐쇄(closure) 검증 공용 라이브러리 — 전 런타임 공유의 단일 출처.
- ① plugin-prerequisite: design-page-lint.py
- ② po-define: screen model L1 validator (구 on-save-lint-L1-L4.py)
- ③ plugin-ai-web-dev: code-reviewer 참조

ds-allowlist.md 파싱 + 허용 컴포넌트/슬롯/props 검사 로직을 한 곳에 둔다.
(이전에는 design-page-lint.py와 on-save-lint-L1-L4.py에 중복돼 있었다.)

props 파싱 주의: ds-allowlist.md의 props는 "label: string, variant: a|b" 형식이므로
검증 비교용으로는 ':' 앞 토큰(키)만 추출한다. (전체 'key: type' 문자열을 저장하면
화면모델 props 키와 절대 매칭되지 않아 오탐이 발생한다.)
"""

import re
from pathlib import Path


def load_allowed_components(guide_path) -> dict:
    """ds-allowlist.md → {ComponentName: {"props": [propKeys], "slots": [slotNames]}}"""
    p = Path(guide_path)
    if not p.exists():
        return {}
    text = p.read_text(encoding="utf-8")
    allowed: dict = {}
    current = None
    props: list = []
    slots: list = []
    for line in text.splitlines():
        m = re.match(r"^##\s+(\w+)", line)
        if m:
            if current:
                allowed[current] = {"props": props, "slots": slots}
            current, props, slots = m.group(1), [], []
            continue
        if current:
            pm = re.match(r"-\s+\*?\*?props?\*?\*?:\s*(.+)", line, re.IGNORECASE)
            if pm:
                for seg in pm.group(1).split(","):
                    name = seg.split(":")[0].strip()
                    if name:
                        props.append(name)
            sm = re.match(r"-\s+\*?\*?slots?\*?\*?:\s*(.+)", line, re.IGNORECASE)
            if sm:
                slots.extend(s.strip() for s in sm.group(1).split(",") if s.strip())
    if current:
        allowed[current] = {"props": props, "slots": slots}
    return allowed


def allowed_names(guide_path) -> set:
    """허용 컴포넌트 이름 집합."""
    return set(load_allowed_components(guide_path).keys())


def is_allowed(ref: str, allowed) -> bool:
    """ref가 허용 집합 안에 있는지. allowed는 dict 또는 name set 모두 허용."""
    return ref in allowed
