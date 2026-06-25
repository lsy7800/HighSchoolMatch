<script setup>
// 推荐结果中的单个学校卡片(Element Plus)
defineProps({
  s: { type: Object, required: true },
  type: { type: String, default: '' }, // el-tag/边框语义: reach/stable/safe
})
const scopeLabel = { city6: '市内六区', whole: '全市', suburb: '郊区' }
const borderColor = { reach: 'var(--c-reach)', stable: 'var(--c-stable)', safe: 'var(--c-safe)' }
</script>

<template>
  <el-card
    shadow="hover"
    class="school-card"
    :style="{ borderLeft: `4px solid ${borderColor[type] || 'transparent'}` }"
    @click="$emit('open')"
  >
    <div class="row">
      <div class="left">
        <div class="name">{{ s.name }}</div>
        <div class="muted">
          {{ scopeLabel[s.scope] }} · {{ s.type || '—' }}
          <template v-if="s.location_district"> · {{ s.location_district }}</template>
        </div>
        <div class="tags">
          <el-tag v-if="s.class_types" size="small" type="info" effect="plain">
            {{ s.class_types.length > 10 ? s.class_types.slice(0, 10) + '…' : s.class_types }}
          </el-tag>
          <el-tag v-if="s.plan != null" size="small" type="info" effect="plain">计划 {{ s.plan }}</el-tag>
          <el-tag v-if="s.boarding === '有'" size="small" type="info" effect="plain">可住宿</el-tag>
        </div>
      </div>
      <div class="right">
        <div class="rank">位次 {{ s.school_rank }}</div>
        <div class="muted">最低分 {{ s.min_score ?? '—' }}</div>
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.school-card { cursor: pointer; }
.school-card :deep(.el-card__body) { padding: 16px; }
.row { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.left { min-width: 0; flex: 1; }
.name { font-weight: 600; font-size: 1rem; margin-bottom: 4px; }
.tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
.right { text-align: right; white-space: nowrap; flex-shrink: 0; }
.rank { font-size: 0.9rem; font-weight: 600; color: #4a5057; margin-bottom: 4px; }
</style>
