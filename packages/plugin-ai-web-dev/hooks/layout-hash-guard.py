#!/usr/bin/env python3
"""
Hook: layout-hash-guard.py  (ADR-002 D5 / §5 ③ — Phase α 해시 가드)
트리거: Phase α(shell 컴포넌트 일괄 생성) 진입 시 / 수동 실행.
목적:  "②확정 위치 ③변경 금지"의 기계적 강제.
       각 pack의 screens[].yaml_ref(SCR)를 ②와 동일한 엔진(harness-core/render/pins)으로
       재렌더해 layout_hash 를 재계산하고, spec 의 pinned_contract.layout_hash 와 비교한다.
       - layout_hash 불일치 → ❌ error + exit 1 (빌드 실패). 위치 계약이 깨졌다는 뜻.
       - render_hash 불일치 → ⚠ warn (비차단). 렌더 엔진 버전 의존성이 커 위치 계약의 핵심이 아님.
       - pinned_contract.layout_hash 가 없거나 placeholder(sha256:... 등) → ⚠ warn + 비차단
         (아직 ②가 핀을 발행하지 않은 단계).

입력:
  python layout-hash-guard.py <PACK/spec.yaml> [<spec.yaml> ...]
  python layout-hash-guard.py --root <project>     # <project>/model_repo/specs/PACK-*/spec.yaml 전체

종료코드: 0 = 통과(또는 warn), 1 = layout_hash 불일치(빌드 차단)
정책: ADR-002 §4·§5, rules/gate-b-checklist.md, README(③) Phase α
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# Windows 콘솔(cp949 등) 출력 크래시 방지 (다른 훅과 동일 블록)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

# harness-core/render 를 import path 에 추가 (manifest-sync.py 와 동일 방식).
# 이 훅 위치: packages/plugin-ai-web-dev/hooks/layout-hash-guard.py
#   parents[2] = packages/  →  packages/harness-core/render
_RENDER_DIR = Path(__file__).resolve().parents[2] / "harness-core" / "render"
sys.path.insert(0, str(_RENDER_DIR))

try:
    import pins  # noqa: E402  — 핀 계산 단일 출처. 직접 해시 재구현 금지.
except Exception as e:  # graceful skip — 가드 부재가 빌드를 막아선 안 된다.
    print(f"[layout-hash-guard] WARN: pins 모듈 import 실패 → 가드 skip (비차단): {e}\n"
          f"    (기대 경로: {_RENDER_DIR})", file=sys.stderr)
    sys.exit(0)


def _is_placeholder(h) -> bool:
    """발행 전 placeholder 핀 판별 — 단일 출처(pins.is_placeholder_hash) 위임(②와 동일 판정, D5).
    실제 핀은 sha256:<64 hex 소문자>; 그 외(빈값·'sha256:...'·'sha256:golden'·비-64자)는 미발행."""
    return pins.is_placeholder_hash(h)


def find_specs(args: list) -> tuple[list[Path], Path | None]:
    """입력 인자 → (spec.yaml 경로 리스트, project_root).
    --root <project> 면 project/model_repo/specs/PACK-*/spec.yaml 전체."""
    if "--root" in args:
        root = Path(args[args.index("--root") + 1]).resolve()
        specs = sorted((root / "model_repo" / "specs").glob("PACK-*/spec.yaml"))
        return specs, root
    specs = [Path(a).resolve() for a in args if not a.startswith("--")]
    return specs, None


def project_root_for(spec_path: Path, root_hint: Path | None) -> Path:
    """yaml_ref(프로젝트 루트 상대) 결합용 프로젝트 루트.
    --root 가 주어졌으면 그것, 아니면 spec 경로에서 model_repo 의 부모를 역추적."""
    if root_hint is not None:
        return root_hint
    for parent in spec_path.parents:
        if (parent / "model_repo").is_dir():
            return parent
    # PACK-*/spec.yaml 이 model_repo/specs 아래라 가정 → 4단계 상위가 프로젝트 루트.
    return spec_path.parents[3] if len(spec_path.parents) >= 4 else spec_path.parent


def check_screen(scr_id: str, scr_path: Path, contract: dict) -> str:
    """단일 화면 검증 → 'error' | 'warn' | 'pass'. 메시지는 직접 출력."""
    expect_layout = (contract or {}).get("layout_hash")
    expect_render = (contract or {}).get("render_hash")

    if _is_placeholder(expect_layout):
        print(f"[layout-hash-guard] ⚠ {scr_id}: pinned_contract.layout_hash 미발행(placeholder) "
              f"→ 비차단 통과. (②가 아직 핀을 확정하지 않음)")
        return "warn"

    if not scr_path.exists():
        print(f"[layout-hash-guard] ❌ {scr_id}: yaml_ref SCR 파일 없음: {scr_path}", file=sys.stderr)
        return "error"

    actual = pins.compute_pins(scr_path)  # ②와 동일 엔진으로 재계산 (단일 출처)
    status = "pass"

    if actual["layout_hash"] != expect_layout:
        print(f"[layout-hash-guard] ❌ {scr_id}: layout_hash 불일치 — 확정 위치가 변경됨(③변경 금지 위반).\n"
              f"    pinned   {expect_layout}\n"
              f"    재계산   {actual['layout_hash']}\n"
              f"    → SCR 의 layout/position 을 ②확정 상태로 되돌리거나 Change Order 로 ②에서 핀을 갱신하세요.",
              file=sys.stderr)
        status = "error"

    # render_hash 는 있을 때만, 그리고 불일치는 warn(비차단)으로 구분.
    if not _is_placeholder(expect_render) and actual["render_hash"] != expect_render:
        print(f"[layout-hash-guard] ⚠ {scr_id}: render_hash 불일치(비차단 — 렌더 엔진 버전 의존성).\n"
              f"    pinned   {expect_render}\n"
              f"    재계산   {actual['render_hash']}", file=sys.stderr)
        if status == "pass":
            status = "warn"

    if status == "pass":
        print(f"[layout-hash-guard] ✅ {scr_id}: layout_hash 일치 (확정 위치 보존).")
    return status


def check_spec(spec_path: Path, root_hint: Path | None) -> int:
    """단일 spec.yaml → 화면별 검증. 1개라도 error 면 1 반환."""
    try:
        doc = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        print(f"[layout-hash-guard] ⚠ {spec_path}: spec.yaml 파싱 실패 → skip (비차단): {e}",
              file=sys.stderr)
        return 0
    if not isinstance(doc, dict):
        return 0

    pack_id = ((doc.get("meta") or {}).get("id")) or spec_path.parent.name
    root = project_root_for(spec_path, root_hint)
    print(f"[layout-hash-guard] {pack_id} 검사 (root={root})")

    rc = 0
    screens = doc.get("screens") or []
    for screen in screens:
        if not isinstance(screen, dict):
            continue
        scr_id = screen.get("id") or "(unknown)"
        yaml_ref = screen.get("yaml_ref")
        if not yaml_ref:
            print(f"[layout-hash-guard] ⚠ {scr_id}: yaml_ref 없음 → skip.", file=sys.stderr)
            continue
        scr_path = (root / yaml_ref).resolve()
        if check_screen(str(scr_id), scr_path, screen.get("pinned_contract") or {}) == "error":
            rc = 1
    return rc


def main(argv: list) -> int:
    args = argv[1:]
    specs, root_hint = find_specs(args)
    if not specs:
        print("[layout-hash-guard] 검사할 spec.yaml 이 없습니다. "
              "사용법: layout-hash-guard.py <spec.yaml ...> | --root <project>", file=sys.stderr)
        return 0  # 검사 대상 부재는 빌드를 막지 않는다(비차단).

    rc = 0
    for spec_path in specs:
        if not spec_path.exists():
            print(f"[layout-hash-guard] ⚠ spec 파일 없음: {spec_path} → skip.", file=sys.stderr)
            continue
        if check_spec(spec_path, root_hint) == 1:
            rc = 1

    if rc == 0:
        print("[layout-hash-guard] PASS — 모든 화면의 layout_hash 가 ②확정 계약과 일치(또는 미발행).")
    else:
        print("[layout-hash-guard] BLOCK — layout_hash 불일치 화면이 있어 Phase α 빌드를 중단합니다.",
              file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
