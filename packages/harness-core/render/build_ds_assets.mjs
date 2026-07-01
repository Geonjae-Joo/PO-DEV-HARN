// harness-core/render/build_ds_assets.mjs
// ① PREREQUISITE 자산 빌더 — 프로젝트 시작 시 1회 실행(ds-bootstrap Phase 9).
//
// 입력  : projects/<id>/foundation/design-system/ds-source/  (설치된 DS)
//          ds-allowlist.md (대상 컴포넌트 집합)
//          [선택] foundation/design-system/ds-fixtures.recipe.json (컴포넌트별 props/slot/import 오버라이드)
// 출력  : foundation/design-system/ds-compiled.css   (실제 DS CSS: 토큰 + 컴파일된 유틸리티)
//          foundation/design-system/ds-fixtures.json  (ref → 기본상태 정적 마크업)
//
// 설계: 프레임워크 특화 작업(Tailwind 컴파일·Vue SSR)을 이 1회 빌드로 격리한다.
//       결과물은 프레임워크 중립 정적 파일이고, Python 렌더 엔진은 이 둘만 읽는다(결정적).
//       컴파일은 렌더 시점이 아니라 여기서 1회 — 그래야 render_hash 가 안정적이다.
//
// 사용: node build_ds_assets.mjs --root projects/<id>
//
// 한계: Tailwind 기반 DS(shadcn-vue 등)는 정확 컴파일. 비-Tailwind DS 는 raw CSS 병합으로 폴백.
//       Vue SSR 가능한 컴포넌트만 fixture 생성 — portal/클라이언트 전용(Dialog 등)은 스킵(엔진이 와이어프레임 폴백).

import { createRequire } from 'node:module'
import { readFileSync, writeFileSync, existsSync, readdirSync } from 'node:fs'
import path from 'node:path'

// ── args ──────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2)
const rootIdx = args.indexOf('--root')
if (rootIdx === -1) {
  console.error('[ds-assets] --root projects/<id> 필요')
  process.exit(2)
}
const PROJECT = path.resolve(args[rootIdx + 1])
const DS_DIR = path.join(PROJECT, 'foundation', 'design-system')
const DS_SOURCE = path.join(DS_DIR, 'ds-source')
const ALLOWLIST = path.join(DS_DIR, 'ds-allowlist.md')
const RECIPE = path.join(DS_DIR, 'ds-fixtures.recipe.json')
const OUT_CSS = path.join(DS_DIR, 'ds-compiled.css')
const OUT_FIXTURES = path.join(DS_DIR, 'ds-fixtures.json')

if (!existsSync(DS_SOURCE)) {
  console.error(`[ds-assets] ds-source 없음: ${DS_SOURCE}`)
  process.exit(1)
}

const require = createRequire(path.join(DS_SOURCE, 'package.json'))
async function tryLoad(name) {
  try { return require(name) } catch {
    try { return await import(require.resolve(name)) } catch { return null }
  }
}

// ── 1) 대상 컴포넌트(allowlist 헤딩) ────────────────────────────────────────────
function allowlistNames() {
  if (!existsSync(ALLOWLIST)) return []
  const text = readFileSync(ALLOWLIST, 'utf8')
  const names = []
  for (const line of text.split(/\r?\n/)) {
    const m = /^##\s+(\w+)/.exec(line)
    if (m) names.push(m[1])
  }
  return names
}
const pascalToKebab = (s) => s.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase()

// ── 2) Tailwind 컴파일 (있으면) / raw CSS 병합 (폴백) ────────────────────────────
function findTokensCss() {
  // @import "tailwindcss" / @theme / @tailwind 를 가진 CSS 우선, 없으면 알려진 경로
  const cssFiles = []
  const walk = (dir) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      if (e.name === 'node_modules') continue
      const p = path.join(dir, e.name)
      if (e.isDirectory()) walk(p)
      else if (e.name.endsWith('.css')) cssFiles.push(p)
    }
  }
  const src = path.join(DS_SOURCE, 'src')
  if (existsSync(src)) walk(src)
  cssFiles.sort()
  for (const f of cssFiles) {
    const t = readFileSync(f, 'utf8')
    if (/@import\s+["']tailwindcss["']|@tailwind\b|@theme\b/.test(t)) return f
  }
  for (const cand of ['src/assets/tokens.css', 'src/tokens.css', 'src/styles/main.css']) {
    const p = path.join(DS_SOURCE, cand)
    if (existsSync(p)) return p
  }
  return cssFiles[0] || null
}

async function buildCss() {
  const tokensCss = findTokensCss()
  const tw = await tryLoad('@tailwindcss/node')
  const oxide = await tryLoad('@tailwindcss/oxide')
  const compile = tw?.compile || tw?.default?.compile
  const Scanner = oxide?.Scanner || oxide?.default?.Scanner

  if (tokensCss && compile && Scanner) {
    const scanner = new Scanner({
      sources: [{ base: path.join(DS_SOURCE, 'src'), pattern: '**/*.{vue,ts,js,jsx,tsx}', negated: false }],
    })
    const candidates = scanner.scan()
    const compiled = await compile(readFileSync(tokensCss, 'utf8'), {
      base: DS_SOURCE,
      onDependency: () => {},
    })
    const css = compiled.build(candidates)
    console.error(`[ds-assets] CSS: Tailwind 컴파일 (${candidates.length} 후보, ${css.length}B) ← ${path.relative(DS_SOURCE, tokensCss)}`)
    return css
  }

  // 폴백: ds-source 의 모든 CSS 병합(비-Tailwind DS — CSS 변수 DS 등)
  const parts = []
  const walk = (dir) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      if (e.name === 'node_modules') continue
      const p = path.join(dir, e.name)
      if (e.isDirectory()) walk(p)
      else if (e.name.endsWith('.css')) parts.push(`/* ${path.relative(DS_SOURCE, p)} */\n` + readFileSync(p, 'utf8'))
    }
  }
  const src = path.join(DS_SOURCE, 'src')
  if (existsSync(src)) walk(src)
  console.error(`[ds-assets] CSS: Tailwind 미감지 → raw CSS 병합 폴백 (${parts.length} 파일)`)
  return parts.join('\n\n')
}

// ── 3) Vue SSR fixtures ─────────────────────────────────────────────────────────
function cleanSSR(html) {
  // Vue SSR 프래그먼트/앵커 주석 제거 → 정적 마크업
  return html.replace(/<!--[\[\]]?-->/g, '').trim()
}

async function buildFixtures(names) {
  const vite = await tryLoad('vite')
  const vueSR = await tryLoad('vue/server-renderer')
  const vue = await tryLoad('vue')
  const createServer = vite?.createServer || vite?.default?.createServer
  const renderToString = vueSR?.renderToString || vueSR?.default?.renderToString
  const createSSRApp = vue?.createSSRApp || vue?.default?.createSSRApp
  const h = vue?.h || vue?.default?.h

  if (!createServer || !renderToString || !createSSRApp) {
    console.error('[ds-assets] Vue SSR toolchain 없음 → fixtures 생략(엔진 와이어프레임 폴백)')
    return {}
  }

  const recipe = existsSync(RECIPE) ? JSON.parse(readFileSync(RECIPE, 'utf8')) : {}
  const viteConfig = path.join(DS_SOURCE, 'vite.config.ts')
  let server
  try {
    server = await createServer({
      root: DS_SOURCE,
      configFile: existsSync(viteConfig) ? viteConfig : path.join(DS_SOURCE, 'vite.config.js'),
      server: { middlewareMode: true },
      appType: 'custom',
      logLevel: 'silent',
    })
  } catch (e) {
    // 비-Vue DS(React 등)·미완성 toolchain → Vue SSR 불가. fixtures 생략(엔진 와이어프레임 폴백).
    console.error(`[ds-assets] Vue SSR 서버 기동 실패 → fixtures 생략 (${String(e.message || e).split('\n')[0].slice(0, 80)})`)
    return {}
  }

  const LABEL = '{label}'   // 엔진이 실제 라벨로 치환
  const fixtures = {}
  let ok = 0, skip = 0
  for (const name of names) {
    const r = recipe[name] || {}
    const kebab = r.import ? null : pascalToKebab(name)
    const importPath = r.import || `/src/components/ui/${kebab}/index.ts`
    const exportName = r.export || name
    const props = r.props || {}
    const slot = r.slot === null ? null : (r.slot ?? LABEL)
    // ds-source 에 컴포넌트가 없으면 스킵
    if (!r.import) {
      const idxTs = path.join(DS_SOURCE, 'src', 'components', 'ui', kebab, 'index.ts')
      if (!existsSync(idxTs)) { skip++; continue }
    }
    try {
      const mod = await server.ssrLoadModule(importPath)
      const Comp = mod[exportName] || mod.default
      if (!Comp) { skip++; continue }
      const app = createSSRApp({ render: () => h(Comp, props, slot != null ? { default: () => slot } : undefined) })
      const html = cleanSSR(await renderToString(app))
      if (!html) { skip++; continue }
      fixtures[name] = { html }
      ok++
    } catch (e) {
      skip++
      console.error(`[ds-assets]   skip ${name}: ${String(e.message || e).split('\n')[0].slice(0, 80)}`)
    }
  }
  await server.close()
  console.error(`[ds-assets] fixtures: ${ok}개 생성, ${skip}개 스킵(폴백)`)
  return fixtures
}

// ── main ────────────────────────────────────────────────────────────────────────
const names = allowlistNames()
console.error(`[ds-assets] allowlist 컴포넌트 ${names.length}개`)

const css = await buildCss()
writeFileSync(OUT_CSS, css, 'utf8')
console.error(`[ds-assets] ✅ ${path.relative(PROJECT, OUT_CSS)}`)

const fixtures = await buildFixtures(names)
// 결정적 출력: 키 정렬, 2-space JSON
const sorted = {}
for (const k of Object.keys(fixtures).sort()) sorted[k] = fixtures[k]
writeFileSync(OUT_FIXTURES, JSON.stringify(sorted, null, 2) + '\n', 'utf8')
console.error(`[ds-assets] ✅ ${path.relative(PROJECT, OUT_FIXTURES)}`)
