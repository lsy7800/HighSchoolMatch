<script setup>
import { ref, watch } from 'vue'
import { getSchool } from '../api'

const props = defineProps({ code: String })
const emit = defineEmits(['close'])

const loading = ref(false)
const channels = ref([]) // 一个 code 可能有多条招生线
const error = ref('')

const scopeLabel = { city6: '市内六区', whole: '全市', suburb: '郊区' }

watch(
  () => props.code,
  async (code) => {
    if (!code) return
    loading.value = true
    error.value = ''
    try {
      channels.value = await getSchool(code)
    } catch (e) {
      error.value = '加载失败'
    } finally {
      loading.value = false
    }
  },
  { immediate: true }
)
</script>

<template>
  <div class="overlay" @click.self="emit('close')">
    <div class="sheet">
      <div v-if="loading" class="muted">加载中…</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <template v-else v-for="(s, i) in channels" :key="i">
        <h2>{{ s.name }}</h2>
        <p class="muted">
          {{ scopeLabel[s.scope] }}招生 · {{ s.type || '—' }} ·
          {{ s.location_district || '' }}
        </p>
        <p v-if="s.address" class="muted">📍 {{ s.address }}</p>
        <p v-if="s.phone" class="muted">☎ {{ s.phone }}</p>
        <p v-if="s.class_types" class="muted">班型：{{ s.class_types }}</p>

        <h2 style="margin-top:16px">历年录取</h2>
        <table>
          <thead>
            <tr>
              <th>年份</th><th>计划</th><th>最低分</th>
              <th v-if="s.scope === 'city6'">市区位次</th>
              <th>全市位次</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="st in s.stats" :key="st.year">
              <td>{{ st.year }}</td>
              <td>{{ st.plan ?? '—' }}</td>
              <td>{{ st.min_score ?? '—' }}</td>
              <td v-if="s.scope === 'city6'">{{ st.rank_city6 ?? '—' }}</td>
              <td>{{ st.rank_whole ?? '—' }}</td>
            </tr>
          </tbody>
        </table>
        <hr v-if="i < channels.length - 1" style="margin:18px 0;border:none;border-top:1px solid var(--c-border)" />
      </template>

      <button class="btn btn-ghost" style="margin-top:18px" @click="emit('close')">
        关闭
      </button>
    </div>
  </div>
</template>
