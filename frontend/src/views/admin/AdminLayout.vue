<script setup>
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const isCollapse = ref(false)
const isMobile = ref(window.innerWidth < 768)

watch(
  () => route.path,
  () => {
    if (isMobile.value) isCollapse.value = true
  }
)

function onResize() {
  isMobile.value = window.innerWidth < 768
  if (isMobile.value) isCollapse.value = true
}
if (typeof window !== 'undefined') {
  window.addEventListener('resize', onResize)
}

function logout() {
  localStorage.removeItem('admin_token')
  router.replace('/admin/login')
}
</script>

<template>
  <el-container class="admin-shell">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="admin-aside">
      <div class="aside-brand">
        <span v-if="isCollapse" class="brand-mini">⚡</span>
        <span v-else class="brand-text">志愿填报 · 管理</span>
        <el-button
          v-if="!isMobile"
          link
          :icon="isCollapse ? 'Expand' : 'Fold'"
          class="toggle-btn"
          @click="isCollapse = !isCollapse"
        />
      </div>
      <el-menu
        :default-active="route.path"
        :collapse="isCollapse"
        router
        class="aside-menu"
      >
        <el-menu-item index="/admin/import">
          <el-icon><Upload /></el-icon>
          <template #title>数据导入</template>
        </el-menu-item>
        <el-menu-item index="/admin/schools">
          <el-icon><School /></el-icon>
          <template #title>学校管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/config">
          <el-icon><Setting /></el-icon>
          <template #title>阈值配置</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主区域 -->
    <el-container>
      <el-header class="admin-header">
        <el-button v-if="isMobile" link :icon="'Menu'" @click="isCollapse = !isCollapse" />
        <span class="header-title">{{ route.meta?.title || '' }}</span>
        <div class="spacer" />
        <el-button text @click="logout">
          <el-icon><SwitchButton /></el-icon>
          <span v-if="!isMobile">退出</span>
        </el-button>
      </el-header>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.admin-shell { height: 100vh; }
.admin-aside {
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  transition: width 0.25s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.aside-brand {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  border-bottom: 1px solid var(--el-border-color-light);
  font-weight: 700;
  gap: 4px;
  justify-content: space-between;
}
.brand-text { font-size: 0.95rem; white-space: nowrap; overflow: hidden; }
.brand-mini { font-size: 1.3rem; width: 100%; text-align: center; }
.toggle-btn { font-size: 1.1rem; }
.aside-menu { border-right: none; flex: 1; }
.admin-header {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 0 16px;
  height: 56px;
}
.header-title { font-weight: 600; color: #4a5057; }
.spacer { flex: 1; }
.admin-main {
  background: var(--c-bg);
  padding: 16px;
  overflow-y: auto;
}
@media (max-width: 767px) {
  .admin-aside { position: fixed; left: 0; top: 0; bottom: 0; z-index: 100; }
  .aside-brand { height: 56px; }
}
</style>
