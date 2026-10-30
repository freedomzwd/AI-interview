<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand-mark">智</div>
      <h2>智面后台</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="email" type="email" placeholder="admin@ai-interview.com" required />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" placeholder="密码" required />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="btn-primary login-submit" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { authApi } from '../api'

const router = useRouter()
const authStore = useAuthStore()
const email = ref('admin@ai-interview.com')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''; loading.value = true
  try {
    const data = await authApi.login(email.value, password.value)
    authStore.setAuth({ ...data, email: email.value })
    router.push('/')
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}
</script>

<style scoped>
.login-page { display: flex; align-items: center; justify-content: center; min-height: 100vh; background: var(--color-background); }
.login-card { width: min(400px, calc(100vw - 32px)); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-card); padding: 40px 36px; text-align: center; box-shadow: var(--shadow-card); }
.brand-mark { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; margin: 0 auto 14px; background: var(--color-primary-soft); border: 1px solid rgba(5, 150, 105, 0.18); color: var(--color-primary); font-weight: 800; font-size: 20px; }
.login-card h2 { font-size: 24px; color: var(--color-foreground); margin-bottom: 28px; }
.form-group { margin-bottom: 18px; text-align: left; }
.form-group label { display: block; margin-bottom: 6px; font-size: 14px; font-weight: 600; color: var(--color-foreground); }
.form-group input { width: 100%; padding: 11px 14px; }
.error { color: var(--color-danger); font-size: 13px; margin-bottom: 12px; }
.login-submit { width: 100%; padding: 12px; font-size: 15px; }
.login-submit:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

@media (max-width: 420px) {
  .login-card { padding: 36px 28px; }
}
</style>
