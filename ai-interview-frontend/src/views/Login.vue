<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="brand-title"><span class="brand-mark">智</span><h2>智面</h2></div>
      <p class="subtitle">模拟面试与岗位匹配平台</p>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="email" type="email" placeholder="请输入邮箱" required />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" placeholder="请输入密码" required />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="btn-glow" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      <p class="auth-link">还没有账号？<router-link to="/register">立即注册</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { login } from '../api/auth'
import { getProfile } from '../api/user'

const router = useRouter()
const authStore = useAuthStore()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const data = await login(email.value, password.value)
    authStore.setAuth(data)
    // 登录后立刻获取完整用户信息（含头像）
    try {
      const profile = await getProfile()
      authStore.setUserInfo(profile)
    } catch (_) {}
    router.push('/dashboard')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: transparent;
}
.auth-card {
  width: min(400px, calc(100vw - 32px));
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: 40px 36px;
  text-align: center;
  box-shadow: var(--shadow-card);
}

@media (max-width: 420px) {
  .auth-card { padding: 36px 28px; }
}
.brand-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}
.brand-mark {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border: 1px solid rgba(5, 150, 105, 0.2);
  font-weight: 800;
}
.auth-card h2 {
  font-size: 28px;
  color: var(--color-foreground);
  margin-bottom: 4px;
}
.subtitle {
  color: var(--color-muted);
  margin-bottom: 28px;
  font-size: 14px;
}
.form-group {
  margin-bottom: 18px;
  text-align: left;
}
.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-foreground);
}
.form-group input {
  width: 100%;
  padding: 11px 14px;
  border: 1px solid #cbd5e1;
  border-radius: var(--radius-control);
  font-size: 14px;
  outline: none;
  transition: border-color 160ms var(--ease-out), box-shadow 160ms var(--ease-out), background-color 160ms var(--ease-out);
  background: rgba(255, 255, 255, 0.86);
}
.form-group input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-focus);
  background: white;
}
.error {
  color: var(--color-danger);
  font-size: 13px;
  margin-bottom: 12px;
}
.btn-glow {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-control);
  font-size: 15px;
  font-weight: 600;
  color: white;
  background: var(--color-primary);
  cursor: pointer;
  transition: transform 130ms var(--ease-out), background-color 160ms var(--ease-out), border-color 160ms var(--ease-out);
}
.btn-glow:hover {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}
.btn-glow:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}
.auth-link {
  margin-top: 18px;
  font-size: 14px;
  color: var(--color-muted);
}
.auth-link a {
  color: var(--color-primary);
  font-weight: 500;
}
</style>
