<script setup>
import { reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminImport } from '../../api'

const kinds = [
  { key: 'score-rank', label: '一分档', hint: '上传当年一分档 xlsx，按年份替换' },
  { key: 'schools', label: '高中数据', hint: '上传三-sheet 高中数据 xlsx，全量替换' },
]

// 每类一份状态
const state = reactive({
  'score-rank': { file: null, preview: null, busy: false },
  schools: { file: null, preview: null, busy: false },
})

function onChange(kind, uploadFile) {
  state[kind].file = uploadFile.raw
  state[kind].preview = null
}

async function doPreview(kind) {
  const s = state[kind]
  if (!s.file) return ElMessage.warning('请先选择文件')
  s.busy = true
  try {
    const res = await adminImport(kind, s.file, false)
    s.preview = res.preview
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '解析失败')
  } finally {
    s.busy = false
  }
}

async function doCommit(kind) {
  const s = state[kind]
  if (!s.file) return
  try {
    await ElMessageBox.confirm('确认导入并替换现有数据？此操作会覆盖对应数据。', '确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  s.busy = true
  try {
    const res = await adminImport(kind, s.file, true)
    ElMessage.success('导入成功：' + JSON.stringify(res.imported))
    s.preview = null
    s.file = null
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导入失败')
  } finally {
    s.busy = false
  }
}
</script>

<template>
  <h2 class="admin-page-title">数据导入</h2>
  <p class="admin-page-sub">先「预览」核对解析结果，再「确认导入」。每年新数据到位后在此替换即可。</p>

  <el-row :gutter="16">
    <el-col v-for="k in kinds" :key="k.key" :xs="24" :md="12">
      <el-card shadow="never" style="margin-bottom:16px">
        <template #header>
          <b>{{ k.label }}</b>
          <span class="muted">　{{ k.hint }}</span>
        </template>

        <el-upload
          drag
          :auto-upload="false"
          :show-file-list="true"
          :limit="1"
          accept=".xlsx"
          :on-change="(f) => onChange(k.key, f)"
          :on-exceed="(files) => onChange(k.key, { raw: files[0] })"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">拖拽文件到此处，或<em>点击选择</em> .xlsx</div>
        </el-upload>

        <div style="margin-top:12px;display:flex;gap:10px">
          <el-button :loading="state[k.key].busy" @click="doPreview(k.key)">预览</el-button>
          <el-button type="primary" :loading="state[k.key].busy" :disabled="!state[k.key].preview" @click="doCommit(k.key)">
            确认导入
          </el-button>
        </div>

        <el-alert
          v-if="state[k.key].preview"
          type="success"
          :closable="false"
          style="margin-top:12px"
        >
          解析结果：{{ JSON.stringify(state[k.key].preview) }}
        </el-alert>
      </el-card>
    </el-col>
  </el-row>
</template>
