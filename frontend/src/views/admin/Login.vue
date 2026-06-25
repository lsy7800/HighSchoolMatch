<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { adminLogin } from '../../api'

const router = useRouter()
const route = useRoute()
const username = ref('admin')
const password = ref('')
const loading = ref(false)

async function login() {
  loading.value = true
  try {
    const { access_token } = await adminLogin(username.value, password.value)
    localStorage.setItem('admin_token', access_token)
    router.replace(route.query.redirect || '/admin/import')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page page--narrow login-page">
    <el-card shadow="never">
      <h2 class="login-title">管理后台登录</h2>
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="用户名">
          <el-input v-model="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" type="password" show-password @keyup.enter="login" />
        </el-form-item>
        <el-button type="primary" style="width:100%" :loading="loading" @click="login">登录</el-button>
      </el-form>
      <div class="back">
        <el-link @click="router.push('/')">← 返回查询页</el-link>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.login-page {
  margin-top: 10vh;
  display: flex;
  justify-content: center;
}
.login-page :deep(.el-card) {
  width: 100%;
  border-radius: 16px;
  box-shadow: var(--shadow-hover);
}
.login-page :deep(.el-card__body) { padding: 32px 28px 24px; }
.login-title {
  text-align: center;
  margin: 0 0 24px;
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--c-text);
}
.login-title::before {
  content: '';
  display: block;
  width: 44px;
  height: 44px;
  margin: 0 auto 14px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--el-color-primary), #6f7ff2);
  box-shadow: 0 6px 14px rgba(58, 109, 240, 0.35);
}
.back { text-align: center; margin-top: 16px; }
</style>
