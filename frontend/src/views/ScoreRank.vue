<script setup>
import { ref, onMounted, computed } from 'vue'
import { getScoreRank, getYears } from '../api'

const years = ref([])
const year = ref(null)
const rows = ref([])
const loading = ref(false)
const q = ref('')
const allYears = ref([])

onMounted(async () => {
  try {
    allYears.value = await getYears()
    if (allYears.value.length) {
      year.value = allYears.value[0]
      await load()
    }
  } catch {}
})

async function load() {
  if (!year.value) return
  loading.value = true
  try {
    const data = await getScoreRank(year.value)
    rows.value = data.rows
  } finally {
    loading.value = false
  }
}

const filtered = computed(() => {
  if (!q.value) return rows.value
  const n = Number(q.value)
  if (isNaN(n)) return rows.value
  // 滚到目标分数行, 高亮该行及附近
  return rows.value
})

function rowClass(row) {
  if (!q.value) return ''
  const n = Number(q.value)
  return !isNaN(n) && row.score === n ? 'highlight-row' : ''
}

function scrollToScore() {
  const n = Number(q.value)
  if (isNaN(n) || !rows.value.length) return
  const el = document.getElementById(`score-${n}`)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
</script>

<template>
  <div>
    <section class="hero hero-sm">
      <div class="hero-inner">
        <h1>一分一段表</h1>
        <p>查看全市与市内六区的分数段累计人数分布</p>
      </div>
    </section>

    <div class="page">
      <el-card shadow="never" style="margin-bottom:16px">
        <div class="rank-toolbar">
          <div>
            <span class="muted">数据年份：</span>
            <el-select v-model="year" style="width:120px" @change="load">
              <el-option v-for="y in allYears" :key="y" :label="`${y} 年`" :value="y" />
            </el-select>
          </div>
          <div class="rank-search">
            <el-input v-model="q" placeholder="搜索分数" style="width:130px" clearable @keyup.enter="scrollToScore" />
            <el-button type="primary" @click="scrollToScore" :icon="'Search'">定位</el-button>
          </div>
        </div>
      </el-card>

      <p class="muted" v-if="rows.length">共 {{ rows.length }} 个分数档，显示 780 → 500 分</p>

      <el-table
        :data="filtered"
        v-loading="loading"
        border
        stripe
        size="small"
        :row-class-name="({row}) => rowClass(row)"
        :highlight-current-row="false"
        max-height="70vh"
      >
        <el-table-column prop="score" label="分数" width="80" sortable />
        <el-table-column prop="cum_whole" label="全市累计（位次）" />
        <el-table-column prop="cum_city6" label="市内六区累计（位次）" />
        <el-table-column prop="band_whole" label="全市该分人数" />
        <el-table-column prop="band_city6" label="市内六区该分人数" />
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.rank-toolbar { display: flex; gap: 16px; justify-content: space-between; align-items: center; flex-wrap: wrap; }
.rank-search { display: flex; gap: 6px; align-items: center; }
:deep(.highlight-row) { background: var(--el-color-warning-light-8) !important; }
</style>
