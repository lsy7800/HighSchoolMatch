<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminGetConfig, adminUpdateConfig } from '../../api'

const labels = {
  stable_margin: '稳档位次比容差（±，如 0.10 = ±10%）',
  safe_floor: '保档下限（低于此 ratio 不再推荐）',
  reach_ceiling: '冲档上限（高于此 ratio 不再推荐）',
}
const cfg = ref({})
const saving = ref(false)

onMounted(async () => {
  cfg.value = await adminGetConfig()
})

async function save() {
  saving.value = true
  try {
    const values = {}
    for (const k in cfg.value) values[k] = Number(cfg.value[k])
    cfg.value = await adminUpdateConfig(values)
    ElMessage.success('已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <h2 class="admin-page-title">阈值配置</h2>
  <p class="admin-page-sub">调整冲/稳/保的划分阈值，立即影响匹配结果。</p>

  <el-card shadow="never" style="max-width:560px">
    <el-form label-position="top">
      <el-form-item v-for="(v, k) in cfg" :key="k" :label="labels[k] || k">
        <el-input-number v-model="cfg[k]" :step="0.01" :precision="2" :min="0" style="width:200px" />
      </el-form-item>
      <el-button type="primary" :loading="saving" @click="save">保存</el-button>
    </el-form>
  </el-card>
</template>
