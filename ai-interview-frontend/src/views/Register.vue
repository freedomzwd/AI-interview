<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="brand-title"><span class="brand-mark">智</span><h2>注册智面</h2></div>
      <p class="subtitle">创建账号开始模拟面试</p>
      <form @submit.prevent="handleRegister">
        <div class="form-row">
          <div class="form-group">
            <label>名</label>
            <input v-model="form.first_name" placeholder="名" required />
          </div>
          <div class="form-group">
            <label>姓</label>
            <input v-model="form.last_name" placeholder="姓" required />
          </div>
        </div>
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="form.email" type="email" placeholder="请输入邮箱" required />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="form.password" type="password" placeholder="至少8位，含字母+数字+特殊字符" required />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="success">{{ success }}</p>
        <button type="submit" class="btn-glow" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>
      <p class="auth-link">已有账号？<router-link to="/login">去登录</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { register } from '../api/auth'

const router = useRouter()
const authStore = useAuthStore()
const form = reactive({ first_name: '', last_name: '', email: '', password: '' })
const error = ref('')
const success = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''; success.value = ''; loading.value = true
  try {
    const res = await register(form)
    // 注册成功直接登录
    authStore.setAuth(res)
    success.value = '注册成功，正在跳转...'
    setTimeout(() => router.push('/dashboard'), 800)
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}
</script>

<style scoped>
.auth-page { display: flex; align-items: center; justify-content: center; min-height: 100vh; background: transparent; }
.auth-card { width: 420px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-card); padding: 36px; text-align: center; box-shadow: var(--shadow-card); }
.brand-title { display: flex; align-items: center; justify-content: center; gap: 10px; }
.brand-mark { width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center; color: var(--color-primary); background: var(--color-primary-soft); border: 1px solid rgba(5, 150, 105, 0.2); font-weight: 800; }
.auth-card h2 { font-size: 24px; color: var(--color-foreground); margin-bottom: 4px; }
.subtitle { color: var(--color-muted); margin-bottom: 24px; font-size: 14px; }
.form-row { display: flex; gap: 12px; }
.form-group { margin-bottom: 16px; text-align: left; flex: 1; }
.form-group label { display: block; margin-bottom: 6px; font-size: 14px; font-weight: 600; color: var(--color-foreground); }
.form-group input { width: 100%; padding: 11px 14px; border: 1px solid #cbd5e1; border-radius: var(--radius-control); font-size: 14px; outline: none; transition: border-color 160ms var(--ease-out), box-shadow 160ms var(--ease-out), background-color 160ms var(--ease-out); background: rgba(255,255,255,.86); }
.form-group input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-focus); background: white; }
.error { color: var(--color-danger); font-size: 13px; margin-bottom: 12px; }
.success { color: var(--color-success); font-size: 13px; margin-bottom: 12px; }
.btn-glow { width: 100%; padding: 12px; border: 1px solid var(--color-primary); border-radius: var(--radius-control); font-size: 15px; font-weight: 700; color: white; background: var(--color-primary); cursor: pointer; transition: transform 130ms var(--ease-out), background-color 160ms var(--ease-out), border-color 160ms var(--ease-out); }
.btn-glow:hover { background: var(--color-primary-hover); border-color: var(--color-primary-hover); }
.btn-glow:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
.auth-link { margin-top: 18px; font-size: 14px; color: var(--color-muted); }
.auth-link a { color: var(--color-primary); font-weight: 600; }
</style>
