<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  adminListSchools, adminGetSchool, adminCreateSchool, adminUpdateSchool,
  adminDeleteSchool, adminUpsertStat, adminDeleteStat,
} from '../../api'

const scopeOpts = [
  { v: 'city6', label: '市内六区' },
  { v: 'whole', label: '全市' },
  { v: 'suburb', label: '郊区' },
]
const scopeLabel = { city6: '市内六区', whole: '全市', suburb: '郊区' }
const scopeTagType = { city6: 'primary', whole: 'success', suburb: 'warning' }

const scope = ref('')
const q = ref('')
const list = ref([])
const loading = ref(false)

// 编辑
const editVisible = ref(false)
const editing = ref(null)
const editId = ref(null)
const saving = ref(false)
const newYear = ref(null)

// 新增
const createVisible = ref(false)
const newSchool = ref(blankSchool())

function blankSchool() {
  return {
    code: '', scope: 'city6', name: '', type: '', location_district: '',
    home_district: '', recruit_area: '', boarding: '', canteen: '',
    class_types: '', fee: '', dorm_fee: '', address: '', phone: '', remark: '',
  }
}
function num(v) { return v === '' || v === null || v === undefined ? null : Number(v) }

async function load() {
  loading.value = true
  try {
    list.value = await adminListSchools({ scope: scope.value || undefined, q: q.value || undefined })
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function openEdit(item) {
  editId.value = item.id
  editing.value = await adminGetSchool(item.id)
  editVisible.value = true
}

async function saveStatic() {
  saving.value = true
  try {
    const e = editing.value
    await adminUpdateSchool(editId.value, {
      name: e.name, type: e.type, location_district: e.location_district,
      address: e.address, phone: e.phone, class_types: e.class_types,
    })
    ElMessage.success('已保存学校信息')
    load()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function saveStat(st) {
  saving.value = true
  try {
    await adminUpsertStat(editId.value, {
      year: st.year, plan: num(st.plan), min_score: num(st.min_score),
      rank_city6: num(st.rank_city6), rank_whole: num(st.rank_whole),
    })
    ElMessage.success(`已保存 ${st.year} 年数据`)
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function removeStat(st) {
  try {
    await ElMessageBox.confirm(`确认删除 ${st.year} 年录取数据？`, '确认', { type: 'warning' })
  } catch { return }
  try {
    editing.value = await adminDeleteStat(editId.value, st.year)
    ElMessage.success(`已删除 ${st.year} 年数据`)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

function addYear() {
  const y = Number(newYear.value)
  if (!y || y < 2000 || y > 2100) return ElMessage.warning('请输入有效年份')
  if (editing.value.stats.some((s) => s.year === y)) return ElMessage.warning('该年份已存在')
  editing.value.stats.unshift({ year: y, plan: null, min_score: null, rank_city6: null, rank_whole: null })
  editing.value.stats.sort((a, b) => b.year - a.year)
  newYear.value = null
}

async function removeSchool(item) {
  try {
    await ElMessageBox.confirm(
      `确认删除「${item.name}」(${item.code})？将一并删除其历年录取数据，且不可恢复。`,
      '危险操作', { type: 'warning', confirmButtonText: '删除', confirmButtonClass: 'el-button--danger' }
    )
  } catch { return }
  try {
    await adminDeleteSchool(item.id)
    if (editId.value === item.id) editVisible.value = false
    ElMessage.success('已删除')
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

function openCreate() {
  newSchool.value = blankSchool()
  createVisible.value = true
}

async function submitCreate() {
  const n = newSchool.value
  if (!n.code || !n.name) return ElMessage.warning('代码和名称必填')
  saving.value = true
  try {
    const payload = {}
    for (const k in n) payload[k] = n[k] === '' ? null : n[k]
    payload.code = n.code; payload.scope = n.scope; payload.name = n.name
    await adminCreateSchool(payload)
    ElMessage.success('已创建')
    createVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="toolbar">
    <h2 style="margin:0;flex:1">学校管理</h2>
    <el-button type="primary" :icon="'Plus'" @click="openCreate">新增学校</el-button>
  </div>

  <el-card shadow="never" style="margin:12px 0">
    <div class="filters">
      <el-select v-model="scope" placeholder="招生口径" clearable style="width:140px" @change="load">
        <el-option v-for="s in scopeOpts" :key="s.v" :label="s.label" :value="s.v" />
      </el-select>
      <el-input v-model="q" placeholder="搜索名称 / 代码" clearable style="max-width:240px" @keyup.enter="load" />
      <el-button type="primary" @click="load">搜索</el-button>
      <span class="muted">共 {{ list.length }} 所</span>
    </div>
  </el-card>

  <el-table :data="list" v-loading="loading" border stripe>
    <el-table-column prop="code" label="代码" width="90" />
    <el-table-column prop="name" label="学校" min-width="160" />
    <el-table-column label="口径" width="110">
      <template #default="{ row }">
        <el-tag :type="scopeTagType[row.scope]" size="small">{{ scopeLabel[row.scope] }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="type" label="性质" width="80" />
    <el-table-column prop="location_district" label="所在区" width="100" />
    <el-table-column label="操作" width="140" fixed="right">
      <template #default="{ row }">
        <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
        <el-button link type="danger" @click="removeSchool(row)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>

  <!-- 编辑弹层 -->
  <el-dialog v-model="editVisible" :title="`编辑 · ${editing?.name || ''}`" width="min(760px, 94vw)" top="5vh">
    <template v-if="editing">
      <el-form label-width="80px">
        <el-row :gutter="12">
          <el-col :xs="24" :sm="12"><el-form-item label="名称"><el-input v-model="editing.name" /></el-form-item></el-col>
          <el-col :xs="24" :sm="12"><el-form-item label="性质"><el-input v-model="editing.type" /></el-form-item></el-col>
          <el-col :xs="24" :sm="12"><el-form-item label="所在区"><el-input v-model="editing.location_district" /></el-form-item></el-col>
          <el-col :xs="24" :sm="12"><el-form-item label="电话"><el-input v-model="editing.phone" /></el-form-item></el-col>
          <el-col :xs="24"><el-form-item label="班型"><el-input v-model="editing.class_types" /></el-form-item></el-col>
          <el-col :xs="24"><el-form-item label="地址"><el-input v-model="editing.address" /></el-form-item></el-col>
        </el-row>
        <el-button type="primary" :loading="saving" @click="saveStatic">保存学校信息</el-button>
      </el-form>

      <el-divider>历年录取数据</el-divider>
      <div class="add-year">
        <el-input-number v-model="newYear" :min="2000" :max="2100" placeholder="年份" controls-position="right" />
        <el-button @click="addYear">添加年份</el-button>
      </div>

      <el-card v-for="st in editing.stats" :key="st.year" shadow="never" class="stat-card">
        <div class="stat-head">
          <b>{{ st.year }} 年</b>
          <el-button link type="danger" size="small" @click="removeStat(st)">删除</el-button>
        </div>
        <el-row :gutter="12">
          <el-col :xs="12" :sm="6"><el-form-item label="最低分" label-width="60px"><el-input v-model="st.min_score" type="number" /></el-form-item></el-col>
          <el-col v-if="editing.scope === 'city6'" :xs="12" :sm="6"><el-form-item label="市区位次" label-width="70px"><el-input v-model="st.rank_city6" type="number" /></el-form-item></el-col>
          <el-col :xs="12" :sm="6"><el-form-item label="全市位次" label-width="70px"><el-input v-model="st.rank_whole" type="number" /></el-form-item></el-col>
          <el-col :xs="12" :sm="6"><el-form-item label="计划" label-width="50px"><el-input v-model="st.plan" type="number" /></el-form-item></el-col>
        </el-row>
        <el-button size="small" type="primary" plain :loading="saving" @click="saveStat(st)">保存 {{ st.year }} 年</el-button>
      </el-card>
    </template>
  </el-dialog>

  <!-- 新增弹层 -->
  <el-dialog v-model="createVisible" title="新增学校" width="min(560px, 94vw)">
    <el-form label-width="90px">
      <el-form-item label="代码" required><el-input v-model="newSchool.code" placeholder="如 10199" /></el-form-item>
      <el-form-item label="招生口径" required>
        <el-select v-model="newSchool.scope" style="width:100%">
          <el-option v-for="s in scopeOpts" :key="s.v" :label="s.label" :value="s.v" />
        </el-select>
      </el-form-item>
      <el-form-item label="名称" required><el-input v-model="newSchool.name" /></el-form-item>
      <el-form-item label="性质"><el-input v-model="newSchool.type" placeholder="公办 / 民办" /></el-form-item>
      <el-form-item label="所在区"><el-input v-model="newSchool.location_district" /></el-form-item>
      <el-form-item label="班型"><el-input v-model="newSchool.class_types" /></el-form-item>
      <el-form-item label="地址"><el-input v-model="newSchool.address" /></el-form-item>
      <el-form-item label="电话"><el-input v-model="newSchool.phone" /></el-form-item>
      <el-alert title="创建后可在编辑页为其添加历年录取数据" type="info" :closable="false" />
    </el-form>
    <template #footer>
      <el-button @click="createVisible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="submitCreate">创建</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.toolbar { display: flex; align-items: center; gap: 12px; }
.filters { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.add-year { display: flex; gap: 10px; margin-bottom: 12px; }
.stat-card { margin-bottom: 10px; background: #fafafa; }
.stat-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
</style>
