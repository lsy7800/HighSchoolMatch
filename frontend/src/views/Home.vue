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

const totalMatches = computed(() =>
  result.value ? result.value.reach.length + result.value.stable.length + result.value.safe.length : 0
)

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
    <p class="muted">输入你的中考分数，按「位次」匹配可报高中（面向市内六区考生）</p>

    <details class="card help">
      <summary>什么是「位次法」？为什么不直接比分数？</summary>
      <div class="help-body">
        <p>每年中考题目难易不同，<strong>同样的分数对应的名次会变</strong>，所以拿今年的分数直接比往年的录取分并不准。</p>
        <p>更稳的做法是看<strong>位次（名次）</strong>：用「一分档」把你的分数换算成全市/市内六区的名次，再和各高中往年的录取名次比较。</p>
        <p>结果分三档：<span class="badge badge-reach">冲</span> 够一够、<span class="badge badge-stable">稳</span> 较稳妥、<span class="badge badge-safe">保</span> 兜底。</p>
      </div>
    </details>

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

      <div v-if="result.equiv_score_city6 != null" class="equiv">
        <span v-if="result.ref_year !== result.year">
          按 {{ result.ref_year }} 年标准，约相当于
          <strong>{{ result.equiv_score_city6 }}</strong> 分（市内六区口径）
        </span>
        <span v-else>
          等位分：市内六区 <strong>{{ result.equiv_score_city6 }}</strong> /
          全市 <strong>{{ result.equiv_score_whole }}</strong> 分
        </span>
        <span class="muted">　学校录取最低分按此口径对比</span>
      </div>

      <p v-if="result.out_of_range" class="muted" style="margin-top:8px">
        ⚠ 分数超出一分档范围，已按边界估算
      </p>
    </div>

    <template v-if="result">
      <div v-if="totalMatches === 0" class="card muted">
        没有匹配到合适的学校。可能分数过高或过低、超出现有学校的录取范围；可在管理后台调整阈值后再试。
      </div>
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
      <template v-if="result">
        本结果基于 {{ result.ref_year }} 年录取数据与一分档，按位次估算，<strong>仅供参考</strong>。<br />
      </template>
      <template v-else>
        本工具结果基于历年录取位次估算，仅供参考。<br />
      </template>
      录取受招生计划、政策、报考人数等多种因素影响，实际结果可能与估算不同。<br />
      志愿填报请以教育考试院等官方渠道发布的正式信息为准。
    </p>

    <SchoolSheet v-if="activeCode" :code="activeCode" @close="activeCode = null" />
  </div>
</template>
