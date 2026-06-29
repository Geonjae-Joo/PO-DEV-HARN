<script setup lang="ts">
import { computed, ref } from 'vue'

interface Cell {
  date: string
  count: number
}

interface TooltipState {
  visible: boolean
  date: string
  count: number
  x: number
  y: number
}

const props = withDefaults(defineProps<{
  cells: Cell[]
  levelOf?: (count: number) => 0 | 1 | 2 | 3 | 4
}>(), {
  levelOf: (n: number) => {
    if (n === 0) return 0
    if (n <= 2) return 1
    if (n <= 5) return 2
    if (n <= 9) return 3
    return 4
  },
})

const COLS = 26
const ROWS = 7
const CELL = 13
const GAP = 2
const DOT = CELL - GAP

/* 색 강도 클래스 — 시안 계열 */
const levelClass = [
  'bg-muted/40',                        // 0 — 없음
  'bg-primary/20',                      // 1
  'bg-primary/45',                      // 2
  'bg-primary/70',                      // 3
  'bg-primary',                         // 4 — 최대
]

/* cells를 date → count map으로 */
const cellMap = computed(() => {
  const m: Record<string, number> = {}
  props.cells.forEach((c) => (m[c.date] = c.count))
  return m
})

/* 오늘 기준으로 26×7 날짜 그리드 생성 (열 = 주, 행 = 요일) */
const grid = computed<string[][]>(() => {
  const today = new Date()
  const result: string[][] = []
  for (let col = COLS - 1; col >= 0; col--) {
    const week: string[] = []
    for (let row = ROWS - 1; row >= 0; row--) {
      const d = new Date(today)
      d.setDate(today.getDate() - col * 7 - row)
      week.unshift(d.toISOString().slice(0, 10))
    }
    result.push(week)
  }
  return result
})

/* 툴팁 */
const tooltip = ref<TooltipState>({ visible: false, date: '', count: 0, x: 0, y: 0 })

function onEnter(e: MouseEvent, date: string) {
  const rect = (e.target as HTMLElement).getBoundingClientRect()
  tooltip.value = {
    visible: true,
    date,
    count: cellMap.value[date] ?? 0,
    x: rect.left + rect.width / 2,
    y: rect.top - 8,
  }
}

function onLeave() {
  tooltip.value.visible = false
}

function formatDate(iso: string) {
  const d = new Date(iso)
  return `${d.getMonth() + 1}월 ${d.getDate()}일`
}
</script>

<template>
  <div class="inline-flex flex-col gap-1 select-none">
    <!-- 잔디밭 그리드 -->
    <div class="flex gap-px">
      <div v-for="(week, ci) in grid" :key="ci" class="flex flex-col gap-px">
        <div
          v-for="date in week"
          :key="date"
          :style="{ width: `${DOT}px`, height: `${DOT}px` }"
          :class="['rounded-sm transition-opacity hover:opacity-80 cursor-default', levelClass[levelOf(cellMap[date] ?? 0)]]"
          @mouseenter="onEnter($event, date)"
          @mouseleave="onLeave"
        />
      </div>
    </div>

    <!-- 범례 -->
    <div class="flex items-center gap-1 self-end mt-1">
      <span class="text-xs text-muted-foreground">적음</span>
      <div
        v-for="(cls, i) in levelClass"
        :key="i"
        :class="['rounded-sm', cls]"
        :style="{ width: '10px', height: '10px' }"
      />
      <span class="text-xs text-muted-foreground">많음</span>
    </div>
  </div>

  <!-- 툴팁 (fixed position) -->
  <Teleport to="body">
    <div
      v-if="tooltip.visible"
      class="pointer-events-none fixed z-50 rounded bg-foreground px-2 py-1 text-xs text-background shadow"
      :style="{ left: `${tooltip.x}px`, top: `${tooltip.y}px`, transform: 'translate(-50%, -100%)' }"
    >
      {{ formatDate(tooltip.date) }} · {{ tooltip.count }}개
    </div>
  </Teleport>
</template>
