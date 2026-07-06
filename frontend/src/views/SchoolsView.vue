<script setup>
import { ref, computed, onMounted } from 'vue'
import { listSchools, listDistricts } from '../api'
import SchoolSheet from '../components/SchoolSheet.vue'

const scopeOpts = [
  { v: 'city6', label: '市内六区' },
  { v: 'whole', label: '全市' },
  { v: 'suburb', label: '郊区' },
]
const typeOpts = ['公办', '民办']

const scopeLabel = { city6: '市内六区', whole: '全市', suburb: '郊区' }
const scopeTagType = { city6: 'primary', whole: 'success', suburb: 'warning' }

const q = ref('')
const scope = ref('')
const type = ref('')
const district = ref('')
const districtOpts = ref([])
const list = ref([])
const loading = ref(false)

// 排序模式: 'code' = 按学校编号升序, 'score' = 按录取分数降序
const sortMode = ref('code')

const detailCode = ref('')
const detailVisible = ref(false)

function openDetail(code) {
  detailCode.value = code
  detailVisible.value = true
}

async function load() {
  loading.value = true
  try {
    list.value = await listSchools({
      q: q.value || undefined,
      scope: scope.value || undefined,
      type: type.value || undefined,
      district: district.value || undefined,
    })
  } finally {
    loading.value = false
  }
}
onMounted(async () => {
  districtOpts.value = await listDistricts()
  await load()
})

function onClear() {
  q.value = ''
  scope.value = ''
  type.value = ''
  district.value = ''
  load()
}

// 客户端排序: 数值空值排末尾
function cmpNum(a, b, key) {
  const av = a[key]
  const bv = b[key]
  if (av == null && bv == null) return 0
  if (av == null) return 1
  if (bv == null) return -1
  return av - bv
}

// 所在区彩色 tag: 市内六区固定配色, 其余按名称哈希取色
const DISTRICT_PALETTE = [
  { bg: '#fef3c7', text: '#b45309' }, // 琥珀
  { bg: '#dcfce7', text: '#15803d' }, // 绿
  { bg: '#dbeafe', text: '#1d4ed8' }, // 蓝
  { bg: '#fbcfe8', text: '#be185d' }, // 粉
  { bg: '#e0e7ff', text: '#4338ca' }, // 紫
  { bg: '#cffafe', text: '#0e7490' }, // 青
  { bg: '#fed7aa', text: '#9a3412' }, // 橙
  { bg: '#f1f5f9', text: '#475569' }, // 灰
]
const DISTRICT_FIXED = {
  和平: { bg: '#fee2e2', text: '#b91c1c' },
  河东: { bg: '#dbeafe', text: '#1d4ed8' },
  河西: { bg: '#dcfce7', text: '#15803d' },
  南开: { bg: '#fbcfe8', text: '#be185d' },
  河北: { bg: '#fed7aa', text: '#9a3412' },
  红桥: { bg: '#e0e7ff', text: '#4338ca' },
}
function districtStyle(d) {
  if (!d) return null
  if (DISTRICT_FIXED[d]) return DISTRICT_FIXED[d]
  let h = 0
  for (let i = 0; i < d.length; i++) h = (h * 31 + d.charCodeAt(i)) >>> 0
  return DISTRICT_PALETTE[h % DISTRICT_PALETTE.length]
}

// 类型彩色 tag: 公办蓝 / 民办橙 / 其他按哈希
const TYPE_FIXED = {
  公办: { bg: '#dbeafe', text: '#1d4ed8' },
  民办: { bg: '#fed7aa', text: '#9a3412' },
}
function typeStyle(t) {
  if (!t) return null
  if (TYPE_FIXED[t]) return TYPE_FIXED[t]
  let h = 0
  for (let i = 0; i < t.length; i++) h = (h * 31 + t.charCodeAt(i)) >>> 0
  return DISTRICT_PALETTE[h % DISTRICT_PALETTE.length]
}

const sortedList = computed(() => {
  const arr = [...list.value]
  if (sortMode.value === 'score') {
    arr.sort((a, b) => cmpNum(b, a, 'latest_min_score') || cmpNum(a, b, 'code'))
  } else {
    arr.sort((a, b) => (a.code > b.code ? 1 : a.code < b.code ? -1 : 0))
  }
  return arr
})
</script>

<template>
  <div class="schools-page">
    <div class="page-header">
      <h1 class="page-title">学校一览</h1>
      <p class="page-desc">天津市高中招生学校，点击学校名称查看详细信息</p>
    </div>

    <el-card shadow="never" class="search-card">
      <div class="search-row">
        <el-input
          v-model="q"
          placeholder="搜索学校名称 / 代码"
          clearable
          style="max-width:260px"
          @keyup.enter="load"
          @clear="load"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="scope" placeholder="招生口径" clearable style="width:130px" @change="load">
          <el-option v-for="s in scopeOpts" :key="s.v" :label="s.label" :value="s.v" />
        </el-select>
        <el-select v-model="district" placeholder="所在区" clearable filterable style="width:130px" @change="load">
          <el-option v-for="d in districtOpts" :key="d" :label="d" :value="d" />
        </el-select>
        <el-select v-model="type" placeholder="性质" clearable style="width:110px" @change="load">
          <el-option v-for="t in typeOpts" :key="t" :label="t" :value="t" />
        </el-select>
        <el-button type="primary" @click="load">搜索</el-button>
        <el-button @click="onClear">重置</el-button>
        <span class="muted">共 {{ sortedList.length }} 所</span>
      </div>
    </el-card>

    <div class="sort-bar">
      <span class="sort-label">排序：</span>
      <el-button
        :type="sortMode === 'code' ? 'primary' : 'default'"
        size="small"
        @click="sortMode = 'code'"
      >按照学校编号排序</el-button>
      <el-button
        :type="sortMode === 'score' ? 'primary' : 'default'"
        size="small"
        @click="sortMode = 'score'"
      >按照录取分数排序</el-button>
    </div>

    <el-card shadow="never">
      <el-table
        :data="sortedList"
        v-loading="loading"
        border
        stripe
        style="width:100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: '600', fontSize: '0.85rem' }"
        :cell-style="{ fontSize: '0.875rem' }"
      >
      <!-- 学校名称 -->
      <el-table-column prop="name" label="学校名称" min-width="160">
        <template #default="{ row }">
          <span class="school-link" @click="openDetail(row.code)">{{ row.name }}</span>
        </template>
      </el-table-column>

      <!-- 类型 -->
      <el-table-column label="类型" width="70" align="center">
        <template #default="{ row }">
          <span
            v-if="row.type"
            class="type-tag"
            :style="{ background: typeStyle(row.type).bg, color: typeStyle(row.type).text }"
          >{{ row.type }}</span>
          <span v-else class="empty-val">—</span>
        </template>
      </el-table-column>

      <!-- 招生范围 -->
      <el-table-column label="招生范围" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="scopeTagType[row.scope]" size="small">{{ scopeLabel[row.scope] }}</el-tag>
        </template>
      </el-table-column>

      <!-- 所在区 -->
      <el-table-column label="所在区" width="90" align="center">
        <template #default="{ row }">
          <span
            v-if="row.location_district"
            class="district-tag"
            :style="{
              background: districtStyle(row.location_district).bg,
              color: districtStyle(row.location_district).text,
            }"
          >{{ row.location_district }}</span>
          <span v-else class="empty-val">—</span>
        </template>
      </el-table-column>

      <!-- 25年最低分 -->
      <el-table-column prop="latest_min_score" label="25年最低分" width="100" align="center">
        <template #default="{ row }">
          <span v-if="row.latest_min_score" class="score-val">{{ row.latest_min_score }}</span>
          <span v-else class="empty-val">—</span>
        </template>
      </el-table-column>

      <!-- 市区位次（仅六区线有意义） -->
      <el-table-column prop="latest_rank_city6" label="市区位次" width="90" align="center">
        <template #default="{ row }">
          <span v-if="row.latest_rank_city6" class="rank-val">{{ row.latest_rank_city6.toLocaleString() }}</span>
          <span v-else class="empty-val">—</span>
        </template>
      </el-table-column>

      <!-- 全市位次 -->
      <el-table-column prop="latest_rank_whole" label="全市位次" width="90" align="center">
        <template #default="{ row }">
          <span v-if="row.latest_rank_whole" class="rank-val">{{ row.latest_rank_whole.toLocaleString() }}</span>
          <span v-else class="empty-val">—</span>
        </template>
      </el-table-column>
      </el-table>
    </el-card>

    <el-empty v-if="!loading && sortedList.length === 0" description="没有匹配的学校" style="padding:60px 0" />
  </div>

  <SchoolSheet :code="detailCode" v-model="detailVisible" />
</template>

<style scoped>
.schools-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 20px 60px;
}

.page-header { margin-bottom: 24px; }
.page-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--c-text);
  margin: 0 0 6px;
}
.page-desc { color: var(--c-text-2); font-size: 0.92rem; margin: 0; }

.search-card { margin-bottom: 16px; }
.search-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.muted { color: var(--c-text-2); font-size: 0.88rem; }

.sort-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 4px;
}
.sort-label {
  font-size: 0.85rem;
  color: var(--c-text-2);
}

.school-link {
  color: var(--el-color-primary);
  font-weight: 600;
  cursor: pointer;
}
.school-link:hover { text-decoration: underline; }

.score-val { font-weight: 600; color: var(--c-text); }
.rank-val { color: var(--c-text-2); }
.empty-val { color: #c0c4cc; }

.district-tag {
  display: inline-block;
  font-size: 0.74rem;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 10px;
  line-height: 1.6;
}

.type-tag {
  display: inline-block;
  font-size: 0.74rem;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 10px;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .schools-page { padding: 20px 12px 48px; }
}
</style>
