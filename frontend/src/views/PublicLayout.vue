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
          <router-link to="/schools" :class="{ active: route.name === 'schools' }">学校一览</router-link>
          <router-link to="/" :class="{ active: route.name === 'home' }">志愿推荐</router-link>
          <router-link to="/chat" :class="{ active: route.name === 'chat' }">智能问答</router-link>
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
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: saturate(180%) blur(12px);
  -webkit-backdrop-filter: saturate(180%) blur(12px);
  border-bottom: 1px solid var(--c-border);
  position: sticky;
  top: 0;
  z-index: 50;
}
.topbar-inner {
  max-width: 1100px;
  margin: 0 auto;
  height: 60px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  gap: 24px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 1.08rem;
  color: var(--el-color-primary);
  text-decoration: none;
  white-space: nowrap;
  letter-spacing: 0.01em;
}
.brand .el-icon {
  font-size: 1.25rem;
}
.nav {
  display: flex;
  gap: 4px;
  margin-left: auto;
  align-items: center;
}
.nav a {
  padding: 7px 14px;
  border-radius: 9px;
  color: var(--c-text-2);
  text-decoration: none;
  font-size: 0.95rem;
  transition: background 0.18s, color 0.18s;
}
.nav a:hover { background: var(--el-color-primary-light-9); color: var(--el-color-primary); }
.nav a.active {
  color: var(--el-color-primary);
  font-weight: 600;
  background: var(--el-color-primary-light-9);
}
.nav a.admin-link { color: var(--c-muted); }
.nav a.admin-link:hover { color: var(--el-color-primary); }
@media (max-width: 480px) {
  .brand span { display: none; }
  .topbar-inner { gap: 8px; padding: 0 14px; }
  .nav a { padding: 6px 10px; font-size: 0.88rem; }
}
</style>
