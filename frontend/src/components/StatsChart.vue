<script setup lang="ts">
/**
 * 统计图表组件
 *
 * 使用 ECharts 展示学习行为统计数据
 */
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import type { StatsResponse } from '@/types'

const props = defineProps<{
  stats: StatsResponse | null
}>()

const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null

/**
 * 格式化秒数为可读字符串
 */
function formatTime(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分${Math.round(seconds % 60)}秒`
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}时${m}分`
}

function initChart() {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value, undefined, {
    renderer: 'canvas',
  })

  updateChart()
}

function updateChart() {
  if (!chartInstance || !props.stats) return

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#0f1424',
      borderColor: 'rgba(0, 212, 255, 0.2)',
      textStyle: {
        fontFamily: '"JetBrains Mono", monospace',
        fontSize: 12,
        color: '#e8ecf4',
      },
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '55%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 4,
          borderColor: '#050810',
          borderWidth: 2,
        },
        label: {
          show: true,
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: 11,
          color: '#8892a8',
          formatter: '{b}\n{d}%',
        },
        labelLine: {
          lineStyle: { color: 'rgba(0, 212, 255, 0.2)' },
        },
        data: [
          {
            value: Math.round(props.stats.focusDuration),
            name: '专注',
            itemStyle: { color: '#00e676' },
          },
          {
            value: Math.round(props.stats.distractedDuration),
            name: '分心',
            itemStyle: { color: '#ff5252' },
          },
          {
            value: Math.round(props.stats.lowEfficiencyDuration),
            name: '低效',
            itemStyle: { color: '#ff9100' },
          },
          {
            value: Math.round(props.stats.awayDuration),
            name: '离开',
            itemStyle: { color: '#546e7a' },
          },
        ].filter(d => d.value > 0),
      },
    ],
  }

  chartInstance.setOption(option)
}

watch(() => props.stats, updateChart, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', () => chartInstance?.resize())
})

onUnmounted(() => {
  chartInstance?.dispose()
})
</script>

<template>
  <div class="card">
    <div class="card-header">
      <span class="card-title">学习统计</span>
      <span v-if="stats" class="data-readout">
        专注率 <span class="value">{{ stats.focusRate }}%</span>
      </span>
    </div>

    <!-- 统计数值网格 -->
    <div v-if="stats" class="stats-grid">
      <div class="stat-card">
        <span class="stat-label">总时长</span>
        <span class="stat-value text-primary">{{ formatTime(stats.totalDuration) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">专注</span>
        <span class="stat-value text-success">{{ formatTime(stats.focusDuration) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">分心次数</span>
        <span class="stat-value text-error">{{ stats.distractedCount }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">手机使用</span>
        <span class="stat-value text-error">{{ formatTime(stats.phoneUsageDuration) }}</span>
      </div>
    </div>

    <!-- ECharts 饼图 -->
    <div ref="chartRef" class="chart-container" />

    <!-- 无数据状态 -->
    <div v-if="!stats" class="no-data text-secondary">
      等待数据采集...
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4);
  background: var(--color-neutral-50);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.stat-card:hover {
  border-color: var(--color-neutral-300);
  transform: translateY(-2px);
  box-shadow: var(--shadow-1);
}

.stat-label {
  font-family: var(--font-artistic);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  color: var(--color-neutral-500);
  letter-spacing: 0.05em;
}

.stat-value {
  font-family: var(--font-data);
  font-size: var(--text-xl);
  font-weight: 600;
  line-height: 1;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.chart-container {
  width: 100%;
  height: 220px;
}

.no-data {
  text-align: center;
  padding: var(--space-8);
}
</style>
