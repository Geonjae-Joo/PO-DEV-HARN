# DECISIONS — 스택 결정 변경 이력 (Decision Log)

> `tech-stack.md`·`ops-stack.md`의 결정이 **바뀔 때마다** 한 줄씩 append한다.
> 결정의 *현재 값*은 각 stack 파일이 단일 출처이며, 이 파일은 *왜·언제 바뀌었는지*의 이력만 남긴다.
> `foundation/VERSION` 을 +1 하는 ① 수정과 짝을 이룬다(재현성·전파).

| 날짜 | 대상 | 변경 | 사유 | foundation VERSION |
|---|---|---|---|---|
| 2026-06-19 | tech-stack / ops-stack | 초기 확정 (백엔드 Spring Boot / 프론트 React+Vite+TS+Tailwind+shadcn/ui) | 프로젝트 착수 baseline | 1 |

<!--
추가 형식 예:
| 2026-07-02 | tech-stack | 프론트 상태관리 Redux → Zustand | 보일러플레이트 축소·번들 절감 | 2 |
| 2026-07-10 | ops-stack | 배포 타깃 Docker → k8s | 오토스케일 요건 | 3 |
-->
