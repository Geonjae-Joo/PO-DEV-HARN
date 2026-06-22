#!/usr/bin/env python3
"""
pack-to-spec.py — spec-pack.yaml + screen model → spec.md 초안 생성 (G2 브리지)

목적(why):
  /speckit-specify 의 "model_repo/specs/PACK-*/spec-pack.yaml 에서 파생하라"는 지시를 산문이 아니라
  기계 단계로 만든다. 이 스크립트가 spec-template.md 슬롯을 채운 spec.md "초안"을 만들고,
  /speckit-specify 는 그 초안을 검토·범위확정·sub-pack 분할만 한다(새 SCR-/REQ- 발명 금지).

권위 경계(boundary):
  - pack = 묶음 + ref(scope·screens·entities·journeys). 내용 권위는 screen model(SCR-*.yaml)·ENT-/JRN-.
  - 따라서 acceptance/notes 본문은 screen model 에서 끌어온다. pack 에 actions[].acceptance(Gherkin)가
    있으면 그 원문을 우선 사용한다.
  - screen model 이 Gherkin 을 갖지 않으면 user_story+validation+error_behavior 로 G/W/T "파생 초안"을
    만들고 명시적으로 표시한다(검토·정식화는 /speckit-clarify). 권위를 날조하지 않는다.

사용:
  python pack-to-spec.py PACK-TODO                 # 프로젝트 루트(자동 탐지)에서 stdout 출력
  python pack-to-spec.py PACK-TODO --feature-dir specs/001-todo-list   # spec.md 파일로 작성
  python pack-to-spec.py path/to/spec-pack.yaml --project-root /path/to/project

종료코드: 0 = 생성, 1 = 입력 오류
"""

from __future__ import annotations  # Path | None 등 PEP604 표기를 3.9 에서도 안전하게

import argparse
import datetime as _dt
import sys
from pathlib import Path

import yaml

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


def load_yaml(fp: Path):
    if not fp.exists():
        return None
    try:
        return yaml.safe_load(fp.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"[pack-to-spec] WARN: {fp} 파싱 실패 — {e}", file=sys.stderr)
        return None


def find_project_root(start: Path) -> Path | None:
    """model_repo/ 를 가진 가장 가까운 상위 디렉터리를 프로젝트 루트로 본다."""
    for anc in [start, *start.parents]:
        if (anc / "model_repo").is_dir():
            return anc
    return None


def as_id(item):
    """문자열이면 그대로, dict면 'id' 키. (스키마 단순/풍부형 모두 수용)"""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("id")
    return None


def resolve_pack(arg: str, project_root: Path | None):
    """PACK-ID 또는 spec-pack.yaml 경로를 (pack_path, project_root) 로 해석."""
    p = Path(arg)
    if p.suffix in (".yaml", ".yml") and p.exists():
        root = project_root or find_project_root(p.resolve().parent)
        return p, root
    # PACK-ID 형태
    root = project_root or find_project_root(Path.cwd())
    if root is None:
        return None, None
    return root / "model_repo" / "specs" / arg / "spec-pack.yaml", root


def collect_screen(root: Path, scr_id: str):
    doc = load_yaml(root / "model_repo" / "screens" / f"{scr_id}.yaml")
    return doc if isinstance(doc, dict) else {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pack", help="PACK-ID 또는 spec-pack.yaml 경로")
    ap.add_argument("--project-root", default=None)
    ap.add_argument("--feature-dir", default=None, help="지정 시 <dir>/spec.md 로 작성")
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve() if args.project_root else None
    pack_path, root = resolve_pack(args.pack, project_root)
    if pack_path is None or root is None:
        print("[pack-to-spec] ERROR: 프로젝트 루트(model_repo 보유)를 찾지 못했습니다. "
              "--project-root 로 지정하세요.", file=sys.stderr)
        return 1
    pack = load_yaml(pack_path)
    if not isinstance(pack, dict):
        print(f"[pack-to-spec] ERROR: 팩을 읽을 수 없습니다: {pack_path}", file=sys.stderr)
        return 1

    pack_id = pack.get("id") or pack.get("meta", {}).get("id") or pack_path.parent.name
    desc = pack.get("description") or pack.get("meta", {}).get("title") or ""
    today = _dt.date.today().isoformat()

    screens = [as_id(s) for s in (pack.get("screens") or []) if as_id(s)]
    req_ids = [as_id(r) for r in (pack.get("requirements") or pack.get("scope", {}).get("reqs") or []) if as_id(r)]
    ent_ids = [as_id(e) for e in (pack.get("entities") or []) if as_id(e)]
    jrn_ids = [as_id(j) for j in (pack.get("journeys") or []) if as_id(j)]

    # 화면 모델 로드 + CMP/REQ 상세 수집
    screen_docs = {sid: collect_screen(root, sid) for sid in screens}
    cmp_ids = []
    for sdoc in screen_docs.values():
        for c in (sdoc.get("components") or []):
            cid = as_id(c)
            if cid:
                cmp_ids.append(cid)

    out = []
    w = out.append

    w(f"# Feature Specification: {pack_id} — {desc}")
    w("")
    w(f"**Spec Pack**: `{pack_id}` (② 발행)  ")
    w("**Feature Branch**: `[###-pack-name]`  ")
    w(f"**Created**: {today}  ")
    w("**Status**: Draft (pack-to-spec 자동 초안 — /speckit-specify 검토 필요)  ")
    w(f"**Input**: `{pack_path.as_posix()}`")
    w("")
    w("<!-- 이 초안은 pack-to-spec.py 가 spec-pack + screen model 에서 파생했다. "
      "새 SCR-/REQ- 발명 금지. acceptance 의 '파생 초안' 표시는 /speckit-clarify 에서 정식화한다. -->")
    w("")

    # ── Pack Scope ──
    w("## Pack Scope *(mandatory)*")
    w("")
    w(f"- **Screens (SCR-)**: {', '.join(screens) if screens else '[없음]'}")
    w(f"- **Components (CMP-)**: {', '.join(cmp_ids) if cmp_ids else '[화면 모델 components 참조]'}")
    w(f"- **Requirements (REQ-)**: {', '.join(req_ids) if req_ids else '[없음]'}")
    w(f"- **Actor/Entity 경계**: {', '.join(ent_ids) if ent_ids else '[검토 필요]'}")
    w("- **Pinned contract**: 각 화면 `pinned_contract`(version·hash·git_ref) 위에서만 구현(freeze). "
      "[pack 에 pinned_contract 없으면 spec-pack-guard --write-pins 로 기록]")
    w("")

    # ── User Scenarios & Acceptance ──
    w("## User Scenarios & Acceptance *(mandatory)*")
    w("")
    for i, sid in enumerate(screens, 1):
        sdoc = screen_docs.get(sid, {})
        title = sdoc.get("title", "[화면명]")
        sdesc = sdoc.get("description", "")
        w(f"### {sid} — {title} (Priority: P{i})")
        w("")
        if sdesc:
            w(sdesc)
            w("")
        w(f"**Independent Test**: [{sid} 만으로 검증하는 방법 — 검토]")
        w("")
        w("**Acceptance Scenarios** (REQ- 추적):")
        w("")
        reqs = sdoc.get("requirements") or []
        if not reqs:
            w("- [화면 모델에 requirements 없음 — 검토 필요]")
        for r in reqs:
            rid = as_id(r) or "REQ-?"
            action = r.get("action", "") if isinstance(r, dict) else ""
            story = r.get("user_story", "") if isinstance(r, dict) else ""
            api = r.get("api", "") if isinstance(r, dict) else ""
            err = r.get("error_behavior", "") if isinstance(r, dict) else ""
            val = r.get("validation", []) if isinstance(r, dict) else []
            w(f"1. **{rid}** **Given** 사용자, **When** {action}, **Then** {story}  "
              f"_(파생 초안 — api: {api or 'n/a'})_")
            if val:
                w(f"   - 검증: {('; '.join(str(v) for v in val))}")
            if err:
                w(f"   - 실패: {err}")
        w("")
        w("---")
        w("")

    # ── Edge / Error / Empty ──
    w("### Edge / Error / Empty States")
    w("")
    any_edge = False
    for sid, sdoc in screen_docs.items():
        for r in (sdoc.get("requirements") or []):
            if isinstance(r, dict) and r.get("error_behavior"):
                w(f"- **{as_id(r)}** 실패: {r['error_behavior']}")
                any_edge = True
        for c in (sdoc.get("components") or []):
            if isinstance(c, dict) and c.get("initial_state"):
                w(f"- 초기/빈 상태 ({as_id(c)}): {c['initial_state']}")
                any_edge = True
    if not any_edge:
        w("- [error_behavior/initial_state 없음 — 검토 필요]")
    w("")

    # ── Notes (verbatim) ──
    w("## Business Rules & Notes (verbatim) *(include if present)*")
    w("")
    any_note = False
    for sid, sdoc in screen_docs.items():
        for n in (sdoc.get("notes") or []):
            nid = as_id(n) or "NOTE-?"
            body = n.get("content") or n.get("body") or "" if isinstance(n, dict) else str(n)
            cx = n.get("complexity", "") if isinstance(n, dict) else ""
            cx_s = f", complexity: {cx}" if cx else ""
            w(f'- **{nid}** (scope: {sid}{cx_s}): "{body}"')
            if cx == "high":
                w("  - `complexity: high` → /speckit-plan 에서 bl-analyst 가 정규화(구현 전).")
            any_note = True
    if not any_note:
        w("- [notes 없음]")
    w("")

    # ── Data Contracts ──
    w("## Data Contracts (ENT-/EXT-) *(include if present)*")
    w("")
    if ent_ids:
        for eid in ent_ids:
            edoc = load_yaml(root / "model_repo" / "entities" / f"{eid}.yaml")
            edesc = edoc.get("description", "") if isinstance(edoc, dict) else ""
            w(f"- **{eid}** (`model_repo/entities/{eid}.yaml`): {edesc}")
    else:
        w("- [entities 없음]")
    w("")

    # ── Journeys ──
    w("## Journeys (E2E, JRN-) *(include if present)*")
    w("")
    if jrn_ids:
        for jid in jrn_ids:
            jdoc = load_yaml(root / "model_repo" / "journeys" / f"{jid}.yaml")
            jt = jdoc.get("title", "") if isinstance(jdoc, dict) else ""
            jp = jdoc.get("priority", "") if isinstance(jdoc, dict) else ""
            steps = jdoc.get("steps", []) if isinstance(jdoc, dict) else []
            step_s = " → ".join(
                f"{s.get('screen','?')}/{s.get('req','-')}" for s in steps if isinstance(s, dict)
            )
            w(f"- **{jid}** (`model_repo/journeys/{jid}.yaml`, priority: {jp}): {jt} — steps: {step_s}")
    else:
        w("- [journeys 없음]")
    w("")

    # ── Open Items ──
    w("## Open Items (deferred) *(from open_questions)*")
    w("")
    any_open = False
    for sid, sdoc in screen_docs.items():
        for q in (sdoc.get("open_questions") or []):
            qid = as_id(q) or "Q-?"
            qq = q.get("question", "") if isinstance(q, dict) else str(q)
            w(f'- **{qid}** (target: {sid}): "{qq}"')
            any_open = True
    for q in (pack.get("open_items") or []):
        qid = as_id(q) or "Q-?"
        qq = q.get("question", "") if isinstance(q, dict) else str(q)
        w(f'- **{qid}**: "{qq}"')
        any_open = True
    if not any_open:
        w("- [open_items 없음]")
    w("")

    # ── Clarifications / Success / Assumptions ──
    w("## Clarifications")
    w("")
    w("<!-- /speckit-clarify 가 채운다. -->")
    w("")
    w("## Success Criteria *(mandatory)*")
    w("")
    w("- **SC-001**: 모든 REQ- acceptance 가 2계층 테스트(API+화면) green")
    w("- **SC-002**: decision table row / state 전이 테스트 커버 100%")
    w("")
    w("## Assumptions")
    w("")
    w("- 프레임워크·테스트 스택: ①의 `tech-stack.md` 핀(`/speckit-constitution`). 임의 변경 금지.")
    w("- 이 팩은 Gate A(confirmed) 계약만 포함. scope 밖 요구는 Change Order.")
    w("")

    text = "\n".join(out)

    if args.feature_dir:
        fdir = Path(args.feature_dir)
        if not fdir.is_absolute():
            fdir = Path.cwd() / fdir
        fdir.mkdir(parents=True, exist_ok=True)
        spec_file = fdir / "spec.md"
        spec_file.write_text(text, encoding="utf-8")
        print(f"[pack-to-spec] 작성 완료: {spec_file}", file=sys.stderr)
    else:
        print(text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
