<script setup>
import { ref, computed, onMounted } from 'vue'
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

// 详情弹层
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

function onSearch() { load() }
function onClear() {
  q.value = ''
  scope.value = ''
  type.value = ''
  load()
}

// 每行显示的最新位次：六区线用市区位次，全市线用全市位次
function rankDisplay(s) {
  if (s.scope === 'city6' && s.latest_rank_city6) return s.latest_rank_city6
  if (s.latest_rank_whole) return s.latest_rank_whole
  return null
}
function rankLabel(s) {
  return s.scope === 'city6' ? '市区位次' : '全市位次'
}
</script>

<template>
  <div class="schools-page">
    <div class="page-header">
      <h1 class="page-title">学校一览</h1>
      <p class="page-desc">天津市高中招生学校，点击名称查看详细信息</p>
    </div>

    <!-- 搜索栏 -->
    <el-card shadow="never" class="search-card">
      <div class="search-row">
        <el-input
          v-model="q"
          placeholder="搜索学校名称 / 代码"
          clearable
          style="max-width:260px"
          @keyup.enter="onSearch"
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

        <el-button type="primary" @click="onSearch">搜索</el-button>
        <el-button @click="onClear">重置</el-button>
        <span class="muted" style="margin-left:4px">共 {{ list.length }} 所</span>
      </div>
    </el-card>

    <!-- 学校列表 -->
    <div v-loading="loading" class="school-list">
      <div
        v-for="s in list"
        :key="s.code + s.scope"
        class="school-row"
        @click="openDetail(s.code)"
      >
        <div class="row-main">
          <div class="row-name-line">
            <span class="school-name">{{ s.name }}</span>
            <el-tag :type="scopeTagType[s.scope]" size="small">{{ scopeLabel[s.scope] }}</el-tag>
          </div>
          <div class="row-meta">
            <span v-if="s.type" class="meta-item">{{ s.type }}</span>
            <span v-if="s.location_district" class="meta-item">{{ s.location_district }}</span>
            <span v-if="s.boarding" class="meta-item">{{ s.boarding }}</span>
            <span v-if="s.class_types" class="meta-item meta-classtypes">{{ s.class_types }}</span>
          </div>
          <p v-if="s.intro" class="row-intro">{{ s.intro }}</p>
        </div>

        <div class="row-stats" v-if="s.latest_min_score || rankDisplay(s)">
          <div v-if="s.latest_min_score" class="stat-col">
            <span class="stat-val">{{ s.latest_min_score }}</span>
            <span class="stat-lbl">{{ s.latest_year }}年最低分</span>
          </div>
          <div v-if="rankDisplay(s)" class="stat-col">
            <span class="stat-val">{{ rankDisplay(s).toLocaleString() }}</span>
            <span class="stat-lbl">{{ rankLabel(s) }}</span>
          </div>
        </div>

        <el-icon class="row-arrow"><ArrowRight /></el-icon>
      </div>

      <el-empty v-if="!loading && list.length === 0" description="没有匹配的学校" style="padding:60px 0" />
    </div>
  </div>

  <!-- 详情弹层 (复用 SchoolSheet) -->
  <SchoolSheet :code="detailCode" v-model="detailVisible" />
</template>

<style scoped>
.schools-page {
  max-width: 960px;
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
.search-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

/* 列表 */
.school-list {
  background: #fff;
  border: 1px solid var(--c-border);
  border-radius: 12px;
  overflow: hidden;
  min-height: 120px;
}

.school-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--c-border);
  cursor: pointer;
  transition: background 0.15s;
}
.school-row:last-child { border-bottom: none; }
.school-row:hover { background: var(--el-color-primary-light-9); }

.row-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.row-name-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.school-name {
  font-size: 0.98rem;
  font-weight: 600;
  color: var(--el-color-primary);
  line-height: 1.3;
}
.school-row:hover .school-name { text-decoration: underline; }

.row-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.meta-item {
  font-size: 0.76rem;
  color: var(--c-text-2);
  background: var(--c-bg);
  border: 1px solid var(--c-border);
  border-radius: 4px;
  padding: 1px 6px;
  white-space: nowrap;
}
.meta-classtypes {
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-intro {
  font-size: 0.81rem;
  color: var(--c-text-2);
  line-height: 1.5;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 右侧数据列 */
.row-stats {
  display: flex;
  gap: 24px;
  flex-shrink: 0;
  text-align: right;
}
.stat-col {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}
.stat-val {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--c-text);
  line-height: 1;
}
.stat-lbl {
  font-size: 0.7rem;
  color: var(--c-text-2);
  white-space: nowrap;
}

.row-arrow {
  color: var(--c-text-2);
  font-size: 14px;
  flex-shrink: 0;
  opacity: 0.5;
}

@media (max-width: 600px) {
  .schools-page { padding: 20px 12px 48px; }
  .row-stats { display: none; }
  .school-row { padding: 14px 16px; }
}
</style>
