<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  type ChartData,
  type ChartOptions,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

interface WeekData {
  label: string
  value: number
}

const props = withDefaults(defineProps<{
  data: WeekData[]
  title?: string
  color?: string
  height?: number
  yLabel?: string
}>(), {
  title: '주간 활동',
  color: '#00D9FF',
  height: 200,
  yLabel: '',
})

const chartData = computed<ChartData<'bar'>>(() => ({
  labels: props.data.map((d) => d.label),
  datasets: [
    {
      label: props.title,
      data: props.data.map((d) => d.value),
      backgroundColor: `${props.color}66`,
      borderColor: props.color,
      borderWidth: 2,
      borderRadius: 4,
    },
  ],
}))

const chartOptions = computed<ChartOptions<'bar'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    title: {
      display: !!props.title,
      text: props.title,
      color: '#96a3b8',
      font: { size: 13 },
    },
    tooltip: {
      callbacks: {
        label: (ctx) =>
          props.yLabel ? `${ctx.formattedValue} ${props.yLabel}` : ctx.formattedValue,
      },
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.05)' },
      ticks: { color: '#96a3b8', font: { size: 11 } },
    },
    y: {
      grid: { color: 'rgba(255,255,255,0.05)' },
      ticks: { color: '#96a3b8', font: { size: 11 } },
      beginAtZero: true,
    },
  },
}))
</script>

<template>
  <div class="w-full" :style="{ height: `${height}px` }">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>
