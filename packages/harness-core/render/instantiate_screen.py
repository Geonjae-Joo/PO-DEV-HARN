#!/usr/bin/env python3
"""harness-core/render/instantiate_screen.py — DP → SCR 인스턴스화 (ADR-002 §6).

PO가 design page를 골라 새 화면을 시작한다. DP의 고정 구성(locked region)은 SCR에 복제하지
않고 **참조 상속**하며(렌더 시 DP에서 읽음), editable 캔버스는 빈 상태로 SCR이 소유한다.
**DP 원본 YAML은 절대 수정하지 않는다.**

사용:
  python instantiate_screen.py --project <projects/example> --template DP-MAIN \
         --name "주문 목록" --domain ORDER --type LIST [--archetype list]

동작(§6.2):
  1. spine_ledger.mint_scr_id 로 SCR-{DOMAIN}-{TYPE} 채번(전역 유일).
  2. 새 SCR-*.yaml(status: draft, layout: [] 빈 캔버스, from_template 핀) 작성.
  3. link-manifest.yaml 에 DP→SCR 엣지(screens[].template) 기록.
출력: <project>/model_repo/screens/<SCR-ID>.yaml
종료코드: 0 = 성공, 1 = 실패(채번 충돌·DP 없음 등).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

# harness-core/lib (spine_ledger) 단일 출처
_LIB = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(_LIB))
import spine_ledger  # noqa: E402

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

ARCHETYPE_BY_TYPE = {
    "LIST": "list", "DETAIL": "detail", "CREATE": "form", "EDIT": "form",
    "DASHBOARD": "dashboard", "POPUP": "popup", "WIZARD": "wizard", "ADMIN": "list",
}


def dp_version(dp: dict) -> int:
    v = dp.get("version")
    return int(v) if isinstance(v, int) else 1


def editable_slot_map(dp: dict) -> dict:
    """DP slots → {slot_id: editable(bool)}. 레거시 평면 슬롯(문자열)은 editable=True."""
    result: dict = {}
    for s in (dp.get("slots") or []):
        if isinstance(s, dict):
            result[s.get("id")] = bool(s.get("editable", True))
        elif isinstance(s, str):
            result[s] = True
    return result


def dp_layout_items(dp: dict) -> list:
    """DP의 디자인 아이템을 screen-model-schema-v2 의 layout 형태로 반환.

    우선순위: v2 `layout:`(스키마 통일) → 없으면 레거시 `components:`를 동치 변환.
    """
    if dp.get("layout"):
        return [it for it in dp["layout"] if isinstance(it, dict)]
    items = []
    for c in (dp.get("components") or []):
        items.append({
            "id": None,
            "source": {"kind": "ds", "ref": c.get("ref")},
            "position": {"slot": c.get("slot"), "order": c.get("order", 1)},
            "props": c.get("props") or {},
            "meta": {"label": c.get("note")} if c.get("note") else {},
        })
    return items


def _seed_suffix(it: dict, used: set) -> str:
    """seed CMP id 접미사: DP 아이템 id의 '.'뒤 토큰 우선, 없으면 ref 소문자. 중복 시 숫자 부여."""
    raw_id = it.get("id")
    if raw_id and "." in raw_id:
        base = raw_id.split(".", 1)[1]
    else:
        base = ((it.get("source") or {}).get("ref", "") or "cmp").lower()
    cand, n = base, 2
    while cand in used:
        cand, n = f"{base}{n}", n + 1
    used.add(cand)
    return cand


def seed_layout(dp: dict, scr_id: str) -> list:
    """DP의 **editable 슬롯** 아이템을 SCR.layout 시작 디자인으로 복사 시딩.

    - locked 슬롯 아이템은 복사하지 않는다 — DP 단일 출처를 유지하고 렌더 시 참조 상속한다
      (드리프트 0; ADR-001 "복사 대신 참조").
    - editable 슬롯 아이템은 그대로 복사하여 **첫 화면 렌더가 DP와 동일**해지게 한다(요구사항).
      CMP-* ID로 재채번하고 source/position/props 를 보존, provenance(seeded_from)를 남긴다.
    """
    ed = editable_slot_map(dp)
    cmp_prefix = scr_id.replace("SCR-", "CMP-", 1)
    seeds, used = [], set()
    for it in dp_layout_items(dp):
        slot = (it.get("position") or {}).get("slot")
        if not ed.get(slot, True):
            continue  # locked → 참조 상속(복사 안 함)
        cmp_id = f"{cmp_prefix}.{_seed_suffix(it, used)}"
        item: dict = {
            "id": cmp_id,
            "source": it.get("source") or {"kind": "ds", "ref": None},
            "position": it.get("position") or {"slot": slot, "order": 1},
        }
        if it.get("props"):
            item["props"] = it["props"]
        meta = dict(it.get("meta") or {})
        meta.pop("locked", None)
        meta["seeded_from"] = it.get("id") or f"{(it.get('source') or {}).get('ref', '')}@{slot}"
        item["meta"] = meta
        seeds.append(item)
    return seeds


def build_scr(scr_id: str, name: str, archetype: str, dp_id: str, dp_ver: int, dp: dict) -> dict:
    return {
        "schema_version": 2,
        "screen": {
            "id": scr_id,
            "name": name,
            "archetype": archetype,
            "status": "draft",
            "version": 1,
            "permission": "all",
            "template": {"page": dp_id, "version": dp_ver},
            "from_template": {"page": dp_id, "version": dp_ver},
        },
        # editable 캔버스는 DP에서 복사 시딩(첫 렌더가 DP와 동일). locked 구성은 DP 참조 상속(복제 안 함).
        "layout": seed_layout(dp, scr_id),
        "actions": [],
        "notes": [],
        "intake": {"open_questions": []},
    }


SCR_HEADER = (
    "# 인스턴스화 산출(ADR-002 §6): DP의 locked region은 DP에서 참조 상속(편집 불가).\n"
    "# editable 캔버스(layout)는 DP에서 복사 시딩된 시작 디자인으로, 이 화면이 소유·편집한다.\n"
    "# 첫 렌더는 DP와 동일(이름·메타 제외). DP 원본은 수정되지 않는다.\n"
)


def update_manifest(manifest_path: Path, scr_id: str, dp_id: str, dp_ver: int,
                    seeded: list | None = None) -> None:
    if not manifest_path.exists():
        return
    seeded = seeded or []
    seed_ids = [s.get("id") for s in seeded if isinstance(s, dict) and s.get("id")]
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    screens = manifest.setdefault("screens", [])
    if not any(isinstance(s, dict) and s.get("id") == scr_id for s in screens):
        screens.append({
            "id": scr_id,
            "status": "draft",
            "version": 1,
            "template": dp_id,
            "from_template": f"{dp_id}@v{dp_ver}",
            # editable seed 복사분만큼 CMP 카운터를 진행시켜 다음 채번이 충돌하지 않게 한다.
            "next_seq": {"CMP": len(seed_ids) + 1, "REQ": 1, "NOTE": 1, "NFR": 1},
            "components": seed_ids,
            "requirements": [],
            "notes": [],
        })
    manifest_path.write_text(
        yaml.dump(manifest, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="DP → SCR 인스턴스화 (ADR-002 §6)")
    ap.add_argument("--project", required=True, help="프로젝트 루트 (projects/<id>)")
    ap.add_argument("--template", required=True, help="design page ID (DP-MAIN 등)")
    ap.add_argument("--name", required=True, help="화면 이름(한국어)")
    ap.add_argument("--domain", required=True, help="도메인 (ORDER, TODO ...)")
    ap.add_argument("--type", required=True, dest="screen_type",
                    help="화면 타입 (LIST|DETAIL|CREATE|EDIT|ADMIN|DASHBOARD|POPUP|WIZARD)")
    ap.add_argument("--archetype", default=None, help="명시 archetype (미지정 시 type에서 추론)")
    args = ap.parse_args(argv[1:])

    project = Path(args.project)
    model_repo = project / "model_repo"
    dp_path = project / "foundation" / "design-pages" / f"{args.template}.yaml"
    if not dp_path.exists():
        print(f"[instantiate] ❌ DP 없음: {dp_path}", file=sys.stderr)
        return 1
    dp = yaml.safe_load(dp_path.read_text(encoding="utf-8")) or {}
    dp_ver = dp_version(dp)

    try:
        scr_id = spine_ledger.mint_scr_id(model_repo, args.domain, args.screen_type)
    except ValueError as e:
        print(f"[instantiate] ❌ 채번 실패: {e}", file=sys.stderr)
        return 1

    archetype = args.archetype or ARCHETYPE_BY_TYPE.get(args.screen_type.upper(), "list")
    scr = build_scr(scr_id, args.name, archetype, args.template, dp_ver, dp)
    seeded = scr["layout"]

    screens_dir = model_repo / "screens"
    screens_dir.mkdir(parents=True, exist_ok=True)
    out_path = screens_dir / f"{scr_id}.yaml"
    body = yaml.dump(scr, allow_unicode=True, sort_keys=False, default_flow_style=False)
    out_path.write_text(SCR_HEADER + body, encoding="utf-8")

    update_manifest(model_repo / "link-manifest.yaml", scr_id, args.template, dp_ver, seeded)

    print(f"[instantiate] ✅ {scr_id} 생성 (from {args.template}@v{dp_ver})")
    print(f"    → {out_path.as_posix()}")
    if seeded:
        print(f"    layout: editable seed {len(seeded)}개 복사(첫 렌더=DP 동일). locked는 DP 참조 상속.")
        print(f"    다음: layout-recommend 로 seed 조정/추가 → render_screen.")
    else:
        print(f"    layout=[] (DP에 editable seed 없음 — 빈 캔버스). 다음: layout-recommend → render_screen.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
