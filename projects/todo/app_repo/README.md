# TodoFlow — 골든패스 앱

> PO-DEV 3-layer 하네스 골든패스 시연 앱. 로그인 + Todo 목록 + 진행상황 팝업.

## 빠른 시작

```bash
# 백엔드
cd backend
npm install
npm run db:push      # SQLite 스키마 적용
npm run db:seed      # 시드 데이터 (admin@todoflow.dev / password123)
npm run dev          # http://localhost:3001

# 프론트엔드 (별도 터미널)
cd frontend
npm install
npm run dev          # http://localhost:5173
```

## 테스트

```bash
cd backend && npm test
cd frontend && npm test
```

## 화면 구성

| 화면 | 경로 | 스펙 |
|---|---|---|
| 로그인 | `/login` | SCR-LOGIN (PACK-AUTH) |
| Todo 목록 | `/todos` | SCR-TODO-LIST (PACK-TODO) |
| 진행상황 팝업 | `/todos` (행 클릭) | SCR-PROGRESS (PACK-TODO) |

## 의사결정 기록

모든 결정은 `DECISIONS/DECISIONS.md` 참조.
