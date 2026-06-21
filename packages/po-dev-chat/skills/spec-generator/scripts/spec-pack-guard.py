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

pack spec.yaml 검사(ADR-002 D5):
  4. screens[].pinned_contract 의 layout_hash/render_hash 를 harness-core/render/pins.py
     의 compute_pins 로 재계산해 대조.
       - 핀이 있고 불일치 → error (스냅샷 stale, 재핀 필요)
       - 핀이 placeholder("sha256:..." / 빈 값) 또는 없음 → warn (--write-pins 안내)

사용:
  # screen model 가드 (종전)
  python spec-pack-guard.py model_repo/screens/SCR-ORDER-LIST.yaml [SCR-...]
  인자 없으면 model_repo/screens/SCR-*.yaml 전체.

  # pack spec.yaml 핀 검증
  python spec-pack-guard.py model_repo/specs/PACK-ORDER/spec.yaml

  # pack spec.yaml 핀 기록(작성)
  python spec-pack-guard.py --write-pins model_repo/specs/PACK-ORDER/spec.yaml

종료코드: 0 = 발행 가능, 1 = 차단(이유 stderr). cwd = projects/<id>/ 가정(screen 가드).
pack spec.yaml 은 yaml_ref 를 프로젝트 루트 기준으로 해석하므로 cwd 무관.
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
        for st in steps:
            scr = st.get("screen")
            if scr in screen_ids:
                covered.add(scr)
    return covered


def _is_pack_spec(fp: Path, doc) -> bool:
    """pack spec.yaml 인지 판별: meta.id 가 PACK- 로 시작하고 screens[] 가 매핑 리스트."""
    if not isinstance(doc, dict):
        return False
    meta = doc.get("meta") or {}
    return isinstance(meta, dict) and str(meta.get("id", "")).startswith("PACK-")


def _project_root_of_pack(spec_path: Path) -> Path:
    """spec.yaml(.../model_repo/specs/PACK-*/spec.yaml) → 프로젝트 루트 역산.
    PACK-* → specs → model_repo → <프로젝트 루트>. 즉 parents[3]."""
    p = spec_path.resolve()
    # 안전 탐색: model_repo 디렉터리를 만나면 그 상위가 프로젝트 루트.
    for parent in p.parents:
        if parent.name == "model_repo":
            return parent.parent
    return p.parents[3] if len(p.parents) >= 4 else p.parent


_PLACEHOLDER_HASHES = {"", "sha256:...", "sha256:golden", "golden"}


def _is_placeholder(val) -> bool:
    # 단일 출처(pins.is_placeholder_hash)와 동일 판정: 실제 핀은 sha256:<64hex>, 그 외 전부 placeholder.
    # ③ layout-hash-guard 와 일치(D5 단일 출처). import 실패 시 기존 집합으로 폴백.
    if _is_placeholder_shared is not None:
        return _is_placeholder_shared(val)
    return val is None or str(val).strip() in _PLACEHOLDER_HASHES


def check_pack_pins(spec_path: Path, doc: dict) -> None:
    """screens[].pinned_contract 의 layout_hash/render_hash 를 compute_pins 로 대조."""
    if _compute_pins is None:
        warn(f"{spec_path.name}: pins.py(harness-core/render) import 실패 — 핀 검증 건너뜀.")
        return
    root = _project_root_of_pack(spec_path)
    for scr in (doc.get("screens") or []):
        if not isinstance(scr, dict):
            continue
        sid = scr.get("id", "?")
        yaml_ref = scr.get("yaml_ref")
        pinned = scr.get("pinned_contract") or {}
        if not yaml_ref:
            warn(f"{sid}: yaml_ref 없음 — 핀 검증 불가.")
            continue
        scr_path = (root / yaml_ref).resolve()
        if not scr_path.exists():
            block(f"{sid}: yaml_ref 파일 없음 ({scr_path}).")
            continue
        try:
            pins = _compute_pins(scr_path)
        except Exception as e:  # noqa: BLE001
            block(f"{sid}: 핀 계산 실패 — {e}")
            continue

        lay = pinned.get("layout_hash")
        ren = pinned.get("render_hash")
        if _is_placeholder(lay) or _is_placeholder(ren):
            warn(f"{sid}: pinned_contract 핀 미작성(placeholder/누락) — "
                 f"--write-pins 로 채우세요.")
            continue
        if lay != pins["layout_hash"]:
            block(f"{sid}: layout_hash 불일치(스냅샷 stale, 재핀 필요)\n"
                  f"    spec     {lay}\n    computed {pins['layout_hash']}")
        if ren != pins["render_hash"]:
            block(f"{sid}: render_hash 불일치(스냅샷 stale, 재핀 필요)\n"
                  f"    spec     {ren}\n    computed {pins['render_hash']}")


def write_pack_pins(spec_path: Path) -> int:
    """--write-pins: 각 screen 의 pinned_contract.layout_hash/render_hash/version 을
    compute_pins 결과로 채워 spec.yaml 을 저장. 기존 키 순서/다른 필드 보존."""
    if _compute_pins is None:
        print("[spec-pack-guard] ❌ pins.py(harness-core/render) import 실패 — "
              "--write-pins 불가.", file=sys.stderr)
        return 1
    doc = load(spec_path)
    if not _is_pack_spec(spec_path, doc):
        print(f"[spec-pack-guard] ❌ {spec_path} 는 pack spec.yaml 이 아님 "
              f"(meta.id 가 PACK- 아님).", file=sys.stderr)
        return 1
    root = _project_root_of_pack(spec_path)
    written = 0
    for scr in (doc.get("screens") or []):
        if not isinstance(scr, dict):
            continue
        sid = scr.get("id", "?")
        yaml_ref = scr.get("yaml_ref")
        if not yaml_ref:
            print(f"[spec-pack-guard] ⚠ {sid}: yaml_ref 없음 — 건너뜀.", file=sys.stderr)
            continue
        scr_path = (root / yaml_ref).resolve()
        if not scr_path.exists():
            print(f"[spec-pack-guard] ⚠ {sid}: yaml_ref 파일 없음 ({scr_path}) — 건너뜀.",
                  file=sys.stderr)
            continue
        pins = _compute_pins(scr_path)
        pinned = scr.get("pinned_contract")
        if not isinstance(pinned, dict):
            pinned = {}
            scr["pinned_contract"] = pinned
        # 기존 다른 필드(hash/git_ref/from_template) 보존, 핀 3종만 갱신/추가.
        pinned["version"] = pins["version"]
        pinned["layout_hash"] = pins["layout_hash"]
        pinned["render_hash"] = pins["render_hash"]
        written += 1
        print(f"[spec-pack-guard] ✏ {sid}: version={pins['version']} "
              f"layout={pins['layout_hash'][:16]}… render={pins['render_hash'][:16]}…")

    spec_path.write_text(
        yaml.dump(doc, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"[spec-pack-guard] ✅ 핀 기록 완료 — {written}개 화면 → {spec_path}")
    return 0


def main() -> int:
    # --write-pins 모드: pack spec.yaml 의 핀을 계산해 기록하고 종료.
    if "--write-pins" in sys.argv:
        targets = [a for a in sys.argv[1:] if not a.startswith("--")]
        if not targets:
            print("[spec-pack-guard] --write-pins: pack spec.yaml 경로 필요",
                  file=sys.stderr)
            return 2
        rc = 0
        for t in targets:
            fp = Path(t)
            if not fp.exists():
                print(f"[spec-pack-guard] ❌ 파일 없음: {fp}", file=sys.stderr)
                rc = 1
                continue
            rc = write_pack_pins(fp) or rc
        return rc

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        args = [str(p) for p in Path(".").glob("model_repo/screens/SCR-*.yaml")]
    if not args:
        print("[spec-pack-guard] 검증할 화면 없음", file=sys.stderr)
        return 1

    screen_ids: set[str] = set()
    pack_count = 0
    for fp_str in args:
        fp = Path(fp_str)
        if not fp.exists():
            block(f"{fp}: 파일 없음")
            continue
        doc = load(fp)
        if not isinstance(doc, dict):
            continue
        if _is_pack_spec(fp, doc):
            # pack spec.yaml → 핀 일치 검증 (ADR-002 D5)
            check_pack_pins(fp, doc)
            pack_count += 1
            continue
        check_screen(fp, doc)
        sid = (doc.get("screen") or {}).get("id")
        if sid:
            screen_ids.add(sid)

    # 여정 커버리지 경고 (비차단) — screen model 가드 대상에만 적용
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
    if pack_count:
        print(f"[spec-pack-guard] ✅ pack {pack_count}개 핀 검증 통과 "
              f"(layout_hash·render_hash 일치).")
    if screen_ids:
        print(f"[spec-pack-guard] ✅ {len(screen_ids)}개 화면 발행 가능 "
              f"(confirmed + 참조 무결).")
    if not pack_count and not screen_ids:
        print("[spec-pack-guard] ✅ 검증 통과 (대상 0건).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
