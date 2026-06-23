<script setup>
import { ref, onMounted, computed } from 'vue'
import { getYears, recommend } from '../api'
import SchoolSheet from '../components/SchoolSheet.vue'

const years = ref([])
const score = ref('')
const year = ref(null)
const loading = ref(false)
const error = ref('')
const result = ref(null)
const activeCode = ref(null)

const groups = computed(() => {
  if (!result.value) return []
  return [
    { key: 'reach', label: '冲', cls: 'reach', badge: 'badge-reach', items: result.value.reach },
    { key: 'stable', label: '稳', cls: 'stable', badge: 'badge-stable', items: result.value.stable },
    { key: 'safe', label: '保', cls: 'safe', badge: 'badge-safe', items: result.value.safe },
  ]
})

const scopeLabel = { city6: '市内六区', whole: '全市', suburb: '郊区' }

onMounted(async () => {
  try {
    years.value = await getYears()
    if (years.value.length) year.value = years.value[0]
  } catch {
    error.value = '无法连接服务，请稍后再试'
  }
})

async function submit() {
  error.value = ''
  const s = parseFloat(score.value)
  if (isNaN(s) || s < 0 || s > 900) {
    error.value = '请输入有效分数'
    return
  }
  loading.value = true
  result.value = null
  try {
    result.value = await recommend({ score: s, year: year.value })
  } catch (e) {
    error.value = e.response?.data?.detail || '查询失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <h1>中考志愿填报辅助</h1>
    <p class="muted">输入你的中考分数，按「位次」匹配可报高中（市内六区）</p>

    <div class="card">
      <div class="field" v-if="years.length > 1">
        <label>数据年份</label>
        <select v-model="year">
          <option v-for="y in years" :key="y" :value="y">{{ y }} 年</option>
        </select>
      </div>
      <div class="field">
        <label>中考总分</label>
        <input
          v-model="score"
          type="number"
          inputmode="decimal"
          placeholder="例如 720.5"
          @keyup.enter="submit"
        />
      </div>
      <button class="btn" :disabled="loading" @click="submit">
        {{ loading ? '匹配中…' : '开始匹配' }}
      </button>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <div v-if="result" class="card">
      <div>你的位次（{{ result.year }} 年）</div>
      <div style="display:flex;gap:24px;margin-top:8px">
        <div>
          <div class="muted">市内六区</div>
          <div style="font-size:1.3rem;font-weight:700">第 {{ result.rank_city6 }} 名</div>
        </div>
        <div>
          <div class="muted">全市</div>
          <div style="font-size:1.3rem;font-weight:700">第 {{ result.rank_whole }} 名</div>
        </div>
      </div>
      <p v-if="result.out_of_range" class="muted" style="margin-top:8px">
        ⚠ 分数超出一分档范围，已按边界估算
      </p>
    </div>

    <template v-if="result">
      <div v-for="g in groups" :key="g.key">
        <div class="group-title">
          <span class="badge" :class="g.badge">{{ g.label }}</span>
          <span>{{ g.items.length }} 所</span>
        </div>
        <p v-if="!g.items.length" class="muted">暂无匹配学校</p>
        <div
          v-for="s in g.items"
          :key="s.code + s.scope"
          class="school-item"
          :class="g.cls"
          @click="activeCode = s.code"
        >
          <div>
            <div class="name">{{ s.name }}</div>
            <div class="meta">
              {{ scopeLabel[s.scope] }} · {{ s.type || '—' }} ·
              {{ s.location_district || '' }}
            </div>
          </div>
          <div class="rank">
            <div>录取位次 {{ s.school_rank }}</div>
            <div class="muted">最低分 {{ s.min_score ?? '—' }}</div>
          </div>
        </div>
      </div>
    </template>

    <p class="disclaimer">
      本结果基于历年录取位次估算，仅供参考。<br />
      志愿填报请以官方招生政策与正式发布数据为准。
    </p>

    <SchoolSheet v-if="activeCode" :code="activeCode" @close="activeCode = null" />
  </div>
</template>
