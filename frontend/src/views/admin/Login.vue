<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { adminLogin } from '../../api'

const router = useRouter()
const route = useRoute()
const username = ref('admin')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function login() {
  error.value = ''
  loading.value = true
  try {
    const { access_token } = await adminLogin(username.value, password.value)
    localStorage.setItem('admin_token', access_token)
    router.replace(route.query.redirect || '/admin/import')
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page page--narrow">
    <h1>管理后台登录</h1>
    <div class="card">
      <div class="field">
        <label>用户名</label>
        <input v-model="username" />
      </div>
      <div class="field">
        <label>密码</label>
        <input v-model="password" type="password" @keyup.enter="login" />
      </div>
      <button class="btn" :disabled="loading" @click="login">
        {{ loading ? '登录中…' : '登录' }}
      </button>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
    <p class="muted" style="text-align:center">
      <router-link to="/">← 返回查询页</router-link>
    </p>
  </div>
</template>
