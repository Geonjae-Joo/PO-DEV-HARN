"""harness-core/render — ADR-002 결정론적 렌더 엔진.

screen model(YAML) / design page(YAML)를 순수 함수로 HTML 렌더한다.
같은 입력 → 바이트 동일 HTML(rendered-at 주석 줄 제외). 인라인 style·외부 CDN/폰트 금지.

공개 API는 engine 모듈에 있다:
  from engine import render_screen, render_designpage, compute_layout_hash, resolve_positions
"""
