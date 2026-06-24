<script setup>
// 学生端外壳: 顶部导航栏 + 内容区
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<template>
  <div class="public-shell">
    <header class="topbar">
      <div class="topbar-inner">
        <router-link to="/" class="brand">
          <el-icon><School /></el-icon>
          <span>天津中考志愿助手</span>
        </router-link>
        <nav class="nav">
          <router-link to="/" :class="{ active: route.name === 'home' }">志愿推荐</router-link>
          <router-link to="/score-rank" :class="{ active: route.name === 'score-rank' }">一分一段表</router-link>
          <router-link to="/admin" class="admin-link">管理后台</router-link>
        </nav>
      </div>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.public-shell { min-height: 100vh; }
.topbar {
  background: #fff;
  border-bottom: 1px solid var(--el-border-color-light);
  position: sticky;
  top: 0;
  z-index: 50;
}
.topbar-inner {
  max-width: 1100px;
  margin: 0 auto;
  height: 56px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 24px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  font-size: 1.05rem;
  color: var(--el-color-primary);
  text-decoration: none;
  white-space: nowrap;
}
.nav {
  display: flex;
  gap: 4px;
  margin-left: auto;
  align-items: center;
}
.nav a {
  padding: 6px 12px;
  border-radius: 8px;
  color: #4a5057;
  text-decoration: none;
  font-size: 0.95rem;
  transition: background 0.15s, color 0.15s;
}
.nav a:hover { background: var(--el-color-primary-light-9); }
.nav a.active { color: var(--el-color-primary); font-weight: 600; background: var(--el-color-primary-light-9); }
.nav a.admin-link { color: var(--c-muted); }
@media (max-width: 480px) {
  .brand span { display: none; }
  .topbar-inner { gap: 8px; }
  .nav a { padding: 6px 8px; font-size: 0.88rem; }
}
</style>
