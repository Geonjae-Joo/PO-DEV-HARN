#!/usr/bin/env python3
"""
spec-pack-guard.py — spec-generator 발행 전 기계 가드 (B3 + C1).

목적:
  PACK-* 팩을 발행하기 전에 반드시 통과해야 하는 선결 조건을 기계적으로 강제한다.
  prose-only("confirmed 화면만 발행") 가드를 실제 코드로 만든다.

검사(AND):
  1. 대상 화면이 모두 status: confirmed   (draft/review/… 차단)
  2. 화면 action 의 outcome.target 이 참조하는 ENT-/EXT-/SCR- 가 model_repo 에 실존  (dangling ref 차단)
  3. outcome.type: open 의 target SCR- 이 template.page: DP-POPUP 인지 확인  (archetype mismatch 경고)
  4. (경고) 화면을 거치는 JRN- 가 하나도 없으면 안내 — 차단은 아님

pack spec-pack.yaml 검사(ADR-002 D5):
  5. screens[].pinned_contract 의 layout_hash/render_hash 를 harness-core/render/pins.py
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
SCR_DIR = Path("model_repo/screens")
DP_DIR  = Path("foundation/design-pages")

# ── 핀 계산 단일 출처(harness-core/render/pins.py) import ───────────────────────
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
    if ref_id.startswith("SCR-"):
        return (SCR_DIR / f"{ref_id}.yaml").exists()
    return True


def get_screen_template(scr_id: str) -> str | None:
    """SCR-*.yaml 에서 template.page 값을 읽어 반환. 파일 없거나 파싱 실패 시 None."""
    scr_path = SCR_DIR / f"{scr_id}.yaml"
    if not scr_path.exists():
        return None
    try:
        doc = yaml.safe_load(scr_path.read_text(encoding="utf-8")) or {}
        return (doc.get("screen", {}).get("template") or {}).get("page")
    except Exception:
        return None


def check_screen(fp: Path, doc: dict) -> None:
    screen = doc.get("screen", {}) if isinstance(doc, dict) else {}
    sid = screen.get("id", fp.stem)
    status = screen.get("status")
    if status != "confirmed":
        block(f"{sid}: status='{status}' — confirmed 아님. Gate A 통과 후에만 팩 발행 가능.")

    for action in (doc.get("actions") or []):
        outcome = action.get("outcome") or {}
        otype  = outcome.get("type")
        target = outcome.get("target")
        aid    = action.get("id", "?")

        if not isinstance(target, str):
            continue

        # ENT-/EXT-/SCR- dangling ref 검증
        if not referent_exists(target):
            block(
                f"{sid}: action '{aid}' outcome.target={target} "
                f"— 참조 파일이 model_repo 에 없음 (dangling ref)."
            )

        # type: open → target 이 DP-POPUP archetype 이어야 함
        if otype == "open" and target.startswith("SCR-"):
            tmpl = get_screen_template(target)
            if tmpl is None:
                pass  # 파일 없음은 위 dangling ref 에서 이미 차단
            elif tmpl != "DP-POPUP":
                warn(
                    f"{sid}: action '{aid}' outcome.type=open target={target} 의 "
                    f"template.page='{tmpl}' — DP-POPUP 이어야 합니다 (archetype mismatch)."
                )


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


def _pack_project_root(fp: Path) -> Path:
    """yaml_ref(프로젝트 루트 상대) 결합용 프로젝트 루트 해석.
    layout-hash-guard.py 의 project_root_for 와 동일 방식: 경로를 거슬러 model_repo 를
    가진 디렉터리를 찾고, 못 찾으면 specs/PACK-*/spec-pack.yaml(=4단계) 가정으로 폴백.
    (구 구현 fp.parent.parent.parent 는 model_repo 까지만 올라가 yaml_ref 해석이 깨졌음.)"""
    fp = fp.resolve()
    for parent in fp.parents:
        if (parent / "model_repo").is_dir():
            return parent
    return fp.parents[3] if len(fp.parents) >= 4 else fp.parent


def check_pack(fp: Path, write_pins: bool = False) -> None:
    """spec-pack.yaml 핀 검증 또는 기록."""
    pack_root = _pack_project_root(fp)  # model_repo/specs/PACK-*/spec-pack.yaml → project root
    doc = load(fp)
    if not isinstance(doc, dict):
        return

    for scr_entry in (doc.get("screens") or []):
        scr_id = scr_entry.get("id", "?")
        yaml_ref = scr_entry.get("yaml_ref")
        if not yaml_ref:
            warn(f"{fp.name}: screens[{scr_id}].yaml_ref 없음.")
            continue

        scr_path = pack_root / yaml_ref
        if not scr_path.exists():
            block(f"{fp.name}: screens[{scr_id}].yaml_ref '{yaml_ref}' 파일 없음.")
            continue

        contract = scr_entry.get("pinned_contract") or {}

        if write_pins:
            if _compute_pins is None:
                warn(f"{fp.name}: pins.py import 실패 — 핀을 계산할 수 없습니다.")
                continue
            pins = _compute_pins(scr_path)
            contract.update(pins)
            scr_entry["pinned_contract"] = contract
            print(f"[guard] ✍ {scr_id} 핀 기록: layout={pins.get('layout_hash','?')[:23]}…")
        else:
            lh = contract.get("layout_hash", "")
            rh = contract.get("render_hash", "")
            is_placeholder = _is_placeholder_shared or (lambda v: not str(v).startswith("sha256:"))
            if is_placeholder(lh) or is_placeholder(rh):
                warn(
                    f"{fp.name}: screens[{scr_id}].pinned_contract 핀 미발행. "
                    f"python spec-pack-guard.py --write-pins {fp} 실행 후 재발행."
                )
            elif _compute_pins is not None:
                actual = _compute_pins(scr_path)
                if actual.get("layout_hash") != lh:
                    block(
                        f"{fp.name}: screens[{scr_id}] layout_hash 불일치 "
                        f"(stale). --write-pins 로 재핀 필요."
                    )
                if actual.get("render_hash") != rh:
                    block(
                        f"{fp.name}: screens[{scr_id}] render_hash 불일치 "
                        f"(stale). --write-pins 로 재핀 필요."
                    )

    if write_pins:
        fp.write_text(yaml.dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
        print(f"[guard] ✅ {fp} 핀 저장 완료.")


def main(argv: list[str]) -> int:
    args = argv[1:]
    write_pins = "--write-pins" in args
    targets = [Path(a) for a in args if not a.startswith("--")]

    # 인자 없으면 SCR-*.yaml 전체
    if not targets:
        targets = sorted(SCR_DIR.glob("SCR-*.yaml"))
    if not targets:
        print("[guard] 검사할 파일 없음.", file=sys.stderr)
        return 0

    screen_ids: set[str] = set()

    for fp in targets:
        if not fp.exists():
            block(f"{fp}: 파일 없음.")
            continue

        # spec-pack.yaml 경로인지 판단
        if fp.name == "spec-pack.yaml" or str(fp).endswith("spec-pack.yaml"):
            check_pack(fp, write_pins=write_pins)
            continue

        doc = load(fp)
        if doc is None:
            continue
        check_screen(fp, doc)
        sid = (doc.get("screen") or {}).get("id", fp.stem)
        screen_ids.add(sid)

    # JRN 커버리지 경고 (screen 가드에서만)
    if screen_ids:
        covered = screens_referenced_by_journeys(screen_ids)
        uncovered = screen_ids - covered
        for sid in sorted(uncovered):
            warn(f"{sid}: 이 화면을 거치는 JRN- 여정이 없습니다. journey-map 스킬 실행 권장.")

    if WARNS:
        for w in WARNS:
            print(f"[guard] ⚠ {w}", file=sys.stderr)
    if BLOCKS:
        for b in BLOCKS:
            print(f"[guard] ❌ {b}", file=sys.stderr)
        print(f"\n[guard] 발행 차단: {len(BLOCKS)}건 오류를 해결하세요.", file=sys.stderr)
        return 1

    print(f"[guard] ✅ 검사 통과 ({len(targets)}개 파일, 경고 {len(WARNS)}건).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
