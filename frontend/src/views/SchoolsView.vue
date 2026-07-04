<script setup>
import { ref, onMounted } from 'vue'
import { listSchools } from '../api'
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
const list = ref([])
const loading = ref(false)

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
    })
  } finally {
    loading.value = false
  }
}
onMounted(load)

function onClear() {
  q.value = ''
  scope.value = ''
  type.value = ''
  load()
}
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
        <el-select v-model="type" placeholder="性质" clearable style="width:110px" @change="load">
          <el-option v-for="t in typeOpts" :key="t" :label="t" :value="t" />
        </el-select>
        <el-button type="primary" @click="load">搜索</el-button>
        <el-button @click="onClear">重置</el-button>
        <span class="muted">共 {{ list.length }} 所</span>
      </div>
    </el-card>

    <el-table
      :data="list"
      v-loading="loading"
      border
      stripe
      style="width:100%"
      :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: '600', fontSize: '0.85rem' }"
      :cell-style="{ fontSize: '0.875rem' }"
    >
      <!-- 学校名称 -->
      <el-table-column label="学校名称" min-width="160">
        <template #default="{ row }">
          <span class="school-link" @click="openDetail(row.code)">{{ row.name }}</span>
        </template>
      </el-table-column>

      <!-- 类型 -->
      <el-table-column prop="type" label="类型" width="70" align="center" />

      <!-- 招生范围 -->
      <el-table-column label="招生范围" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="scopeTagType[row.scope]" size="small">{{ scopeLabel[row.scope] }}</el-tag>
        </template>
      </el-table-column>

      <!-- 所在区 -->
      <el-table-column prop="location_district" label="所在区" width="90" align="center" />

      <!-- 25年最低分 -->
      <el-table-column label="25年最低分" width="100" align="center">
        <template #default="{ row }">
          <span v-if="row.latest_min_score" class="score-val">{{ row.latest_min_score }}</span>
          <span v-else class="empty-val">—</span>
        </template>
      </el-table-column>

      <!-- 市区位次（仅六区线有意义） -->
      <el-table-column label="市区位次" width="90" align="center">
        <template #default="{ row }">
          <span v-if="row.latest_rank_city6" class="rank-val">{{ row.latest_rank_city6.toLocaleString() }}</span>
          <span v-else class="empty-val">—</span>
        </template>
      </el-table-column>

      <!-- 全市位次 -->
      <el-table-column label="全市位次" width="90" align="center">
        <template #default="{ row }">
          <span v-if="row.latest_rank_whole" class="rank-val">{{ row.latest_rank_whole.toLocaleString() }}</span>
          <span v-else class="empty-val">—</span>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && list.length === 0" description="没有匹配的学校" style="padding:60px 0" />
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

.search-card { margin-bottom: 20px; }
.search-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.muted { color: var(--c-text-2); font-size: 0.88rem; }

.school-link {
  color: var(--el-color-primary);
  font-weight: 600;
  cursor: pointer;
}
.school-link:hover { text-decoration: underline; }

.score-val { font-weight: 600; color: var(--c-text); }
.rank-val { color: var(--c-text-2); }
.empty-val { color: #c0c4cc; }

@media (max-width: 768px) {
  .schools-page { padding: 20px 12px 48px; }
}
</style>
