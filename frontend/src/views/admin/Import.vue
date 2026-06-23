<script setup>
import { ref } from 'vue'
import { adminImport } from '../../api'

// 两类导入: 一分档(score-rank) / 高中数据(schools)
const kinds = [
  { key: 'score-rank', label: '一分档 (score-rank)', hint: '上传当年一分档 xlsx，按年份替换' },
  { key: 'schools', label: '高中数据 (schools)', hint: '上传三-sheet 高中数据 xlsx，全量替换' },
]

const state = ref({})

function pick(kind, e) {
  state.value[kind] = { file: e.target.files[0], preview: null, msg: '', err: '', busy: false }
}

async function doPreview(kind) {
  const s = state.value[kind]
  if (!s?.file) return
  s.busy = true; s.err = ''; s.msg = ''
  try {
    const res = await adminImport(kind, s.file, false)
    s.preview = res.preview
  } catch (e) {
    s.err = e.response?.data?.detail || '解析失败'
  } finally {
    s.busy = false
  }
}

async function doCommit(kind) {
  const s = state.value[kind]
  if (!s?.file) return
  if (!confirm('确认导入并替换现有数据？此操作会覆盖对应数据。')) return
  s.busy = true; s.err = ''; s.msg = ''
  try {
    const res = await adminImport(kind, s.file, true)
    s.msg = '导入成功：' + JSON.stringify(res.imported)
    s.preview = null
  } catch (e) {
    s.err = e.response?.data?.detail || '导入失败'
  } finally {
    s.busy = false
  }
}
</script>

<template>
  <h1>数据导入</h1>
  <p class="muted">先「预览」核对解析结果，再「确认导入」。每年新数据到位后在此替换即可。</p>

  <div class="card" v-for="k in kinds" :key="k.key">
    <h2>{{ k.label }}</h2>
    <p class="muted">{{ k.hint }}</p>
    <div class="field">
      <input type="file" accept=".xlsx" @change="pick(k.key, $event)" />
    </div>
    <div style="display:flex;gap:10px">
      <button class="btn btn-ghost btn-sm" :disabled="state[k.key]?.busy" @click="doPreview(k.key)">
        预览
      </button>
      <button class="btn btn-sm" :disabled="state[k.key]?.busy || !state[k.key]?.preview" @click="doCommit(k.key)">
        确认导入
      </button>
    </div>
    <pre v-if="state[k.key]?.preview" class="card" style="background:#f0f4ff;margin-top:10px;overflow-x:auto">{{ state[k.key].preview }}</pre>
    <p v-if="state[k.key]?.msg" style="color:var(--c-stable);margin-top:8px">{{ state[k.key].msg }}</p>
    <p v-if="state[k.key]?.err" class="error">{{ state[k.key].err }}</p>
  </div>
</template>
