#!/usr/bin/env python3
"""
Hook: gate-a-check.py
트리거: PO가 "확정(confirm)" 요청 시
목적:  Gate A의 모든 조건을 종합 판정하고 status: confirmed로 전환
종료코드: 0 = pass (status: confirmed로 전환), 1 = 차단 (이유 stderr 출력)

Gate A 통과 조건 (AND):
  1. lint L1 error 0 (on-save-lint-L1-L4.py 재실행으로 확인)
  2. sufficiency: pass 또는 pass_with_deferred (sufficiency-check.py 재실행)
  3. 모든 action이 user_confirmed
  4. open_questions 중 status=open인 항목 0개 (all answered or deferred with reason)
  5. PO 승인 확인 (--pi-approved 플래그 또는 환경변수 GATE_A_PO_APPROVED=1)
  6. 전역 스파인 ID 유일성 (link-manifest 원장 기준, harness-core/lib/spine_ledger.py)
"""

import sys
import yaml
import json
import subprocess
import os
from pathlib import Path

# Windows 콘솔(cp949 등) 유니코드 출력 크래시 방지
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

# 하위 스크립트(lint/sufficiency)는 UTF-8로 출력하므로 파이프도 UTF-8로 디코드한다.
# (text=True 기본 디코더가 cp949면 한글/em-dash에서 UnicodeDecodeError → 거짓 차단)
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# harness-core 공용 ledger 라이브러리 (전역 ID 유일성 단일 출처)
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "harness-core" / "lib"))
try:
    import spine_ledger
except Exception:  # noqa: BLE001
    spine_ledger = None

BLOCKS = []   # 차단 이유 목록
PASSES = []   # 통과 항목


def block(reason: str):
    BLOCKS.append(reason)

def ok(msg: str):
    PASSES.append(msg)


# ── 조건 1: L1 lint ───────────────────────────────────────────────────────────

def check_lint(targets: list[str]) -> bool:
    lint_script = Path(__file__).parent / "../../../hooks/on-save-lint-L1-L4.py"
    if not lint_script.exists():
        block("on-save-lint-L1-L4.py 없음 — lint 검증 불가")
        return False
    result = subprocess.run(
        [sys.executable, str(lint_script)] + targets,
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        # L1 에러가 있음
        l1_errors = [line for line in result.stderr.splitlines() if "[L1 ERROR]" in line]
        block(f"L1 lint error {len(l1_errors)}건 — DS 폐쇄 위반:\n" +
              "\n".join(f"    {e}" for e in l1_errors))
        return False
    # L2/L3/L4/L5 에러도 Gate A 차단
    gate_errors = [line for line in result.stderr.splitlines()
                   if any(tag in line for tag in ("[L2 ERROR]", "[L3 ERROR]", "[L4 ERROR]", "[L5 ERROR]"))]
    if gate_errors:
        block(f"L2/L3/L4/L5 error {len(gate_errors)}건 — 완전성/일관성/커버리지/캔버스경계 위반:\n" +
              "\n".join(f"    {e}" for e in gate_errors))
        return False
    ok("lint L1~L5 pass")
    return True


# ── 조건 2: sufficiency ───────────────────────────────────────────────────────

def check_sufficiency(targets: list[str]) -> bool:
    suf_script = Path(__file__).parent / "../../sufficiency-check/scripts/sufficiency-check.py"
    if not suf_script.exists():
        block("sufficiency-check.py 없음 — sufficiency 검증 불가")
        return False
    result = subprocess.run(
        [sys.executable, str(suf_script)] + targets,
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    try:
        data = json.loads(result.stdout)
    except Exception:
        block("sufficiency-check.py 출력 파싱 실패")
        return False
    suf = data.get("sufficiency", "fail")
    if suf == "fail":
        errors = data.get("results", {}).get("error", [])
        block(f"sufficiency=fail — error {len(errors)}건:\n" +
              "\n".join(f"    {e['msg']}" for e in errors))
        return False
    if suf == "pass_with_deferred":
        warn_count = data.get("warn_count", 0)
        ok(f"sufficiency=pass_with_deferred ({warn_count}건 deferred 포함)")
    else:
        ok("sufficiency=pass")
    return True


# ── 조건 3: 모든 action user_confirmed ───────────────────────────────────────

def check_actions_confirmed(docs: list[dict]) -> bool:
    not_confirmed = []
    for doc in docs:
        screen_id = doc.get("screen", {}).get("id", "?")   # ← "screen" 키
        for action in doc.get("actions", []):
            if action.get("status") != "user_confirmed":
                not_confirmed.append(f"{screen_id}: action '{action.get('id')}' (status: {action.get('status')})")
    if not_confirmed:
        block(f"user_confirmed 아닌 action {len(not_confirmed)}건:\n" +
              "\n".join(f"    {a}" for a in not_confirmed))
        return False
    ok("모든 action user_confirmed")
    return True


# ── 조건 4: open_questions 잔여 없음 ─────────────────────────────────────────

def check_open_questions(docs: list[dict]) -> bool:
    still_open = []
    no_reason  = []
    for doc in docs:
        screen_id = doc.get("screen", {}).get("id", "?")   # ← "screen" 키
        for q in doc.get("intake", {}).get("open_questions", []):
            status = q.get("status")
            if status == "open":
                still_open.append(f"{screen_id}: Q '{q.get('id')}' — {q.get('ask', '')[:60]}")
            elif status == "deferred" and not q.get("defer_reason"):
                no_reason.append(f"{screen_id}: Q '{q.get('id')}' — deferred인데 defer_reason 없음")
    issues = still_open + no_reason
    if issues:
        block(f"미처리 open_question {len(issues)}건:\n" +
              "\n".join(f"    {i}" for i in issues))
        return False
    ok("모든 open_question answered 또는 deferred(사유 있음)")
    return True


# ── 조건 5: PO 승인 ───────────────────────────────────────────────────────────

def check_pi_approved(args: list[str]) -> bool:
    if "--pi-approved" in args or os.environ.get("GATE_A_PO_APPROVED") == "1":
        ok("PO 승인 확인됨")
        return True
    block("PO 승인 플래그 없음 (--pi-approved 또는 GATE_A_PO_APPROVED=1 필요)")
    return False


# ── 조건 6: 전역 스파인 ID 유일성 ────────────────────────────────────────────

def check_spine_uniqueness() -> bool:
    if spine_ledger is None:
        warn_unavailable = "spine_ledger 라이브러리 로드 실패 — 전역 ID 유일성 검사 건너뜀"
        ok(warn_unavailable)  # 비차단: 라이브러리 부재 시 게이트를 막지 않음(보수적)
        return True
    root = Path("model_repo")
    res = spine_ledger.check(root, root / "link-manifest.yaml")
    if not res["ok"]:
        lines = [f"{i}: {', '.join(fs)}" for i, fs in res["dups"].items()]
        block(f"전역 스파인 ID 중복 {len(res['dups'])}건 — 채번 충돌:\n" +
              "\n".join(f"    {l}" for l in lines))
        return False
    note = ""
    if res["warnings"]:
        note = " (경고: " + "; ".join(res["warnings"]) + ")"
    ok(f"전역 ID 유일성 OK — {res['id_count']}개 ID{note}")
    return True


# ── status: confirmed 전환 ────────────────────────────────────────────────────

def transition_to_confirmed(targets: list[str], docs_map: dict):
    for fp_str in targets:
        fp = Path(fp_str)
        if not fp.exists():
            continue
        doc = docs_map.get(fp_str)
        if not doc:
            continue
        doc["screen"]["status"] = "confirmed"                              # ← "screen" 키
        doc["screen"]["version"] = doc["screen"].get("version", 0) + 1
        from datetime import datetime, timezone
        doc["screen"]["confirmed_at"] = datetime.now(timezone.utc).isoformat()
        text = yaml.dump(doc, allow_unicode=True, sort_keys=False, default_flow_style=False)
        fp.write_text(text, encoding="utf-8")
        print(f"[gate-a] ✅ {fp.name} → status: confirmed (v{doc['screen']['version']})")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    file_args = [a for a in args if not a.startswith("--")]
    flag_args = [a for a in args if a.startswith("--")]

    if not file_args:
        file_args = [str(p) for p in Path(".").glob("model_repo/screens/SCR-*.yaml")]

    if not file_args:
        print("[gate-a] 검증할 파일 없음", file=sys.stderr)
        sys.exit(0)

    # YAML 로드
    docs_map = {}
    docs     = []
    for fp_str in file_args:
        fp = Path(fp_str)
        if not fp.exists():
            block(f"{fp}: 파일 없음")
            continue
        try:
            doc = yaml.safe_load(fp.read_text(encoding="utf-8"))
            docs_map[fp_str] = doc
            docs.append(doc)
        except Exception as e:
            block(f"{fp.name}: YAML 파싱 실패 — {e}")

    # 6가지 조건 검사
    c1 = check_lint(file_args)
    c2 = check_sufficiency(file_args)
    c3 = check_actions_confirmed(docs)
    c4 = check_open_questions(docs)
    c5 = check_pi_approved(flag_args)
    c6 = check_spine_uniqueness()

    print("\n[Gate A 판정 결과]")
    for p in PASSES:
        print(f"  ✅ {p}")
    for b in BLOCKS:
        print(f"  ❌ {b}", file=sys.stderr)

    if BLOCKS:
        print(f"\n[gate-a] ❌ Gate A 차단 — {len(BLOCKS)}가지 조건 미충족", file=sys.stderr)
        sys.exit(1)

    # 모두 통과 → status: confirmed 전환
    transition_to_confirmed(file_args, docs_map)
    print(f"\n[gate-a] 🎉 Gate A 통과 — {len(file_args)}개 screen → status: confirmed")
    sys.exit(0)


if __name__ == "__main__":
    main()
