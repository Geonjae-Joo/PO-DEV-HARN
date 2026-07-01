# devlog_dev_plugin — ③ plugin-ai-web-dev 테스트용 샘플 프로젝트

> DevLog SRS(`../../DevLog_raw.md`)를 기반으로 만든 **③ AI-WEB-DEV 플러그인 테스트 픽스처**.
> ①(foundation)·②(model_repo) 산출물이 미리 준비되어 있어, **③를 사용하는 단계에서 바로 시작**할 수 있다.

## 빠른 시작

1. **[`TUTORIAL.md`](TUTORIAL.md)** — 부트스트랩 → Phase 0 → α → β → γ 의 step-by-step 가이드. **여기서 시작.**
2. 검증(픽스처가 ③ 게이트를 실제 통과하는지):
   ```bash
   python ../../packages/plugin-ai-web-dev/hooks/layout-hash-guard.py --root .
   # → PASS (3화면 × 2팩 layout_hash 일치)
   ```

## 준비된 것 (요약)

| 레이어 | 위치 | 내용 |
|---|---|---|
| ① foundation | `foundation/` | tech-stack(Next.js 14 풀스택)·ops-stack(Standalone+PM2)·SPEC-000/OPS-000·DS 허용집합·DP-MAIN·DS 렌더자산·VERSION |
| ② model_repo | `model_repo/` | confirmed 3화면(MAIN·POST-DETAIL·DASHBOARD)·ENT-POST·ENT-STUDY-LOG·JRN 2개·PACK-BLOG·PACK-STUDY (**실측 pin**) |
| ③ app_repo | `app_repo/` | **비어 있음 = 당신의 시작점** (Phase 0/α/β/γ가 채움) |

## 핵심 특징

- **runnable 픽스처**: screen model의 `pinned_contract.layout_hash`는 `pins.py`로 실제 계산한 값 → `layout-hash-guard`가 실제로 통과한다(placeholder 아님).
- **다중 팩 화면**: `SCR-MAIN`이 PACK-BLOG·PACK-STUDY 둘 다에 속한다(Phase α가 shell을 먼저 만드는 이유를 보여주는 실제 사례).
- **complexity:high 노트**: `NOTE-MAIN.001`·`NOTE-DASHBOARD.001`(KST 시각/잔디밭 날짜) → Phase β에서 bl-analyst subagent 트리거를 시연.

> 스택은 SRS COR-001(Next.js App Router 강제)을 따른다. DS 시각 레퍼런스는 Vue지만 화면 모델은 프레임워크 중립이며, ③가 allowlist 계약을 React로 구현한다(`foundation/design-system/ds-source/README.md`).
