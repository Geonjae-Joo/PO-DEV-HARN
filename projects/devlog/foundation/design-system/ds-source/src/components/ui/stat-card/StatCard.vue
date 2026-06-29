<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, TrendingDown, Minus } from 'lucide-vue-next'

interface Trend {
  value: number
  label?: string
}

const props = withDefaults(defineProps<{
  title: string
  value: string | number
  description?: string
  trend?: Trend
  icon?: object
  variant?: 'default' | 'accent'
}>(), {
  variant: 'default',
})

const trendIcon = computed(() => {
  if (!props.trend) return null
  if (props.trend.value > 0) return TrendingUp
  if (props.trend.value < 0) return TrendingDown
  return Minus
})

const trendClass = computed(() => {
  if (!props.trend) return ''
  if (props.trend.value > 0) return 'text-emerald-400'
  if (props.trend.value < 0) return 'text-destructive'
  return 'text-muted-foreground'
})

const trendLabel = computed(() => {
  if (!props.trend) return ''
  const sign = props.trend.value > 0 ? '+' : ''
  const pct = `${sign}${props.trend.value}%`
  return props.trend.label ? `${pct} ${props.trend.label}` : pct
})
</script>

<template>
  <Card :class="variant === 'accent' ? 'border-primary/30 bg-primary/5' : ''">
    <CardHeader class="flex flex-row items-center justify-between pb-2">
      <CardTitle class="text-sm font-medium text-muted-foreground">{{ title }}</CardTitle>
      <component
        v-if="icon"
        :is="icon"
        class="size-4 text-muted-foreground"
      />
    </CardHeader>
    <CardContent>
      <div class="text-2xl font-bold">{{ value }}</div>

      <div class="mt-1 flex items-center gap-1.5">
        <!-- Trend badge -->
        <div v-if="trend" class="flex items-center gap-0.5" :class="trendClass">
          <component :is="trendIcon" class="size-3.5" />
          <span class="text-xs font-medium">{{ trendLabel }}</span>
        </div>

        <span v-if="description" class="text-xs text-muted-foreground">{{ description }}</span>
      </div>
    </CardContent>
  </Card>
</template>
