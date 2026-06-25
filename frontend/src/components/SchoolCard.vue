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
    shadow="never"
    class="school-card"
    :style="{ '--accent': borderColor[type] || 'transparent' }"
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
.school-card {
  cursor: pointer;
  border-left: 4px solid var(--accent) !important;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.school-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}
.school-card :deep(.el-card__body) { padding: 16px 18px; }
.row { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.left { min-width: 0; flex: 1; }
.name { font-weight: 600; font-size: 1.02rem; margin-bottom: 4px; color: var(--c-text); }
.tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 9px; }
.right { text-align: right; white-space: nowrap; flex-shrink: 0; }
.rank {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 4px;
}
.right .muted { font-size: 0.78rem; }
</style>
