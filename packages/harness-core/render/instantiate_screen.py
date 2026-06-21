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


def build_scr(scr_id: str, name: str, archetype: str, dp_id: str, dp_ver: int) -> dict:
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
        "layout": [],   # 빈 editable 캔버스 — 고정 구성은 DP 참조 상속(SCR에 복제 안 함)
        "actions": [],
        "notes": [],
        "intake": {"open_questions": []},
    }


SCR_HEADER = (
    "# 인스턴스화 산출(ADR-002 §6): DP의 locked region은 DP에서 참조 상속(편집 불가),\n"
    "# layout(editable 캔버스)만 이 화면이 소유한다. DP 원본은 수정되지 않는다.\n"
)


def update_manifest(manifest_path: Path, scr_id: str, dp_id: str, dp_ver: int) -> None:
    if not manifest_path.exists():
        return
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    screens = manifest.setdefault("screens", [])
    if not any(isinstance(s, dict) and s.get("id") == scr_id for s in screens):
        screens.append({
            "id": scr_id,
            "status": "draft",
            "version": 1,
            "template": dp_id,
            "from_template": f"{dp_id}@v{dp_ver}",
            "next_seq": {"CMP": 1, "REQ": 1, "NOTE": 1, "NFR": 1},
            "components": [],
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
    scr = build_scr(scr_id, args.name, archetype, args.template, dp_ver)

    screens_dir = model_repo / "screens"
    screens_dir.mkdir(parents=True, exist_ok=True)
    out_path = screens_dir / f"{scr_id}.yaml"
    body = yaml.dump(scr, allow_unicode=True, sort_keys=False, default_flow_style=False)
    out_path.write_text(SCR_HEADER + body, encoding="utf-8")

    update_manifest(model_repo / "link-manifest.yaml", scr_id, args.template, dp_ver)

    print(f"[instantiate] ✅ {scr_id} 생성 (from {args.template}@v{dp_ver})")
    print(f"    → {out_path.as_posix()}")
    print(f"    layout=[] (빈 캔버스). 다음: layout-recommend 로 컴포넌트 배치 → render_screen.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
