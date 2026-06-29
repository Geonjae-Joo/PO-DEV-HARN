#!/usr/bin/env python3
"""
Script: sufficiency-check.py
트리거: Stage 4 진입 시 (sufficiency-check skill이 직접 호출)
목적:  spec-readiness-checklist.md의 기계 검사 부분 수행
       결과를 JSON으로 stdout에 출력 → sufficiency-check skill이 받아서 AI gap 분석 이어받음
종료코드: 0 = pass (warn 있어도), 1 = error 항목 존재 시
"""

import sys
import yaml
import json
from pathlib import Path

# Windows 콘솔(cp949 등) 유니코드 출력 크래시 방지
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

# 결과 버킷
RESULTS = {
    "error":    [],   # Gate A 차단
    "warn":     [],   # open_question 생성
    "pass":     [],   # 정상
}

# navigate target 실존 검증용 — main()에서 model_repo 전체 SCR id 로드
KNOWN_SCREENS: set = set()

def error(item_id: str, msg: str, target: str = "screen"):
    RESULTS["error"].append({"id": item_id, "msg": msg, "target": target})

def warning(item_id: str, msg: str, target: str = "screen"):
    RESULTS["warn"].append({"id": item_id, "msg": msg, "target": target})

def passed(item_id: str, msg: str):
    RESULTS["pass"].append({"id": item_id, "msg": msg})


def _cmp_ref(item: dict) -> str:
    """layout item의 DS 컴포넌트 ref 반환 (source.ref). null-안전."""
    return ((item.get("source") or {}).get("ref") or "").lower()


# ── 컴포넌트 레벨 체크 ────────────────────────────────────────────────────────

def _has_validation_signal(cid: str, action: dict, notes: list) -> bool:
    """입력 컴포넌트의 validation 규칙 존재 신호 탐지."""
    if action and action.get("type") == "validation":
        return True
    kws = ("검증", "validation", "필수", "required", "형식", "valid", "정규식", "regex", "최대", "최소")
    for n in (notes or []):
        if n.get("scope") in (cid, "screen"):
            if any(kw in str(n.get("body", "")).lower() for kw in kws):
                return True
    return False


def check_component_level(layout: list, actions: list, notes: list, screen_id: str, screen_permission: str):
    action_map = {a.get("component"): a for a in (actions or [])}

    for item in (layout or []):
        cid      = item.get("id", "unknown")
        ref      = _cmp_ref(item)
        meta     = item.get("meta", {})
        is_interactive = meta.get("interactive", False)

        if is_interactive:
            if cid not in action_map:
                error(f"CHK-CMP-ACTION-{cid}", f"{cid}: interactive인데 action 없음", cid)
            else:
                action = action_map[cid]
                passed(f"CHK-CMP-ACTION-{cid}", f"{cid}: action 존재")

                # [ERROR] acceptance 없음
                if not action.get("acceptance"):
                    error(f"CHK-CMP-ACC-{cid}", f"{cid}: acceptance 없음", cid)
                else:
                    passed(f"CHK-CMP-ACC-{cid}", f"{cid}: acceptance 존재")

                # (outcome_target / data_source 검증은 check_action_level에서 일괄 처리)
                outcome = action.get("outcome", {})

                # [WARN] permission 미정의
                if "permission" not in action:
                    warning(f"CHK-CMP-PERM-{cid}", f"{cid}: action.permission 없음 (기본 all 적용)", cid)

                # [ERROR] error_behavior 없음 (mutate/export/query)
                ot = (outcome if isinstance(outcome, dict) else {}).get("type")
                if ot in ("mutate", "export", "query"):
                    if not action.get("error_behavior"):
                        error(
                            f"CHK-ACT-ERR-{cid}",
                            f"{cid}: outcome.type={ot}인데 error_behavior 미정의 (network_fail/permission_denied 케이스 필요)",
                            cid,
                        )
                    else:
                        passed(f"CHK-ACT-ERR-{cid}", f"{cid}: error_behavior 정의됨")

                # [ERROR] action.permission이 screen.permission보다 더 넓음
                action_perm = action.get("permission", "all")
                if screen_permission and screen_permission != "all" and action_perm == "all":
                    error(
                        f"CHK-ACT-PERM-CONSISTENCY-{cid}",
                        f"{cid}: screen.permission={screen_permission}인데 action.permission=all (역할 체계 붕괴)",
                        cid,
                    )

                # [WARN] permission 제한이 있는데 permission_denied UX 없음
                if action_perm != "all":
                    eb = action.get("error_behavior", {})
                    if isinstance(eb, dict) and "permission_denied" not in eb:
                        warning(
                            f"CHK-ACT-PERM-DENIED-UX-{cid}",
                            f"{cid}: action.permission={action_perm}인데 error_behavior.permission_denied 미정의",
                            cid,
                        )

        # [ERROR] 입력(form 계열) CMP인데 validation 규칙 미정의
        if any(kw in ref for kw in ("input", "form", "select", "datepicker", "textfield")):
            if not _has_validation_signal(cid, action_map.get(cid), notes):
                error(
                    f"CHK-CMP-VALID-{cid}",
                    f"{cid}: 입력(form 계열) 컴포넌트인데 validation 규칙 미정의 (필수/형식/범위 등)",
                    cid,
                )
            else:
                passed(f"CHK-CMP-VALID-{cid}", f"{cid}: validation 규칙 확인됨")


# ── 화면 레벨 체크 ────────────────────────────────────────────────────────────

def check_screen_level(doc: dict, screen_id: str):
    screen  = doc.get("screen", {})   # ← 최상위 키는 "screen" (이전: "meta")
    layout  = doc.get("layout", [])
    actions = doc.get("actions", [])
    notes   = doc.get("notes", [])

    # ── 화면 진입 경로 ──
    has_entry = any(
        "entry" in str(n.get("body", "")).lower() or "진입" in str(n.get("body", ""))
        for n in notes
    ) or any(
        a.get("outcome", {}).get("type") == "navigate" and
        a.get("outcome", {}).get("target") == screen_id
        for a in actions
    )
    if not has_entry:
        warning("CHK-SCR-ENTRY",
                f"{screen_id}: 화면 진입 경로가 명확하지 않음 (note 또는 navigate action 확인)", "screen")
    else:
        passed("CHK-SCR-ENTRY", f"{screen_id}: 진입 경로 확인됨")

    # ── 화면 접근 권한 ──
    screen_permission = screen.get("permission")   # "all" | role-string | None
    if not screen_permission:
        warning("CHK-SCR-PERM", f"{screen_id}: screen.permission 미정의", "screen")
    else:
        passed("CHK-SCR-PERM", f"{screen_id}: screen.permission={screen_permission}")

    # ── initial_state (list/table 있을 때 필수) ──
    has_list_cmp = any(
        any(kw in _cmp_ref(item) for kw in ("table", "list", "grid", "datatable"))
        for item in layout
    )
    if has_list_cmp:
        if not screen.get("initial_state"):
            error(
                "CHK-SCR-INIT",
                f"{screen_id}: list/table 컴포넌트가 있는데 screen.initial_state 미정의 (auto_query, default_filter 등)",
                "screen",
            )
        else:
            passed("CHK-SCR-INIT", f"{screen_id}: screen.initial_state 정의됨")

    # ── reactive (FilterBar + DataTable 함께 있는데 reactive 없음) ──
    has_filter = any(
        any(kw in _cmp_ref(item) for kw in ("filterbar", "filter", "searchbar"))
        for item in layout
    )
    if has_list_cmp and has_filter:
        table_items = [
            item for item in layout
            if any(kw in _cmp_ref(item) for kw in ("table", "list", "grid", "datatable"))
        ]
        missing_reactive = [
            item.get("id", "?") for item in table_items
            if not item.get("reactive")
        ]
        if missing_reactive:
            warning(
                "CHK-SCR-REACTIVE",
                f"{screen_id}: FilterBar + Table 구성인데 reactive 미정의 → {missing_reactive}",
                "screen",
            )
        else:
            passed("CHK-SCR-REACTIVE", f"{screen_id}: reactive 정의됨")

    # ── NFR note 있는데 nfr_detail 없음 ──
    nfr_notes = [n for n in notes if n.get("kind") == "nfr"]
    if not nfr_notes:
        warning("CHK-SCR-NFR",
                f"{screen_id}: NFR note가 없음 — 성능·가용성 요구사항 확인 필요", "screen")
    else:
        for n in nfr_notes:
            nid = n.get("id", "?")
            if not n.get("nfr_detail"):
                warning(
                    f"CHK-NOTE-NFR-DETAIL-{nid}",
                    f"{nid}: kind=nfr인데 nfr_detail 없음 (동시접속자수/응답목표/우선순위 미수집)",
                    nid,
                )
            else:
                passed(f"CHK-NOTE-NFR-DETAIL-{nid}", f"{nid}: nfr_detail 정의됨")

    # ── Empty state ──
    if has_list_cmp:
        has_empty = any(
            "empty" in str(n.get("body", "")).lower() or
            "빈" in str(n.get("body", "")) or
            "0건" in str(n.get("body", "")) or
            "결과 없" in str(n.get("body", ""))
            for n in notes
        )
        if not has_empty:
            warning("CHK-SCR-EMPTY",
                    f"{screen_id}: 목록/테이블이 있는데 empty state 처리 미정의", "screen")

    # ── 비동기 action loading state ──
    async_actions = [
        a for a in actions
        if a.get("outcome", {}).get("type") in ("query", "mutate", "export")
    ]
    if async_actions:
        has_loading = any(
            "loading" in str(n.get("body", "")).lower() or
            "로딩" in str(n.get("body", "")) or
            "진행" in str(n.get("body", ""))
            for n in notes
        )
        if not has_loading:
            warning("CHK-SCR-LOADING",
                    f"{screen_id}: 비동기 action({len(async_actions)}개)이 있는데 loading 상태 처리 미정의",
                    "screen")

    return screen_permission  # 컴포넌트 레벨 교차 체크에 전달


# ── action 레벨 체크 ──────────────────────────────────────────────────────────

def check_action_level(actions: list, screen_id: str):
    for action in (actions or []):
        aid    = action.get("id", "unknown")
        status = action.get("status")

        # [ERROR] user_confirmed 아닌 action
        if status != "user_confirmed":
            error(f"CHK-ACT-CONFIRM-{aid}",
                  f"{aid}: status=user_confirmed 아님 (현재: {status})", aid)
        else:
            passed(f"CHK-ACT-CONFIRM-{aid}", f"{aid}: user_confirmed ✓")

        # [ERROR] acceptance 없음
        if not action.get("acceptance"):
            error(f"CHK-ACT-ACC-{aid}", f"{aid}: acceptance 없음", aid)

        # outcome_target / data_source
        outcome = action.get("outcome", {})
        if isinstance(outcome, dict):
            ot  = outcome.get("type")
            tgt = outcome.get("target")
            # [ERROR] outcome_target: navigate/mutate/export는 대상이 명확해야 함
            if ot in ("navigate", "mutate", "export") and not tgt:
                error(f"CHK-ACT-TARGET-{aid}",
                      f"{aid}: outcome.type={ot}인데 target 없음 (대상 SCR-/ENT-/EXT- 식별 필요)", aid)
            # [ERROR] data_source: query/mutate/export는 ENT-/EXT- 데이터 출처 식별 필요
            if ot in ("query", "mutate", "export"):
                if not tgt:
                    error(f"CHK-ACT-DATASOURCE-{aid}",
                          f"{aid}: outcome.type={ot}인데 데이터 출처(ENT-/EXT-) 미식별", aid)
                elif not (str(tgt).startswith("ENT-") or str(tgt).startswith("EXT-")):
                    error(f"CHK-ACT-DATASOURCE-{aid}",
                          f"{aid}: outcome.type={ot}의 target '{tgt}'이 ENT-/EXT- 형식이 아님 (데이터 출처 미식별)", aid)
                else:
                    passed(f"CHK-ACT-DATASOURCE-{aid}", f"{aid}: 데이터 출처 {tgt} 식별됨")
            # [WARN] navigate target 실존 여부
            if ot == "navigate" and tgt and not str(tgt).startswith("EXT-"):
                if KNOWN_SCREENS and tgt not in KNOWN_SCREENS:
                    warning(f"CHK-ACT-NAV-EXIST-{aid}",
                            f"{aid}: navigate target '{tgt}'이 model_repo에 없음 (미래 화면이면 무시)", aid)


# ── sufficiency 판정 ──────────────────────────────────────────────────────────

def determine_sufficiency() -> str:
    if RESULTS["error"]:
        return "fail"
    if RESULTS["warn"]:
        return "pass_with_deferred"
    return "pass"


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        targets = list(Path(".").glob("model_repo/screens/SCR-*.yaml"))
    else:
        targets = [Path(p) for p in sys.argv[1:]]

    if not targets:
        output = {"sufficiency": "pass", "results": RESULTS, "files": []}
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0)

    # navigate target 실존 검증용 — model_repo 전체 SCR id 로드
    screens_dir = targets[0].parent if targets[0].parent.name == "screens" else Path("model_repo/screens")
    for f in screens_dir.glob("SCR-*.yaml"):
        KNOWN_SCREENS.add(f.stem)

    processed = []
    for fp in targets:
        if not fp.exists():
            error("CHK-FILE", f"{fp}: 파일 없음")
            continue
        try:
            doc = yaml.safe_load(fp.read_text(encoding="utf-8"))
        except Exception as e:
            error("CHK-YAML", f"{fp.name}: YAML 파싱 실패 — {e}")
            continue

        screen_id       = doc.get("screen", {}).get("id", fp.stem)   # ← "screen" 키
        layout          = doc.get("layout", [])
        actions         = doc.get("actions", [])
        notes           = doc.get("notes", [])

        screen_permission = check_screen_level(doc, screen_id)
        check_component_level(layout, actions, notes, screen_id, screen_permission or "all")
        check_action_level(actions, screen_id)
        processed.append(screen_id)

    sufficiency = determine_sufficiency()
    output = {
        "sufficiency":  sufficiency,
        "error_count":  len(RESULTS["error"]),
        "warn_count":   len(RESULTS["warn"]),
        "pass_count":   len(RESULTS["pass"]),
        "results":      RESULTS,
        "files":        processed,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

    if RESULTS["error"]:
        print(f"\n[sufficiency] ❌ fail — error {len(RESULTS['error'])}건 (Gate A 차단)",
              file=sys.stderr)
        for e in RESULTS["error"]:
            print(f"  {e['msg']}", file=sys.stderr)
        sys.exit(1)
    if RESULTS["warn"]:
        print(f"\n[sufficiency] ⚠️  pass_with_deferred — warn {len(RESULTS['warn'])}건",
              file=sys.stderr)
    else:
        print("[sufficiency] ✅ pass", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
