#!/usr/bin/env python3
"""harness-core/lib/spine_ledger.py

스파인 ID 원장(link-manifest.yaml) 검증·채번 공용 라이브러리 — 전 런타임 공유 단일 출처.

배경(B2):
  link-manifest.yaml 이 "채번의 유일한 근거"라고 문서화돼 있으나, 이전에는 어떤 코드도
  카운터를 읽거나 전역 유일성을 검사하지 않았다(LLM 자율). 이 모듈이 그것을 기계화한다.

제공:
  - scan_ids(model_repo): model_repo 의 모든 정의 ID 수집 (id: 키 기준)
  - find_global_dups(...): 파일을 가로지르는 ID 중복 탐지 (전역 유일성)
  - load_manifest / next_counters: 관측 ID 로 다음 채번 번호 계산
  - check(): 차단(중복) + 경고(미등록/드리프트) 판정 dict 반환
  - reconcile(): 관측값으로 manifest 카운터·screens 레지스트리 재작성

CLI:
  python spine_ledger.py [--root DIR] [--reconcile]
  종료코드: 0 = 전역 유일성 OK, 1 = 중복 발견(차단).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Windows 콘솔(cp949 등)에서 이모지/유니코드 출력 시 크래시 방지
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

# 정의 ID 접두 (참조가 아닌 '정의'를 갖는 것). spine-ids.md 와 일치.
DEF_PREFIXES = ("SCR-", "CMP-", "REQ-", "NOTE-", "NFR-", "ENT-", "EXT-", "JRN-", "PRM-", "Q-", "DP-")
SPINE_RE = re.compile(r"^(SCR|CMP|REQ|NOTE|NFR|ENT|EXT|JRN|PRM|Q|DP)-")

SUBDIRS = ("screens", "entities", "externals", "journeys", "design-pages")


def _walk_ids(node, acc: list[str]) -> None:
    """dict/list 를 재귀 순회하며 'id' 키의 스파인 ID 값을 수집(정의만)."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "id" and isinstance(v, str) and SPINE_RE.match(v):
                acc.append(v)
            else:
                _walk_ids(v, acc)
    elif isinstance(node, list):
        for item in node:
            _walk_ids(item, acc)


def scan_ids(root: Path) -> dict[str, list[str]]:
    """root(=model_repo 또는 foundation) 하위 YAML 의 정의 ID → [정의된 파일들] 매핑."""
    if yaml is None:
        return {}
    id_files: dict[str, list[str]] = {}
    for sub in SUBDIRS:
        d = root / sub
        if not d.exists():
            continue
        for fp in sorted(d.glob("*.yaml")):
            try:
                doc = yaml.safe_load(fp.read_text(encoding="utf-8"))
            except Exception:
                continue
            ids: list[str] = []
            _walk_ids(doc, ids)
            for i in ids:
                id_files.setdefault(i, []).append(fp.as_posix())
    return id_files


def find_global_dups(id_files: dict[str, list[str]]) -> dict[str, list[str]]:
    """같은 ID 가 2개 이상 파일(또는 같은 파일에 2회)에서 정의되면 중복."""
    return {i: fs for i, fs in id_files.items() if len(fs) > 1}


def load_manifest(manifest_path: Path) -> dict:
    if yaml is None or not manifest_path.exists():
        return {}
    try:
        return yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _max_seq(ids: list[str], prefix: str) -> int:
    """'PRM-0007' / 'Q-003' 형태 전역 카운터의 최대 순번."""
    mx = 0
    for i in ids:
        if i.startswith(prefix):
            m = re.search(r"(\d+)$", i)
            if m:
                mx = max(mx, int(m.group(1)))
    return mx


def observed_counters(id_files: dict[str, list[str]]) -> dict:
    ids = list(id_files.keys())
    return {"PRM_next": _max_seq(ids, "PRM-") + 1, "Q_next": _max_seq(ids, "Q-") + 1}


def check(root: Path, manifest_path: Path) -> dict:
    """전역 유일성(차단) + manifest 정합(경고) 판정."""
    id_files = scan_ids(root)
    dups = find_global_dups(id_files)
    manifest = load_manifest(manifest_path)

    warnings: list[str] = []
    # 카운터 드리프트: 관측 next > manifest 카운터면 경고
    obs = observed_counters(id_files)
    counters = (manifest.get("counters") or {})
    prm_m = (counters.get("PRM") if isinstance(counters.get("PRM"), int) else None)
    if prm_m is not None and obs["PRM_next"] > prm_m:
        warnings.append(f"PRM 카운터 드리프트: manifest={prm_m}, 관측 next={obs['PRM_next']}")
    q_m = (counters.get("Q") if isinstance(counters.get("Q"), int) else None)
    if q_m is not None and obs["Q_next"] > q_m:
        warnings.append(f"Q 카운터 드리프트: manifest={q_m}, 관측 next={obs['Q_next']}")

    # 레지스트리 커버리지: 정의된 SCR- 가 manifest.screens 에 등록됐는지
    registered = {s.get("id") for s in (manifest.get("screens") or []) if isinstance(s, dict)}
    defined_scr = {i for i in id_files if i.startswith("SCR-")}
    missing = sorted(defined_scr - registered)
    if missing:
        warnings.append("manifest.screens 미등록 화면: " + ", ".join(missing))

    return {
        "ok": not dups,
        "dups": dups,
        "warnings": warnings,
        "observed": obs,
        "id_count": len(id_files),
    }


def reconcile(root: Path, manifest_path: Path) -> dict:
    """관측값으로 manifest 카운터/screens 레지스트리를 재작성(명시 호출 전용)."""
    if yaml is None:
        raise RuntimeError("pyyaml 필요")
    id_files = scan_ids(root)
    manifest = load_manifest(manifest_path) or {"manifest_version": 1}
    obs = observed_counters(id_files)
    counters = manifest.setdefault("counters", {})
    counters["PRM"] = max(int(counters.get("PRM", 1) or 1), obs["PRM_next"])
    counters["Q"] = max(int(counters.get("Q", 1) or 1), obs["Q_next"])
    manifest_path.write_text(
        yaml.dump(manifest, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return {"counters": counters, "id_count": len(id_files)}


def _main(argv: list[str]) -> int:
    args = argv[1:]
    root = Path("model_repo")
    if "--root" in args:
        root = Path(args[args.index("--root") + 1])
    manifest_path = root / "link-manifest.yaml"

    if "--reconcile" in args:
        res = reconcile(root, manifest_path)
        print(f"[spine-ledger] reconcile 완료: PRM next={res['counters'].get('PRM')}, "
              f"Q next={res['counters'].get('Q')} ({res['id_count']} IDs)")
        return 0

    res = check(root, manifest_path)
    for w in res["warnings"]:
        print(f"[spine-ledger] ⚠ {w}", file=sys.stderr)
    if not res["ok"]:
        print(f"[spine-ledger] ❌ 전역 ID 중복 {len(res['dups'])}건 — 채번 충돌:", file=sys.stderr)
        for i, fs in res["dups"].items():
            print(f"    {i}: {', '.join(fs)}", file=sys.stderr)
        return 1
    print(f"[spine-ledger] ✅ 전역 유일성 OK ({res['id_count']} IDs, "
          f"{len(res['warnings'])} warning)")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
