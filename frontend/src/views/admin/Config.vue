<script setup>
import { ref, onMounted } from 'vue'
import { adminGetConfig, adminUpdateConfig } from '../../api'

const labels = {
  stable_margin: '稳档位次比容差 (±, 如0.10=±10%)',
  safe_floor: '保档下限 (低于此ratio不再推荐)',
  reach_ceiling: '冲档上限 (高于此ratio不再推荐)',
}
const cfg = ref({})
const msg = ref('')
const err = ref('')
const saving = ref(false)

onMounted(async () => {
  cfg.value = await adminGetConfig()
})

async function save() {
  saving.value = true; msg.value = ''; err.value = ''
  try {
    const values = {}
    for (const k in cfg.value) values[k] = Number(cfg.value[k])
    cfg.value = await adminUpdateConfig(values)
    msg.value = '已保存'
  } catch (e) {
    err.value = e.response?.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <h1>阈值配置</h1>
  <p class="muted">调整冲/稳/保的划分阈值，立即影响匹配结果。</p>
  <div class="card">
    <div class="field" v-for="(v, k) in cfg" :key="k">
      <label>{{ labels[k] || k }}</label>
      <input v-model="cfg[k]" type="number" step="0.01" />
    </div>
    <button class="btn" :disabled="saving" @click="save">保存</button>
    <p v-if="msg" style="color:var(--c-stable);margin-top:8px">{{ msg }}</p>
    <p v-if="err" class="error">{{ err }}</p>
  </div>
</template>
