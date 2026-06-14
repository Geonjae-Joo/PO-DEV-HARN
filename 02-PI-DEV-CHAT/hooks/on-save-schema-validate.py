#!/usr/bin/env python3
"""
Hook: on-save-schema-validate.py
트리거: screen model YAML 저장 시 (Claude Code pre-tool-use hook)
목적:  screen-model-schema-v2의 필수 필드·enum 유효성 검증
종료코드: 0 = pass, 1 = fail (stderr에 에러 목록)
"""

import sys
import yaml
import re
from pathlib import Path

ERRORS = []
WARNINGS = []

# ── 허용 enum 값 ──────────────────────────────────────────────────────────────
STATUS_VALUES = {"draft", "layout_confirmed", "actions_in_progress", "review", "confirmed"}
OUTCOME_TYPES = {"navigate", "query", "mutate", "export", "open", "validate"}
NOTE_KINDS    = {"business_rule", "nfr", "ux", "constraint", "assumption", "open_question"}
COMPLEXITY    = {"low", "med", "high"}
PERMISSIONS   = {"all", "admin", "manager", "viewer"}   # 프로젝트별 확장 가능
ACTION_STATUS = {"draft", "user_confirmed"}

# ── spine ID 패턴 ─────────────────────────────────────────────────────────────
SCR_RE  = re.compile(r"^SCR-[A-Z][A-Z0-9-]+$")
CMP_RE  = re.compile(r"^CMP-[A-Z][A-Z0-9-]+\.[a-zA-Z][a-zA-Z0-9_]+$")
REQ_RE  = re.compile(r"^REQ-[A-Z][A-Z0-9-]+\.\d{3}$")
NOTE_RE = re.compile(r"^NOTE-[A-Z][A-Z0-9-]+\.\d{3}$")
NFR_RE  = re.compile(r"^NFR-[A-Z][A-Z0-9-]+\.\d{3}$")
PRM_RE  = re.compile(r"^PRM-\d{3,}$")
DP_RE   = re.compile(r"^DP-[A-Z][A-Z0-9-]+$")


def err(msg: str):
    ERRORS.append(f"[ERROR] {msg}")

def warn(msg: str):
    WARNINGS.append(f"[WARN]  {msg}")


def validate_meta(meta: dict, path: str):
    if not meta:
        err(f"{path}: meta 섹션 없음")
        return
    # 필수 필드
    for field in ("id", "title", "status", "version"):
        if field not in meta:
            err(f"{path}.meta: 필수 필드 '{field}' 없음")
    # ID 패턴
    if "id" in meta and not SCR_RE.match(str(meta["id"])):
        err(f"{path}.meta.id: SCR- 패턴 불일치 (값: {meta['id']})")
    # status enum
    if "status" in meta and meta["status"] not in STATUS_VALUES:
        err(f"{path}.meta.status: 허용되지 않은 값 '{meta['status']}' (허용: {STATUS_VALUES})")
    # version 정수
    if "version" in meta and not isinstance(meta["version"], int):
        err(f"{path}.meta.version: 정수 타입 필요 (값: {meta['version']})")
    # hash 형식
    if "hash" in meta:
        h = str(meta["hash"])
        if not (h.startswith("sha256:") and len(h) == 71):
            warn(f"{path}.meta.hash: sha256:... 형식 권장 (값: {h[:20]}...)")


def validate_layout(layout: list, path: str):
    if not isinstance(layout, list):
        err(f"{path}.layout: list 타입 필요")
        return
    ids_seen = set()
    for i, item in enumerate(layout):
        loc = f"{path}.layout[{i}]"
        for field in ("id", "component", "position"):
            if field not in item:
                err(f"{loc}: 필수 필드 '{field}' 없음")
        if "id" in item:
            cmp_id = str(item["id"])
            if not CMP_RE.match(cmp_id):
                err(f"{loc}.id: CMP- 패턴 불일치 (값: {cmp_id})")
            if cmp_id in ids_seen:
                err(f"{loc}.id: 중복 CMP ID '{cmp_id}'")
            ids_seen.add(cmp_id)
        if "position" in item:
            pos = item["position"]
            if "slot" not in pos:
                err(f"{loc}.position: 'slot' 없음")
            if "order" not in pos:
                warn(f"{loc}.position: 'order' 없음 (렌더링 순서 미정)")
        if "meta" in item and "interactive" in item["meta"]:
            if not isinstance(item["meta"]["interactive"], bool):
                err(f"{loc}.meta.interactive: boolean 타입 필요")


def validate_actions(actions: list, layout: list, path: str):
    if not isinstance(actions, list):
        err(f"{path}.actions: list 타입 필요")
        return
    layout_ids = {item.get("id") for item in (layout or [])}
    ids_seen = set()
    for i, action in enumerate(actions):
        loc = f"{path}.actions[{i}]"
        for field in ("id", "component", "trigger", "behavior", "outcome", "permission"):
            if field not in action:
                err(f"{loc}: 필수 필드 '{field}' 없음")
        if "id" in action:
            req_id = str(action["id"])
            if not REQ_RE.match(req_id):
                err(f"{loc}.id: REQ- 패턴 불일치 (값: {req_id})")
            if req_id in ids_seen:
                err(f"{loc}.id: 중복 REQ ID '{req_id}'")
            ids_seen.add(req_id)
        # component → layout 참조 검증
        if "component" in action and action["component"] not in layout_ids:
            err(f"{loc}.component: layout에 존재하지 않는 CMP 참조 '{action['component']}'")
        # outcome.type enum
        if "outcome" in action and isinstance(action["outcome"], dict):
            ot = action["outcome"].get("type")
            if ot and ot not in OUTCOME_TYPES:
                err(f"{loc}.outcome.type: 허용되지 않은 값 '{ot}' (허용: {OUTCOME_TYPES})")
        # permission
        if "permission" in action and action["permission"] not in PERMISSIONS:
            warn(f"{loc}.permission: 비표준 값 '{action['permission']}' — tech-stack.md의 role 목록과 일치하는지 확인")
        # acceptance
        if "acceptance" not in action or not action["acceptance"]:
            warn(f"{loc}: acceptance 없음 — Stage 2에서 추가 필요")
        # status
        if "status" in action and action["status"] not in ACTION_STATUS:
            err(f"{loc}.status: 허용되지 않은 값 '{action['status']}'")


def validate_notes(notes: list, layout: list, path: str):
    if not isinstance(notes, list):
        return
    layout_ids = {item.get("id") for item in (layout or [])} | {"screen"}
    for i, note in enumerate(notes):
        loc = f"{path}.notes[{i}]"
        for field in ("id", "body", "kind", "complexity"):
            if field not in note:
                err(f"{loc}: 필수 필드 '{field}' 없음")
        if "id" in note and not NOTE_RE.match(str(note["id"])):
            err(f"{loc}.id: NOTE- 패턴 불일치 (값: {note['id']})")
        if "kind" in note and note["kind"] not in NOTE_KINDS:
            err(f"{loc}.kind: 허용되지 않은 값 '{note['kind']}'")
        if "complexity" in note and note["complexity"] not in COMPLEXITY:
            err(f"{loc}.complexity: 허용되지 않은 값 '{note['complexity']}'")
        if "verbatim" in note and note["verbatim"] is not True:
            warn(f"{loc}.verbatim: note는 항상 verbatim:true 권장")
        if "scope" in note and note["scope"] not in layout_ids:
            warn(f"{loc}.scope: layout에 없는 scope '{note['scope']}'")


def validate_prompt_log(prompt_log: list, path: str):
    if not isinstance(prompt_log, list):
        return
    prev_id = -1
    for i, entry in enumerate(prompt_log):
        loc = f"{path}.prompt_log[{i}]"
        for field in ("id", "stage", "text", "applied_version"):
            if field not in entry:
                err(f"{loc}: 필수 필드 '{field}' 없음")
        if "id" in entry and not PRM_RE.match(str(entry["id"])):
            err(f"{loc}.id: PRM- 패턴 불일치 (값: {entry['id']})")
        if "applied_version" in entry:
            v = entry["applied_version"]
            if isinstance(v, int) and v <= prev_id:
                warn(f"{loc}: applied_version이 역순 ({v} ≤ {prev_id}) — append-only 원칙 확인")
            if isinstance(v, int):
                prev_id = v


def validate_intake(intake: dict, path: str):
    if not intake:
        return
    oqs = intake.get("open_questions", [])
    if not isinstance(oqs, list):
        err(f"{path}.intake.open_questions: list 타입 필요")
        return
    for i, q in enumerate(oqs):
        loc = f"{path}.intake.open_questions[{i}]"
        for field in ("id", "ask", "status"):
            if field not in q:
                err(f"{loc}: 필수 필드 '{field}' 없음")
        if "status" in q and q["status"] == "deferred" and "defer_reason" not in q:
            err(f"{loc}: status=deferred인데 defer_reason 없음")


def validate_file(file_path: Path):
    text = file_path.read_text(encoding="utf-8")
    # raw HTML 감지
    if re.search(r"<(div|span|table|button|input|form)\s", text, re.IGNORECASE):
        err(f"{file_path.name}: raw HTML 감지 — screen model에 HTML 직접 작성 금지")
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as e:
        err(f"{file_path.name}: YAML 파싱 실패 — {e}")
        return
    if not isinstance(doc, dict):
        err(f"{file_path.name}: 최상위 구조가 dict가 아님")
        return
    p = file_path.stem
    meta   = doc.get("meta", {})
    layout = doc.get("layout", [])
    validate_meta(meta, p)
    validate_layout(layout, p)
    validate_actions(doc.get("actions", []), layout, p)
    validate_notes(doc.get("notes", []), layout, p)
    validate_prompt_log(doc.get("prompt_log", []), p)
    validate_intake(doc.get("intake", {}), p)


def main():
    if len(sys.argv) < 2:
        # Claude Code가 파일 경로를 stdin JSON으로 줄 수도 있으므로 glob 대안
        targets = list(Path(".").glob("model_repo/screens/SCR-*.yaml"))
    else:
        targets = [Path(p) for p in sys.argv[1:]]

    if not targets:
        print("[schema-validate] 검증할 파일 없음", file=sys.stderr)
        sys.exit(0)

    for fp in targets:
        if not fp.exists():
            err(f"{fp}: 파일 없음")
            continue
        validate_file(fp)

    for w in WARNINGS:
        print(w, file=sys.stderr)
    if ERRORS:
        for e in ERRORS:
            print(e, file=sys.stderr)
        print(f"\n[schema-validate] ❌ {len(ERRORS)} error(s) — 저장 차단", file=sys.stderr)
        sys.exit(1)
    print(f"[schema-validate] ✅ pass ({len(targets)} file(s), {len(WARNINGS)} warning(s))")
    sys.exit(0)


if __name__ == "__main__":
    main()
