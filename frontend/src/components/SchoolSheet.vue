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
const channels = ref([]) // 一个 code 可能有多条招生线
const error = ref('')

const scopeLabel = { city6: '市内六区', whole: '全市', suburb: '郊区' }

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
      // 市内六区考生不能填报郊区招生线, 详情里也只展示可报的招生线
      channels.value = all.filter((c) => c.scope !== 'suburb')
    } catch {
      error.value = '加载失败'
    } finally {
      loading.value = false
    }
  },
  { immediate: true }
)
</script>

<template>
  <el-dialog v-model="visible" width="min(720px, 94vw)" top="6vh" :title="channels[0]?.name || '学校详情'">
    <div v-if="loading" v-loading="true" style="min-height:120px"></div>
    <el-alert v-else-if="error" :title="error" type="error" :closable="false" />

    <template v-else>
      <div v-for="(s, i) in channels" :key="i" :style="i ? 'margin-top:24px' : ''">
        <el-divider v-if="i" />
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="招生口径">{{ scopeLabel[s.scope] }}</el-descriptions-item>
          <el-descriptions-item label="性质">{{ s.type || '—' }}</el-descriptions-item>
          <el-descriptions-item v-if="s.home_district" label="归属区">{{ s.home_district }}</el-descriptions-item>
          <el-descriptions-item v-if="s.location_district" label="所在区">{{ s.location_district }}</el-descriptions-item>
          <el-descriptions-item v-if="s.recruit_area" label="招生区域">{{ s.recruit_area }}</el-descriptions-item>
          <el-descriptions-item label="住宿">{{ s.boarding || '—' }}</el-descriptions-item>
          <el-descriptions-item label="食堂">{{ s.canteen || '—' }}</el-descriptions-item>
          <el-descriptions-item v-if="s.class_types" label="班型">{{ s.class_types }}</el-descriptions-item>
          <el-descriptions-item v-if="s.fee" label="学费">{{ s.fee }}</el-descriptions-item>
          <el-descriptions-item v-if="s.dorm_fee" label="住宿费">{{ s.dorm_fee }}</el-descriptions-item>
          <el-descriptions-item v-if="s.address" label="地址">{{ s.address }}</el-descriptions-item>
          <el-descriptions-item v-if="s.phone" label="电话">{{ s.phone }}</el-descriptions-item>
          <el-descriptions-item v-if="s.remark" label="备注">{{ s.remark }}</el-descriptions-item>
        </el-descriptions>

        <h4>历年趋势</h4>
        <div class="trend-row">
          <TrendChart
            :points="rankPoints(s)"
            :invert="true"
            color="#3b6fe0"
            :label="(s.scope === 'city6' ? '市区' : '全市') + '录取位次（越低越好）'"
          />
          <TrendChart :points="scorePoints(s)" color="#2e9e5b" label="录取最低分" />
        </div>

        <h4>历年录取</h4>
        <el-table :data="s.stats" size="small" border>
          <el-table-column prop="year" label="年份" width="70" />
          <el-table-column prop="plan" label="计划" />
          <el-table-column prop="min_score" label="最低分" />
          <el-table-column v-if="s.scope === 'city6'" prop="rank_city6" label="市区位次" />
          <el-table-column prop="rank_whole" label="全市位次" />
        </el-table>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
h4 { margin: 20px 0 10px; font-size: 0.95rem; font-weight: 600; color: #4a5057; }
.trend-row { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 4px; }
.trend-row > * { flex: 1; min-width: 220px; }
</style>
