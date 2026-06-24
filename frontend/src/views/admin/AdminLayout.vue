<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
function logout() {
  localStorage.removeItem('admin_token')
  router.replace('/admin/login')
}
</script>

<template>
  <el-container class="admin">
    <el-header class="admin-header">
      <div class="brand">志愿填报 · 管理后台</div>
      <el-menu mode="horizontal" router :default-active="$route.path" class="admin-menu" :ellipsis="false">
        <el-menu-item index="/admin/import">数据导入</el-menu-item>
        <el-menu-item index="/admin/schools">学校管理</el-menu-item>
        <el-menu-item index="/admin/config">阈值配置</el-menu-item>
      </el-menu>
      <div class="spacer" />
      <el-button text @click="logout">退出</el-button>
    </el-header>
    <el-main>
      <div class="page">
        <router-view />
      </div>
    </el-main>
  </el-container>
</template>

<style scoped>
.admin-header {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #fff;
  border-bottom: 1px solid var(--el-border-color);
  padding: 0 16px;
}
.brand { font-weight: 700; white-space: nowrap; }
.admin-menu { border-bottom: none; flex: 1; }
.spacer { flex: 0; }
.el-main { padding: 0; }
</style>
