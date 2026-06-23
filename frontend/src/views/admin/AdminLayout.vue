<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
function logout() {
  localStorage.removeItem('admin_token')
  router.replace('/admin/login')
}
</script>

<template>
  <div>
    <nav class="topbar">
      <router-link to="/admin/import">数据导入</router-link>
      <router-link to="/admin/schools">学校管理</router-link>
      <router-link to="/admin/config">阈值配置</router-link>
      <span class="spacer"></span>
      <a href="#" @click.prevent="logout">退出</a>
    </nav>
    <div class="page">
      <router-view />
    </div>
  </div>
</template>
