<script setup lang="ts">
import { computed } from 'vue'
import { Button } from '@/components/ui/button'
import { Play, Pause, RotateCcw } from 'lucide-vue-next'

type TimerStatus = 'idle' | 'running' | 'paused' | 'done'

const props = withDefaults(defineProps<{
  targetSeconds?: number
  status?: TimerStatus
  elapsed?: number
}>(), {
  targetSeconds: 1500,
  status: 'idle',
  elapsed: 0,
})

const emit = defineEmits<{
  start: []
  pause: []
  reset: []
}>()

const RADIUS = 80
const STROKE = 8
const CIRCUMFERENCE = 2 * Math.PI * RADIUS
const VIEW = (RADIUS + STROKE) * 2

const progress = computed(() =>
  props.targetSeconds > 0
    ? Math.min(props.elapsed / props.targetSeconds, 1)
    : 0,
)

const dashOffset = computed(() => CIRCUMFERENCE * (1 - progress.value))

const remaining = computed(() => Math.max(props.targetSeconds - props.elapsed, 0))
const mm = computed(() => String(Math.floor(remaining.value / 60)).padStart(2, '0'))
const ss = computed(() => String(remaining.value % 60).padStart(2, '0'))

const statusLabel = computed(() => ({
  idle: '준비',
  running: '집중 중',
  paused: '일시정지',
  done: '완료!',
}[props.status]))

const statusColor = computed(() =>
  props.status === 'done' ? 'text-primary' : 'text-foreground',
)
</script>

<template>
  <div class="flex flex-col items-center gap-4">
    <!-- SVG 원형 게이지 -->
    <div class="relative">
      <svg
        :width="VIEW"
        :height="VIEW"
        :viewBox="`0 0 ${VIEW} ${VIEW}`"
        class="-rotate-90"
      >
        <!-- 배경 트랙 -->
        <circle
          :cx="VIEW / 2"
          :cy="VIEW / 2"
          :r="RADIUS"
          fill="none"
          class="stroke-muted"
          :stroke-width="STROKE"
        />
        <!-- 진행 아크 -->
        <circle
          :cx="VIEW / 2"
          :cy="VIEW / 2"
          :r="RADIUS"
          fill="none"
          class="stroke-primary transition-all duration-1000 ease-linear"
          :stroke-width="STROKE"
          stroke-linecap="round"
          :stroke-dasharray="CIRCUMFERENCE"
          :stroke-dashoffset="dashOffset"
        />
      </svg>

      <!-- 중앙 텍스트 -->
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <span class="text-4xl font-mono font-bold tabular-nums" :class="statusColor">
          {{ mm }}:{{ ss }}
        </span>
        <span class="text-xs text-muted-foreground mt-1">{{ statusLabel }}</span>
      </div>
    </div>

    <!-- 컨트롤 버튼 -->
    <div class="flex items-center gap-2">
      <Button
        v-if="status !== 'running'"
        variant="default"
        size="icon"
        @click="emit('start')"
        :disabled="status === 'done'"
      >
        <Play class="size-4" />
      </Button>
      <Button
        v-else
        variant="outline"
        size="icon"
        @click="emit('pause')"
      >
        <Pause class="size-4" />
      </Button>
      <Button variant="ghost" size="icon" @click="emit('reset')">
        <RotateCcw class="size-4" />
      </Button>
    </div>
  </div>
</template>
