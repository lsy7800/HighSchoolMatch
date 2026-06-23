<script setup>
import { computed } from 'vue'

// 通用折线趋势图(纯SVG, 无第三方库)。
// points: [{ year, value }]  (value 为 null 的年份跳过)
// invert: true 时数值越小画得越高(适合"位次": 越小越好)
const props = defineProps({
  points: { type: Array, default: () => [] },
  invert: { type: Boolean, default: false },
  color: { type: String, default: '#3b6fe0' },
  label: { type: String, default: '' },
})

const W = 280
const H = 90
const PAD_X = 28
const PAD_Y = 16

const valid = computed(() =>
  props.points
    .filter((p) => p.value != null && !isNaN(p.value))
    .slice()
    .sort((a, b) => a.year - b.year)
)

const geom = computed(() => {
  const pts = valid.value
  if (pts.length === 0) return null
  const values = pts.map((p) => p.value)
  let min = Math.min(...values)
  let max = Math.max(...values)
  if (min === max) { min -= 1; max += 1 } // 单点/全等时避免除零

  const xStep = pts.length > 1 ? (W - 2 * PAD_X) / (pts.length - 1) : 0
  const yOf = (v) => {
    const t = (v - min) / (max - min) // 0..1
    const tt = props.invert ? t : 1 - t // invert: 小值在上
    return PAD_Y + tt * (H - 2 * PAD_Y)
  }
  const coords = pts.map((p, i) => ({
    x: PAD_X + (pts.length > 1 ? i * xStep : (W - 2 * PAD_X) / 2),
    y: yOf(p.value),
    year: p.year,
    value: p.value,
  }))
  const line = coords.map((c, i) => `${i ? 'L' : 'M'}${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(' ')
  return { coords, line }
})
</script>

<template>
  <div class="trend">
    <div v-if="label" class="muted" style="margin-bottom:2px">{{ label }}</div>
    <svg v-if="geom" :viewBox="`0 0 ${W} ${H}`" class="trend-svg">
      <path :d="geom.line" fill="none" :stroke="color" stroke-width="2" />
      <g v-for="c in geom.coords" :key="c.year">
        <circle :cx="c.x" :cy="c.y" r="3" :fill="color" />
        <text :x="c.x" :y="H - 2" text-anchor="middle" class="trend-x">{{ c.year }}</text>
        <text :x="c.x" :y="c.y - 7" text-anchor="middle" class="trend-v">{{ c.value }}</text>
      </g>
    </svg>
    <div v-else class="muted">暂无数据</div>
  </div>
</template>

<style scoped>
.trend-svg { width: 100%; height: auto; display: block; }
.trend-x { font-size: 9px; fill: #8a909a; }
.trend-v { font-size: 9px; fill: #4a5057; }
</style>
