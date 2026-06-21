#!/usr/bin/env python3
"""
spec-pack-guard.py — spec-generator 발행 전 기계 가드 (B3 + C1).

목적:
  PACK-* 팩을 발행하기 전에 반드시 통과해야 하는 선결 조건을 기계적으로 강제한다.
  prose-only("confirmed 화면만 발행") 가드를 실제 코드로 만든다.

검사(AND):
  1. 대상 화면이 모두 status: confirmed   (draft/review/… 차단)
  2. 화면 action 의 outcome.target 이 참조하는 ENT-/EXT- 가 model_repo 에 실존  (dangling ref 차단)
  3. (경고) 화면을 거치는 JRN- 가 하나도 없으면 안내 — 차단은 아님

pack spec-pack.yaml 검사(ADR-002 D5):
  4. screens[].pinned_contract 의 layout_hash/render_hash 를 harness-core/render/pins.py
     의 compute_pins 로 재계산해 대조.
       - 핀이 있고 불일치 → error (스냅샷 stale, 재핀 필요)
       - 핀이 placeholder("sha256:..." / 빈 값) 또는 없음 → warn (--write-pins 안내)

사용:
  # screen model 가드 (종전)
  python spec-pack-guard.py model_repo/screens/SCR-ORDER-LIST.yaml [SCR-...]
  인자 없으면 model_repo/screens/SCR-*.yaml 전체.

  # pack spec-pack.yaml 핀 검증
  python spec-pack-guard.py model_repo/specs/PACK-ORDER/spec-pack.yaml

  # pack spec-pack.yaml 핀 기록(작성)
  python spec-pack-guard.py --write-pins model_repo/specs/PACK-ORDER/spec-pack.yaml

종료코드: 0 = 발행 가능, 1 = 차단(이유 stderr). cwd = projects/<id>/ 가정(screen 가드).
pack spec-pack.yaml 은 yaml_ref 를 프로젝트 루트 기준으로 해석하므로 cwd 무관.
"""

import sys
from pathlib import Path

import yaml

# Windows 콘솔(cp949 등) 유니코드 출력 크래시 방지
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

ENT_DIR = Path("model_repo/entities")
EXT_DIR = Path("model_repo/externals")
JRN_DIR = Path("model_repo/journeys")

# ── 핀 계산 단일 출처(harness-core/render/pins.py) import ───────────────────────
# on-save-lint-L1-L4.py 가 harness-core/lib 를 sys.path 에 추가하는 방식과 동일 패턴.
# 런타임 레이아웃이 달라 경로를 못 찾거나 import 실패 시 graceful skip + warn 한다.
_compute_pins = None
_is_placeholder_shared = None
for _anc in Path(__file__).resolve().parents:
    _render_dir = _anc / "harness-core" / "render"
    if _render_dir.exists():
        if str(_render_dir) not in sys.path:
            sys.path.insert(0, str(_render_dir))
        try:
            from pins import compute_pins as _compute_pins  # type: ignore
            from pins import is_placeholder_hash as _is_placeholder_shared  # type: ignore
        except Exception:
            _compute_pins = None
            _is_placeholder_shared = None
        break

BLOCKS: list[str] = []
WARNS: list[str] = []


def block(msg: str) -> None:
    BLOCKS.append(msg)


def warn(msg: str) -> None:
    WARNS.append(msg)


def load(fp: Path):
    try:
        return yaml.safe_load(fp.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        block(f"{fp.name}: YAML 파싱 실패 — {e}")
        return None


def referent_exists(ref_id: str) -> bool:
    if ref_id.startswith("ENT-"):
        return (ENT_DIR / f"{ref_id}.yaml").exists()
    if ref_id.startswith("EXT-"):
        return (EXT_DIR / f"{ref_id}.yaml").exists()
    return True  # SCR-/기타 target 은 이 가드의 관심사 아님


def check_screen(fp: Path, doc: dict) -> None:
    screen = doc.get("screen", {}) if isinstance(doc, dict) else {}
    sid = screen.get("id", fp.stem)
    status = screen.get("status")
    if status != "confirmed":
        block(f"{sid}: status='{status}' — confirmed 아님. Gate A 통과 후에만 팩 발행 가능.")

    # action outcome.target 의 ENT-/EXT- 실존 검증
    for action in (doc.get("actions") or []):
        outcome = action.get("outcome") or {}
        target = outcome.get("target")
        if isinstance(target, str) and (target.startswith("ENT-") or target.startswith("EXT-")):
            if not referent_exists(target):
                block(f"{sid}: action '{action.get('id')}' outcome.target={target} "
                      f"— 참조 계약 파일이 model_repo 에 없음 (dangling ref).")


def screens_referenced_by_journeys(screen_ids: set[str]) -> set[str]:
    """JRN- 중 이 화면들을 step 으로 거치는 것이 있는 화면 집합."""
    covered: set[str] = set()
    if not JRN_DIR.exists():
        return covered
    for jf in JRN_DIR.glob("JRN-*.yaml"):
        jdoc = load(jf)
        if not isinstance(jdoc, dict):
            continue
        steps = (jdoc.get("journey") or {}).get("steps") or []
        for st in step