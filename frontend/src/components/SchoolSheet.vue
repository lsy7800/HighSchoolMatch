<script setup>
import { ref, watch, computed } from 'vue'
import { getSchool } from '../api'
import TrendChart from './TrendChart.vue'

const props = defineProps({
  code: String,
  modelValue: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const loading = ref(false)
const channels = ref([])
const error = ref('')

const scopeLabel = { city6: '市内六区', whole: '全市', suburb: '郊区' }
const scopeTagType = { city6: 'primary', whole: 'success', suburb: 'warning' }

function rankPoints(s) {
  const key = s.scope === 'city6' ? 'rank_city6' : 'rank_whole'
  return s.stats.map((st) => ({ year: st.year, value: st[key] }))
}
function scorePoints(s) {
  return s.stats.map((st) => ({ year: st.year, value: st.min_score }))
}

watch(
  () => [props.code, props.modelValue],
  async ([code, open]) => {
    if (!code || !open) return
    loading.value = true
    error.value = ''
    channels.value = []
    try {
      const all = await getSchool(code)
      channels.value = all.filter((c) => c.scope !== 'suburb')
    } catch {
      error.value = '加载失败'
    } finally {
      loading.value = false
    }
  },
  { immediate: true }
)

// 班型拆分 + 颜色映射（鲜亮配色）
function splitClassTypes(str) {
  if (!str) return []
  return str.split(/[/、，,]/).map((s) => s.trim()).filter(Boolean)
}

const CLASS_COLORS = [
  { keys: ['普通'], bg: 'linear-gradient(135deg,#f1f5f9,#e2e8f0)', text: '#475569' },
  { keys: ['实验'], bg: 'linear-gradient(135deg,#dbeafe,#bfdbfe)', text: '#1d4ed8' },
  { keys: ['体育'], bg: 'linear-gradient(135deg,#fef3c7,#fde68a)', text: '#b45309' },
  { keys: ['艺术', '音乐', '美术', '舞蹈'], bg: 'linear-gradient(135deg,#fbcfe8,#f9a8d4)', text: '#be185d' },
  { keys: ['国际'], bg: 'linear-gradient(135deg,#e0e7ff,#c7d2fe)', text: '#4338ca' },
  { keys: ['理工', '创新', '科技', '科创'], bg: 'linear-gradient(135deg,#cffafe,#a5f3fc)', text: '#0e7490' },
  { keys: ['文理', '文科', '人文'], bg: 'linear-gradient(135deg,#dcfce7,#bbf7d0)', text: '#15803d' },
  { keys: ['航', '强基', '竞赛'], bg: 'linear-gradient(135deg,#fed7aa,#fdba74)', text: '#9a3412' },
]
const CLASS_DEFAULT = { bg: 'linear-gradient(135deg,#f1f5f9,#e2e8f0)', text: '#475569' }

function classTypeStyle(cls) {
  for (const rule of CLASS_COLORS) {
    if (rule.keys.some((k) => cls.includes(k))) return rule
  }
  return CLASS_DEFAULT
}

function fmt(v) {
  if (v === null || v === undefined || v === '') return '—'
  return v
}

// 与上一年(更早的年份)对比的增减趋势。
// stats 按年份降序排列, 故上一行 = 索引+1。
// mode='score': 数值升=更难(红); mode='rank': 数值升=排名靠后=更易(绿)
function trend(stats, index, key, mode) {
  if (index + 1 >= stats.length) return null
  const cur = stats[index][key]
  const prev = stats[index + 1][key]
  if (cur == null || prev == null) return null
  let delta = cur - prev
  if (mode === 'score') delta = Math.round(delta * 10) / 10
  else delta = Math.round(delta)
  if (delta === 0) return { arrow: '–', color: '#909399', text: '持平' }
  const up = delta > 0
  const harder = mode === 'score' ? up : !up
  return {
    arrow: up ? '↑' : '↓',
    color: harder ? '#f56c6c' : '#67c23a',
    text: Math.abs(delta).toString(),
  }
}
</script>

<template>
  <el-dialog v-model="visible" width="min(780px, 95vw)" top="5vh" :show-close="true" class="school-detail-dialog">
    <template #header>
      <div class="dialog-header">
        <el-icon class="dialog-icon"><School /></el-icon>
        <span class="dialog-title">{{ channels[0]?.name || '学校详情' }}</span>
      </div>
    </template>

    <div v-if="loading" v-loading="true" style="min-height:200px"></div>
    <el-alert v-else-if="error" :title="error" type="error" :closable="false" />

    <template v-else>
      <div v-for="(s, i) in channels" :key="i">
        <el-divider v-if="i" />

        <!-- 招生口径标签条 -->
        <div class="scope-bar">
          <el-tag :type="scopeTagType[s.scope]" effect="dark" round>{{ scopeLabel[s.scope] }} 招生</el-tag>
          <span v-if="s.type" class="type-chip">{{ s.type }}</span>
          <span v-if="s.location_district" class="meta-dot">{{ s.location_district }}</span>
        </div>

        <!-- 班型设置（彩色 tag） -->
        <div v-if="s.class_types" class="class-section">
          <div class="section-label">班型设置</div>
          <div class="class-tags">
            <span
              v-for="cls in splitClassTypes(s.class_types)"
              :key="cls"
              class="class-tag"
              :style="{ background: classTypeStyle(cls).bg, color: classTypeStyle(cls).text }"
            >{{ cls }}</span>
          </div>
        </div>

        <!-- 基本信息 -->
        <div class="info-grid">
          <div class="info-cell"><span class="info-key">住宿</span><span class="info-val">{{ fmt(s.boarding) }}</span></div>
          <div class="info-cell"><span class="info-key">餐饮</span><span class="info-val">{{ fmt(s.canteen) }}</span></div>
          <div class="info-cell"><span class="info-key">学费</span><span class="info-val">{{ fmt(s.fee) }}</span></div>
          <div class="info-cell"><span class="info-key">学费减免</span><span class="info-val">{{ fmt(s.fee_reduction) }}</span></div>
          <div v-if="s.subject_model" class="info-cell info-wide"><span class="info-key">选科模式</span><span class="info-val">{{ s.subject_model }}</span></div>
          <div v-if="s.class_adjust" class="info-cell info-wide"><span class="info-key">调班机制</span><span class="info-val">{{ s.class_adjust }}</span></div>
          <div v-if="s.schedule" class="info-cell info-wide"><span class="info-key">作息</span><span class="info-val">{{ s.schedule }}</span></div>
        </div>

        <!-- 简介 -->
        <div v-if="s.intro" class="intro-block">
          <div class="section-label">学校简介</div>
          <p class="intro-text">{{ s.intro }}</p>
        </div>

        <div v-if="s.remark || s.other_info" class="extra-block">
          <div v-if="s.remark" class="extra-row"><span class="extra-key">备注</span><span class="extra-val">{{ s.remark }}</span></div>
          <div v-if="s.other_info" class="extra-row"><span class="extra-key">其他</span><span class="extra-val">{{ s.other_info }}</span></div>
        </div>

        <!-- 历年趋势 -->
        <div class="trend-section">
          <div class="section-label">历年趋势</div>
          <div class="trend-row">
            <TrendChart
              :points="rankPoints(s)"
              :invert="true"
              color="#3b6fe0"
              :label="(s.scope === 'city6' ? '市区' : '全市') + '录取位次（越低越好）'"
            />
            <TrendChart :points="scorePoints(s)" color="#2e9e5b" label="录取最低分" />
          </div>
        </div>

        <!-- 历年录取 -->
        <div class="stats-section">
          <div class="section-label">历年录取</div>
          <el-table :data="s.stats" size="small" border>
            <el-table-column prop="year" label="年份" width="70" align="center" />
            <el-table-column prop="plan" label="计划" align="center" />
            <el-table-column label="最低分" align="center" width="110">
              <template #default="{ row, $index }">
                <div class="cell-trend">
                  <span>{{ row.min_score ?? '—' }}</span>
                  <span
                    v-if="trend(s.stats, $index, 'min_score', 'score')"
                    class="trend"
                    :style="{ color: trend(s.stats, $index, 'min_score', 'score').color }"
                  >{{ trend(s.stats, $index, 'min_score', 'score').arrow }}{{ trend(s.stats, $index, 'min_score', 'score').text }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column v-if="s.scope === 'city6'" label="市区位次" align="center" width="120">
              <template #default="{ row, $index }">
                <div class="cell-trend">
                  <span>{{ row.rank_city6 != null ? row.rank_city6.toLocaleString() : '—' }}</span>
                  <span
                    v-if="trend(s.stats, $index, 'rank_city6', 'rank')"
                    class="trend"
                    :style="{ color: trend(s.stats, $index, 'rank_city6', 'rank').color }"
                  >{{ trend(s.stats, $index, 'rank_city6', 'rank').arrow }}{{ trend(s.stats, $index, 'rank_city6', 'rank').text }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="全市位次" align="center" width="120">
              <template #default="{ row, $index }">
                <div class="cell-trend">
                  <span>{{ row.rank_whole != null ? row.rank_whole.toLocaleString() : '—' }}</span>
                  <span
                    v-if="trend(s.stats, $index, 'rank_whole', 'rank')"
                    class="trend"
                    :style="{ color: trend(s.stats, $index, 'rank_whole', 'rank').color }"
                  >{{ trend(s.stats, $index, 'rank_whole', 'rank').arrow }}{{ trend(s.stats, $index, 'rank_whole', 'rank').text }}</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.dialog-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dialog-icon {
  font-size: 1.2rem;
  color: var(--el-color-primary);
}
.dialog-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--c-text);
}

/* 招生口径条 */
.scope-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--c-border);
}
.type-chip {
  font-size: 0.78rem;
  color: var(--c-text-2);
  background: var(--c-bg);
  border: 1px solid var(--c-border);
  border-radius: 6px;
  padding: 2px 8px;
}
.meta-dot { font-size: 0.8rem; color: var(--c-text-2); }
.meta-dot::before { content: '· '; }

/* 通用 section 标题 */
.section-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--c-text-2);
  margin-bottom: 8px;
  padding-left: 8px;
  border-left: 3px solid var(--el-color-primary);
  line-height: 1.2;
}

/* 班型彩色 tag */
.class-section { margin-bottom: 16px; }
.class-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.class-tag {
  display: inline-block;
  font-size: 0.76rem;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 14px;
  line-height: 1.6;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

/* 基本信息 grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: var(--c-border);
  border: 1px solid var(--c-border);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
}
.info-cell {
  background: #fff;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.info-wide { grid-column: span 4; }
.info-key {
  font-size: 0.72rem;
  color: var(--c-text-2);
}
.info-val {
  font-size: 0.88rem;
  color: var(--c-text);
  font-weight: 500;
  line-height: 1.4;
}

/* 简介 */
.intro-block { margin-bottom: 16px; }
.intro-text {
  margin: 0;
  font-size: 0.86rem;
  color: var(--c-text);
  line-height: 1.7;
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  border-radius: 8px;
  padding: 14px 16px;
  border-left: 3px solid var(--el-color-primary);
}

/* 备注/其他 */
.extra-block {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 18px;
}
.extra-row {
  display: flex;
  gap: 8px;
  font-size: 0.82rem;
  line-height: 1.6;
}
.extra-row + .extra-row { margin-top: 4px; }
.extra-key {
  flex-shrink: 0;
  color: #b45309;
  font-weight: 600;
}
.extra-val { color: #78350f; }

/* 趋势 */
.trend-section { margin-bottom: 18px; }
.trend-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.trend-row > * { flex: 1; min-width: 220px; }

/* 录取表 */
.stats-section { margin-top: 4px; }
.cell-trend {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  justify-content: center;
}
.trend {
  font-size: 0.72rem;
  font-weight: 700;
  line-height: 1;
}

@media (max-width: 600px) {
  .info-grid { grid-template-columns: repeat(2, 1fr); }
  .info-wide { grid-column: span 2; }
}
</style>
