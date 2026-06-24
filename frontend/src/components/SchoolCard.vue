<script setup>
// 推荐结果中的单个学校卡片(响应式网格内使用)
defineProps({
  s: { type: Object, required: true },
  cls: { type: String, default: '' }, // reach / stable / safe (左边框色)
})
const scopeLabel = { city6: '市内六区', whole: '全市', suburb: '郊区' }
</script>

<template>
  <div class="school-item" :class="cls">
    <div class="info">
      <div class="name">{{ s.name }}</div>
      <div class="meta">
        {{ scopeLabel[s.scope] }} · {{ s.type || '—' }}
        <template v-if="s.location_district"> · {{ s.location_district }}</template>
      </div>
      <div class="tags">
        <span v-if="s.class_types" class="tag" :title="s.class_types">
          {{ s.class_types.length > 12 ? s.class_types.slice(0, 12) + '…' : s.class_types }}
        </span>
        <span v-if="s.plan != null" class="tag">计划 {{ s.plan }}</span>
        <span v-if="s.boarding === '有'" class="tag">可住宿</span>
      </div>
    </div>
    <div class="rank">
      <div>录取位次 {{ s.school_rank }}</div>
      <div class="muted">最低分 {{ s.min_score ?? '—' }}</div>
    </div>
  </div>
</template>
