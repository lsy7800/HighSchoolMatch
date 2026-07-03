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

    <!-- 学校卡片列表 -->
    <div v-loading="loading" class="card-grid">
      <div
        v-for="s in list"
        :key="s.code + s.scope"
        class="school-card"
      >
        <!-- 标题行 -->
        <div class="card-head">
          <button class="school-name" @click="openDetail(s.code)">{{ s.name }}</button>
          <el-tag :type="scopeTagType[s.scope]" size="small" class="scope-tag">
            {{ scopeLabel[s.scope] }}
          </el-tag>
        </div>

        <!-- 基本信息标签 -->
        <div class="card-tags">
          <span v-if="s.type" class="info-tag">{{ s.type }}</span>
          <span v-if="s.location_district" class="info-tag">{{ s.location_district }}</span>
          <span v-if="s.boarding" class="info-tag">{{ s.boarding }}</span>
          <span v-if="s.class_types" class="info-tag class-types">{{ s.class_types }}</span>
        </div>

        <!-- 简介 -->
        <p v-if="s.intro" class="card-intro">{{ s.intro }}</p>

        <!-- 最新录取数据 -->
        <div v-if="s.latest_min_score || rankDisplay(s)" class="card-stats">
          <div v-if="s.latest_year" class="stat-year">{{ s.latest_year }} 年录取</div>
          <div class="stat-items">
            <div v-if="s.latest_min_score" class="stat-item">
              <span class="stat-value">{{ s.latest_min_score }}</span>
              <span class="stat-label">最低分</span>
            </div>
            <div v-if="rankDisplay(s)" class="stat-item">
              <span class="stat-value">{{ rankDisplay(s).toLocaleString() }}</span>
              <span class="stat-label">{{ rankLabel(s) }}</span>
            </div>
          </div>
        </div>

        <div class="card-footer">
          <el-button link type="primary" size="small" @click="openDetail(s.code)">
            查看详情 →
          </el-button>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="!loading && list.length === 0" class="empty-state">
        <el-empty description="没有匹配的学校" />
      </div>
    </div>
  </div>

  <!-- 详情弹层 (复用 SchoolSheet) -->
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

.search-card { margin-bottom: 24px; }
.search-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

/* 卡片网格 */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  min-height: 200px;
}

.school-card {
  background: #fff;
  border: 1px solid var(--c-border);
  border-radius: 12px;
  padding: 18px 20px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: box-shadow 0.18s, border-color 0.18s;
}
.school-card:hover {
  box-shadow: 0 4px 18px rgba(0,0,0,0.08);
  border-color: var(--el-color-primary-light-5);
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}
.school-name {
  background: none;
  border: none;
  padding: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--el-color-primary);
  cursor: pointer;
  text-align: left;
  line-height: 1.4;
  flex: 1;
}
.school-name:hover { text-decoration: underline; }
.scope-tag { flex-shrink: 0; }

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.info-tag {
  font-size: 0.78rem;
  color: var(--c-text-2);
  background: var(--c-bg);
  border: 1px solid var(--c-border);
  border-radius: 5px;
  padding: 1px 7px;
  white-space: nowrap;
}
.class-types {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-intro {
  font-size: 0.83rem;
  color: var(--c-text-2);
  line-height: 1.55;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 录取数据摘要 */
.card-stats {
  background: var(--c-bg);
  border-radius: 8px;
  padding: 10px 14px;
}
.stat-year {
  font-size: 0.75rem;
  color: var(--c-text-2);
  margin-bottom: 6px;
}
.stat-items {
  display: flex;
  gap: 24px;
}
.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.stat-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--c-text);
  line-height: 1;
}
.stat-label {
  font-size: 0.72rem;
  color: var(--c-text-2);
}

.card-footer {
  margin-top: auto;
  padding-top: 2px;
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

@media (max-width: 480px) {
  .schools-page { padding: 20px 14px 48px; }
  .card-grid { grid-template-columns: 1fr; }
}
</style>
