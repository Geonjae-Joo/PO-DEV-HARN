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

사용:
  python spec-pack-guard.py model_repo/screens/SCR-ORDER-LIST.yaml [SCR-...]
  인자 없으면 model_repo/screens/SCR-*.yaml 전체.

종료코드: 0 = 발행 가능, 1 = 차단(이유 stderr). cwd = projects/<id>/ 가정.
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
        for st in steps:
            scr = st.get("screen")
            if scr in screen_ids:
                covered.add(scr)
    return covered


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        args = [str(p) for p in Path(".").glob("model_repo/screens/SCR-*.yaml")]
    if not args:
        print("[spec-pack-guard] 검증할 화면 없음", file=sys.stderr)
        return 1

    screen_ids: set[str] = set()
    for fp_str in args:
        fp = Path(fp_str)
        if not fp.exists():
            block(f"{fp}: 파일 없음")
            continue
        doc = load(fp)
        if not isinstance(doc, dict):
            continue
        check_screen(fp, doc)
        sid = (doc.get("screen") or {}).get("id")
        if sid:
            screen_ids.add(sid)

    # 여정 커버리지 경고 (비차단)
    covered = screens_referenced_by_journeys(screen_ids)
    uncovered = screen_ids - covered
    if uncovered:
        warn("어떤 JRN- 여정에도 등장하지 않는 화면: " + ", ".join(sorted(uncovered))
             + " — Phase γ E2E 누락 가능 (journey-map 확인 권장).")

    for w in WARNS:
        print(f"[spec-pack-guard] ⚠ {w}")
    if BLOCKS:
        for b in BLOCKS:
            print(f"[spec-pack-guard] ❌ {b}", file=sys.stderr)
        print(f"\n[spec-pack-guard] 차단 — {len(BLOCKS)}건. 팩 발행 불가.", file=sys.stderr)
        return 1
    print(f"[spec-pack-guard] ✅ {len(screen_ids)}개 화면 발행 가능 (confirmed + 참조 무결).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
