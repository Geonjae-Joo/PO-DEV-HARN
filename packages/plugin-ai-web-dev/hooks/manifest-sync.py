#!/usr/bin/env python3
"""
Hook: manifest-sync.py
트리거: commit 이후 (post-commit)
목적:  ②의 spec 팩(model_repo/specs)을 app_repo/specs/ 와 동기화한다.
       - model_repo/specs/PACK-*/spec-pack.yaml → app_repo/specs/PACK-*/spec-pack.yaml 반영
       - Phase α 이후 생성된 shell 경로를 screens[].shell_ref 에 갱신 (실존 파일만)
경로: 3-Tier 신구조 기준(②가 model_repo/specs 에 발행 → ③가 app_repo/specs 로 동기화).
      cwd = projects/<id>/ 로 가정. 다른 위치는 HARNESS_SPEC_PACK_DIR 로 덮어쓴다.
종료코드: 0 = 성공(비차단 — post-commit이므로 실패해도 commit은 유지)
정책: README(③) Phase α/β, ②의 link-manifest
"""

import os
import sys
import shutil
from pathlib import Path

import yaml


def _project_root() -> Path:
    """projects/<id> 루트를 cwd 기준으로 해석한다(cwd 가정에 의존하지 않음).
    - 설치된 git 훅(post-commit): git 은 app_repo 저장소 루트에서 실행 → cwd=app_repo →
      model_repo 는 형제(..) 에 있다 → root='..'.
    - 프로젝트 루트에서 수동 실행: cwd=projects/<id> → root='.'.
    (이전에는 cwd=projects/<id> 만 가정해 훅 실행 시 model_repo/specs 를 못 찾고 SKIP 했다.)
    """
    for cand in (Path("."), Path("..")):
        if (cand / "model_repo").is_dir() or (cand / "app_repo").is_dir():
            return cand
    return Path(".")


_ROOT = _project_root()
# HARNESS_SPEC_PACK_DIR 가 있으면 그대로(절대/명시 경로), 없으면 해석된 루트 기준.
SRC = Path(os.environ["HARNESS_SPEC_PACK_DIR"]) if os.environ.get("HARNESS_SPEC_PACK_DIR") else _ROOT / "model_repo" / "specs"
DST = _ROOT / "app_repo" / "specs"

# 프론트엔드 pages 디렉터리·shell 확장자는 ①의 tech-stack.md 스택에 따른다(고정값 아님).
# 다른 스택은 환경변수로 덮어쓴다: HARNESS_PAGES_DIR, HARNESS_SHELL_EXT(쉼표구분).
PAGES_DIR = Path(os.environ["HARNESS_PAGES_DIR"]) if os.environ.get("HARNESS_PAGES_DIR") else _ROOT / "app_repo" / "frontend" / "src" / "pages"
DEFAULT_SHELL_EXT = (".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte")


def shell_exts() -> tuple:
    extra = os.environ.get("HARNESS_SHELL_EXT", "")
    extra_list = tuple(e.strip() for e in extra.split(",") if e.strip())
    return (extra_list + DEFAULT_SHELL_EXT) if extra_list else DEFAULT_SHELL_EXT


def scr_to_pascal(scr_id: str) -> str:
    """SCR-ORDER-LIST → OrderList (pages 디렉터리 컴포넌트명)."""
    body = scr_id[4:] if scr_id.startswith("SCR-") else scr_id
    return "".join(part.capitalize() for part in body.split("-") if part)


def resolve_shell_ref(scr_id: str) -> str | None:
    """Phase α가 생성한 shell 파일이 실존하면 그 경로를 반환, 없으면 None.
    프레임워크별 확장자(.tsx/.vue/.svelte 등)와 'index' 또는 동명 파일을 모두 탐색."""
    name = scr_to_pascal(scr_id)
    for ext in shell_exts():
        for cand in (PAGES_DIR / name / f"index{ext}", PAGES_DIR / f"{name}{ext}"):
            if cand.exists():
                # 계약에는 프로젝트 루트 상대 경로(canonical)로 저장한다.
                # (cwd=app_repo 로 훅이 돌면 _ROOT='..' 라 cand 가 '../app_repo/...' 가 되는데,
                #  그 cwd-상대 prefix 를 벗겨 'app_repo/...' 로 정규화한다.)
                try:
                    return cand.relative_to(_ROOT).as_posix()
                except ValueError:
                    return cand.as_posix()
    return None


def update_shell_refs(spec_path: Path) -> int:
    """동기화된 spec-pack.yaml의 screens[].shell_ref를 실존 shell 경로로 갱신."""
    try:
        doc = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except Exception:
        return 0
    if not isinstance(doc, dict):
        return 0
    changed = 0
    for screen in (doc.get("screens") or []):
        if not isinstance(screen, dict):
            continue
        scr_id = screen.get("id")
        if not scr_id:
            continue
        shell = resolve_shell_ref(str(scr_id))
        if shell and screen.get("shell_ref") != shell:
            screen["shell_ref"] = shell
            changed += 1
    if changed:
        spec_path.write_text(
            yaml.dump(doc, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
    return changed


def sync_packs() -> int:
    if not SRC.exists():
        print(f"[manifest-sync] SKIP: {SRC} 없음.")
        return 0
    DST.mkdir(parents=True, exist_ok=True)
    file_count = 0
    shell_count = 0
    for pack in sorted(SRC.glob("PACK-*")):
        if not pack.is_dir():
            continue
        target = DST / pack.name
        target.mkdir(parents=True, exist_ok=True)
        for f in pack.glob("*"):
            if f.is_file():
                shutil.copy2(f, target / f.name)
                file_count += 1
        spec_yaml = target / "spec-pack.yaml"
        if spec_yaml.exists():
            shell_count += update_shell_refs(spec_yaml)
    print(f"[manifest-sync] {file_count}개 파일 동기화, shell_ref {shell_count}건 갱신 (→ {DST}).")
    return 0


def main() -> int:
    try:
        return sync_packs()
    except Exception as e:
        # post-commit이므로 commit을 되돌리지 않는다. 경고만.
        print(f"[manifest-sync] WARN: 동기화 중 오류: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
