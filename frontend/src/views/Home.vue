<script setup>
import { ref, onMounted, computed } from 'vue'
import { getYears, recommend } from '../api'
import SchoolSheet from '../components/SchoolSheet.vue'
import SchoolCard from '../components/SchoolCard.vue'

const years = ref([])
const score = ref('')
const year = ref(null)
const loading = ref(false)
const error = ref('')
const result = ref(null)

const activeCode = ref(null)
const sheetVisible = ref(false)
function openSchool(code) {
  activeCode.value = code
  sheetVisible.value = true
}

const groups = computed(() => {
  if (!result.value) return []
  return [
    { key: 'reach', label: '冲', type: 'warning', items: result.value.reach },
    { key: 'stable', label: '稳', type: 'success', items: result.value.stable },
    { key: 'safe', label: '保', type: 'primary', items: result.value.safe },
  ]
})

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
  <div>
    <!-- Hero -->
    <section class="hero">
      <div class="hero-inner">
        <h1>智能匹配你的中考志愿</h1>
        <p>输入中考分数，用「位次法」一键找到可冲、可稳、可保的高中（面向市内六区考生）</p>
      </div>
    </section>

    <div class="page">
    <div class="query-box">
      <el-collapse class="help">
        <el-collapse-item title="什么是「位次法」？为什么不直接比分数？" name="1">
          <p>每年中考题目难易不同，<b>同样的分数对应的名次会变</b>，所以拿今年的分数直接比往年的录取分并不准。</p>
          <p>更稳的做法是看<b>位次（名次）</b>：用「一分档」把分数换算成全市/市内六区的名次，再和各高中往年录取名次比较。</p>
          <p>
            结果分三档：
            <el-tag type="warning" size="small" effect="dark">冲</el-tag> 够一够、
            <el-tag type="success" size="small" effect="dark">稳</el-tag> 较稳妥、
            <el-tag type="primary" size="small" effect="dark">保</el-tag> 兜底。
          </p>
        </el-collapse-item>
      </el-collapse>

      <el-card class="query-card" shadow="never">
        <el-form label-position="top" @submit.prevent>
          <el-form-item v-if="years.length > 1" label="数据年份">
            <el-select v-model="year" style="width:100%">
              <el-option v-for="y in years" :key="y" :label="`${y} 年`" :value="y" />
            </el-select>
          </el-form-item>
          <el-form-item label="中考总分">
            <el-input
              v-model="score"
              type="number"
              placeholder="例如 720.5"
              size="large"
              clearable
              @keyup.enter="submit"
            />
          </el-form-item>
          <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="submit">
            开始匹配
          </el-button>
          <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon style="margin-top:12px" />
        </el-form>
      </el-card>

      <el-card v-if="result" class="rank-card" shadow="never">
        <div class="rank-row">
          <el-statistic title="市内六区位次" :value="result.rank_city6" />
          <el-statistic title="全市位次" :value="result.rank_whole" />
        </div>
        <el-alert
          v-if="result.equiv_score_city6 != null"
          type="info"
          :closable="false"
          show-icon
          style="margin-top:12px"
        >
          <template v-if="result.ref_year !== result.year">
            按 {{ result.ref_year }} 年标准，约相当于 <b>{{ result.equiv_score_city6 }}</b> 分（市内六区口径）
          </template>
          <template v-else>
            等位分：市内六区 <b>{{ result.equiv_score_city6 }}</b> / 全市 <b>{{ result.equiv_score_whole }}</b> 分；学校录取最低分按此口径对比
          </template>
        </el-alert>
        <el-alert
          v-if="result.out_of_range"
          title="分数超出一分档范围，已按边界估算"
          type="warning"
          :closable="false"
          show-icon
          style="margin-top:8px"
        />
      </el-card>
    </div>

    <!-- 结果 -->
    <template v-if="result">
      <!-- 低分模式 -->
      <template v-if="result.low_score_mode">
        <el-alert type="warning" :closable="false" show-icon style="margin:16px 0">
          你的分数低于本档数据的最低分，已不区分「冲/稳/保」。下列学校按<b>历年录取门槛由低到高</b>排序，越靠前越容易录取。
        </el-alert>
        <div class="group-title">
          可考虑的学校
          <el-tag type="info" size="small">{{ result.reachable.length }} 所（门槛低→高）</el-tag>
        </div>
        <div class="school-grid">
          <SchoolCard
            v-for="s in result.reachable"
            :key="s.code + s.scope"
            :s="s"
            type="safe"
            @open="openSchool(s.code)"
          />
        </div>
      </template>

      <!-- 正常模式 -->
      <template v-else>
        <el-empty v-if="totalMatches === 0" description="没有匹配到合适的学校，可能分数过高/过低，或可在后台调整阈值后再试" />
        <div v-for="g in groups" :key="g.key">
          <div class="group-title">
            <el-tag :type="g.type" effect="dark">{{ g.label }}</el-tag>
            <span class="muted">{{ g.items.length }} 所</span>
          </div>
          <el-empty v-if="!g.items.length" description="暂无" :image-size="60" />
          <div class="school-grid">
            <SchoolCard
              v-for="s in g.items"
              :key="s.code + s.scope"
              :s="s"
              :type="g.key"
              @open="openSchool(s.code)"
            />
          </div>
        </div>
      </template>
    </template>

    <p class="disclaimer">
      <template v-if="result">
        本结果基于 {{ result.ref_year }} 年录取数据与一分档，按位次估算，<b>仅供参考</b>。<br />
      </template>
      录取受招生计划、政策、报考人数等多种因素影响，实际结果可能与估算不同。<br />
      志愿填报请以教育考试院等官方渠道发布的正式信息为准。
    </p>

    <SchoolSheet v-model="sheetVisible" :code="activeCode" />
    </div>
  </div>
</template>

<style scoped>
.query-box { max-width: 520px; margin: 0 auto; }
.help { margin-bottom: 16px; }
.help p { margin: 6px 0; line-height: 1.6; font-size: 0.9rem; }
.query-card, .rank-card { margin-bottom: 16px; }
.rank-row { display: flex; gap: 0; justify-content: space-around; }
.disclaimer {
  font-size: 0.78rem;
  color: var(--c-muted);
  text-align: center;
  margin-top: 32px;
  line-height: 1.8;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}
</style>
