<script setup>
import { ref, onMounted } from 'vue'
import { adminListSchools, adminGetSchool, adminUpdateSchool, adminUpsertStat } from '../../api'

const scopes = [
  { v: '', label: '全部' },
  { v: 'city6', label: '市内六区' },
  { v: 'whole', label: '全市' },
  { v: 'suburb', label: '郊区' },
]
const scope = ref('')
const q = ref('')
const list = ref([])
const loading = ref(false)

const editing = ref(null) // SchoolDetail
const editId = ref(null)  // detail has no id field; track separately
const saving = ref(false)
const editMsg = ref('')

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
  </div>

  <p v-if="loading" class="muted">加载中…</p>
  <p class="muted">共 {{ list.length }} 所</p>

  <div v-for="s in list" :key="s.id" class="school-item" @click="openEdit(s)">
    <div>
      <div class="name">{{ s.name }}</div>
      <div class="meta">{{ s.code }} · {{ s.type || '—' }} · {{ s.location_district || '' }}</div>
    </div>
    <div class="rank muted">编辑 ›</div>
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
      <div v-for="st in editing.stats" :key="st.year" class="card" style="background:#f7f8fa">
        <strong>{{ st.year }} 年</strong>
        <div class="field"><label>最低分</label><input v-model="st.min_score" type="number" /></div>
        <div class="field" v-if="editing.scope === 'city6'">
          <label>市区位次</label><input v-model="st.rank_city6" type="number" />
        </div>
        <div class="field"><label>全市位次</label><input v-model="st.rank_whole" type="number" /></div>
        <div class="field"><label>招生计划</label><input v-model="st.plan" type="number" /></div>
        <button class="btn btn-ghost btn-sm" :disabled="saving" @click="saveStat(st)">
          保存 {{ st.year }} 年
        </button>
      </div>

      <p v-if="editMsg" style="color:var(--c-stable)">{{ editMsg }}</p>
      <button class="btn btn-ghost" style="margin-top:12px" @click="editing = null">关闭</button>
    </div>
  </div>
</template>
