<script setup>
import { ref, onMounted } from 'vue'
import {
  adminListSchools, adminGetSchool, adminCreateSchool, adminUpdateSchool,
  adminDeleteSchool, adminUpsertStat, adminDeleteStat,
} from '../../api'

const scopes = [
  { v: '', label: '全部' },
  { v: 'city6', label: '市内六区' },
  { v: 'whole', label: '全市' },
  { v: 'suburb', label: '郊区' },
]
const scopeOpts = scopes.filter((s) => s.v) // 新增时可选口径(不含"全部")
const scope = ref('')
const q = ref('')
const list = ref([])
const loading = ref(false)

const editing = ref(null) // SchoolDetail
const editId = ref(null)  // detail has no id field; track separately
const saving = ref(false)
const editMsg = ref('')

// 新增学校
const creating = ref(false)
const newSchool = ref(null)
const createMsg = ref('')
// 编辑弹层内新增年度
const newYear = ref('')

function blankSchool() {
  return {
    code: '', scope: 'city6', name: '', type: '', location_district: '',
    home_district: '', recruit_area: '', boarding: '', canteen: '',
    class_types: '', fee: '', dorm_fee: '', address: '', phone: '', remark: '',
  }
}

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
  editMsg.value = ''
  editId.value = item.id
  editing.value = await adminGetSchool(item.id)
}

async function saveStatic() {
  saving.value = true; editMsg.value = ''
  try {
    const e = editing.value
    await adminUpdateSchool(editId.value, {
      name: e.name, type: e.type, location_district: e.location_district,
      address: e.address, phone: e.phone, class_types: e.class_types,
    })
    editMsg.value = '已保存学校信息'
  } catch {
    editMsg.value = '保存失败'
  } finally {
    saving.value = false
  }
}

async function saveStat(st) {
  saving.value = true; editMsg.value = ''
  try {
    await adminUpsertStat(editId.value, {
      year: st.year, plan: num(st.plan), min_score: num(st.min_score),
      rank_city6: num(st.rank_city6), rank_whole: num(st.rank_whole),
    })
    editMsg.value = `已保存 ${st.year} 年录取数据`
  } catch {
    editMsg.value = '保存失败'
  } finally {
    saving.value = false
  }
}

async function removeStat(st) {
  if (!confirm(`确认删除 ${st.year} 年录取数据？`)) return
  saving.value = true; editMsg.value = ''
  try {
    editing.value = await adminDeleteStat(editId.value, st.year)
    editMsg.value = `已删除 ${st.year} 年数据`
  } catch (e) {
    editMsg.value = e.response?.data?.detail || '删除失败'
  } finally {
    saving.value = false
  }
}

function addYear() {
  const y = Number(newYear.value)
  if (!y || y < 2000 || y > 2100) { editMsg.value = '请输入有效年份'; return }
  if (editing.value.stats.some((s) => s.year === y)) { editMsg.value = '该年份已存在'; return }
  editing.value.stats.unshift({ year: y, plan: null, min_score: null, rank_city6: null, rank_whole: null })
  editing.value.stats.sort((a, b) => b.year - a.year)
  newYear.value = ''
}

async function removeSchool(item) {
  if (!confirm(`确认删除「${item.name}」(${item.code})？将一并删除其历年录取数据，且不可恢复。`)) return
  try {
    await adminDeleteSchool(item.id)
    if (editId.value === item.id) editing.value = null
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

function openCreate() {
  createMsg.value = ''
  newSchool.value = blankSchool()
  creating.value = true
}

async function submitCreate() {
  const n = newSchool.value
  if (!n.code || !n.name) { createMsg.value = '代码和名称必填'; return }
  saving.value = true; createMsg.value = ''
  try {
    // 清掉空字符串, 让后端存 null
    const payload = {}
    for (const k in n) payload[k] = n[k] === '' ? null : n[k]
    payload.code = n.code; payload.scope = n.scope; payload.name = n.name
    await adminCreateSchool(payload)
    creating.value = false
    await load()
  } catch (e) {
    createMsg.value = e.response?.data?.detail || '创建失败'
  } finally {
    saving.value = false
  }
}

function num(v) { return v === '' || v === null ? null : Number(v) }
</script>

<template>
  <h1>学校管理</h1>
  <div class="card">
    <div style="display:flex;gap:10px">
      <select v-model="scope" @change="load" style="flex:0 0 130px">
        <option v-for="s in scopes" :key="s.v" :value="s.v">{{ s.label }}</option>
      </select>
      <input v-model="q" placeholder="搜索名称/代码" @keyup.enter="load" />
      <button class="btn btn-sm" @click="load">搜索</button>
    </div>
    <button class="btn btn-sm" style="margin-top:10px" @click="openCreate">+ 新增学校</button>
  </div>

  <p v-if="loading" class="muted">加载中…</p>
  <p class="muted">共 {{ list.length }} 所</p>

  <div v-for="s in list" :key="s.id" class="school-item">
    <div style="flex:1;cursor:pointer" @click="openEdit(s)">
      <div class="name">{{ s.name }}</div>
      <div class="meta">{{ s.code }} · {{ s.type || '—' }} · {{ s.location_district || '' }}</div>
    </div>
    <div style="display:flex;align-items:center;gap:12px">
      <span class="rank muted" style="cursor:pointer" @click="openEdit(s)">编辑 ›</span>
      <span class="link-danger" @click.stop="removeSchool(s)">删除</span>
    </div>
  </div>

  <!-- 编辑弹层 -->
  <div v-if="editing" class="overlay" @click.self="editing = null">
    <div class="sheet">
      <h2>编辑 · {{ editing.name }}</h2>
      <div class="field"><label>名称</label><input v-model="editing.name" /></div>
      <div class="field"><label>类型</label><input v-model="editing.type" /></div>
      <div class="field"><label>所在区</label><input v-model="editing.location_district" /></div>
      <div class="field"><label>班型</label><input v-model="editing.class_types" /></div>
      <div class="field"><label>地址</label><input v-model="editing.address" /></div>
      <div class="field"><label>电话</label><input v-model="editing.phone" /></div>
      <button class="btn btn-sm" :disabled="saving" @click="saveStatic">保存学校信息</button>

      <h2 style="margin-top:18px">历年录取数据</h2>
      <div style="display:flex;gap:10px;margin-bottom:10px">
        <input v-model="newYear" type="number" placeholder="年份, 如 2026" />
        <button class="btn btn-ghost btn-sm" @click="addYear">+ 添加年份</button>
      </div>
      <div v-for="st in editing.stats" :key="st.year" class="card" style="background:#f7f8fa">
        <strong>{{ st.year }} 年</strong>
        <div class="field"><label>最低分</label><input v-model="st.min_score" type="number" /></div>
        <div class="field" v-if="editing.scope === 'city6'">
          <label>市区位次</label><input v-model="st.rank_city6" type="number" />
        </div>
        <div class="field"><label>全市位次</label><input v-model="st.rank_whole" type="number" /></div>
        <div class="field"><label>招生计划</label><input v-model="st.plan" type="number" /></div>
        <div style="display:flex;gap:10px">
          <button class="btn btn-ghost btn-sm" :disabled="saving" @click="saveStat(st)">
            保存 {{ st.year }} 年
          </button>
          <button class="btn btn-sm btn-danger" :disabled="saving" @click="removeStat(st)">
            删除
          </button>
        </div>
      </div>

      <p v-if="editMsg" style="color:var(--c-stable)">{{ editMsg }}</p>
      <button class="btn btn-ghost" style="margin-top:12px" @click="editing = null">关闭</button>
    </div>
  </div>

  <!-- 新增弹层 -->
  <div v-if="creating" class="overlay" @click.self="creating = false">
    <div class="sheet">
      <h2>新增学校</h2>
      <div class="field"><label>代码 *</label><input v-model="newSchool.code" placeholder="如 10199" /></div>
      <div class="field">
        <label>招生口径 *</label>
        <select v-model="newSchool.scope">
          <option v-for="s in scopeOpts" :key="s.v" :value="s.v">{{ s.label }}</option>
        </select>
      </div>
      <div class="field"><label>名称 *</label><input v-model="newSchool.name" /></div>
      <div class="field"><label>类型</label><input v-model="newSchool.type" placeholder="公办/民办" /></div>
      <div class="field"><label>所在区</label><input v-model="newSchool.location_district" /></div>
      <div class="field"><label>班型</label><input v-model="newSchool.class_types" /></div>
      <div class="field"><label>地址</label><input v-model="newSchool.address" /></div>
      <div class="field"><label>电话</label><input v-model="newSchool.phone" /></div>
      <p class="muted">提示：创建后在编辑页为其添加历年录取数据。</p>
      <button class="btn" :disabled="saving" @click="submitCreate">创建</button>
      <p v-if="createMsg" class="error">{{ createMsg }}</p>
      <button class="btn btn-ghost" style="margin-top:10px" @click="creating = false">取消</button>
    </div>
  </div>
</template>
