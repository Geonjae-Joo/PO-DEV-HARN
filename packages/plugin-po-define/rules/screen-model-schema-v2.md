<!-- MOVED(R1, ADR-001 D2-a) — 단일 출처는 harness-core 입니다. 이 파일은 redirect stub. -->

# Screen Model Schema v2 — 이동됨 (MOVED)

> **이 파일은 더 이상 원본이 아닙니다.**
> screen-model-schema-v2 의 단일 출처(single source of truth)는 아래로 이동했습니다:
>
> **→ `packages/harness-core/rules/screen-model-schema-v2.md`**

## 왜 이동했나 (ADR-001 R1 / D2-a)

이 스키마는 ②(po-define)만의 자산이 아니라 **①(prerequisite)과 ②가 함께 지키는 교차 계약**입니다.
①의 `design-page-builder`가 만드는 `DP-*` 템플릿을 ②의 `SCR-*` 인스턴스가 `from_template`으로
상속하기 때문에, DP와 SCR은 §7의 동일한 `layout` 스키마를 공유합니다.

따라서 constitution·spine-ids·ds-closure 와 동일하게 **`harness-core/rules/` 단일 출처**에 둡니다.
내용을 양쪽에 두면 drift가 생기므로, 이 파일에는 본문을 두지 않고 포인터만 남깁니다.

## 참조 갱신 안내

- ① `design-page-builder/SKILL.md` supporting-files → `../../../harness-core/rules/screen-model-schema-v2.md`
- ② `layout-recommend/SKILL.md` supporting-files → `../../../harness-core/rules/screen-model-schema-v2.md`
- 새 코드/문서는 harness-core 경로를 직접 참조하세요.
