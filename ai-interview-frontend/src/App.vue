<template>
  <div id="app">
    <nav class="navbar" v-if="authStore.token">
      <div class="nav-content">
        <router-link to="/dashboard" class="nav-logo"><span class="brand-mark">智</span><span>智面</span></router-link>
        <div class="nav-links">
          <router-link to="/dashboard">面试记录</router-link>
          <router-link to="/resume/upload">上传简历</router-link>
          <router-link to="/position-match">岗位匹配</router-link>
          <router-link to="/jobs">职位机会</router-link>
          <router-link to="/profile" class="nav-user-link">
            <img v-if="authStore.userAvatar && !avatarError" :src="authStore.userAvatar" class="nav-avatar" alt="avatar" @error="avatarError = true" />
            <span v-else class="nav-avatar-placeholder">{{ (authStore.userName || '个人').charAt(0) }}</span>
            <span>{{ authStore.userName || '个人中心' }}</span>
          </router-link>
          <button class="btn-secondary nav-logout" @click="logout">退出</button>
        </div>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'
import { getProfile } from './api/user'

const authStore = useAuthStore()
const router = useRouter()
const avatarError = ref(false)

onMounted(async () => {
  if (authStore.token) {
    try {
      const data = await getProfile()
      authStore.setUserInfo(data)
      avatarError.value = false
    } catch (e) {
      // 忽略
    }
  }
})

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  background: rgba(255, 255, 255, 0.76);
  border-bottom: 1px solid var(--color-border);
  backdrop-filter: blur(16px);
  padding: 0 20px;
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-content {
  max-width: 1040px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
}
.nav-logo {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-foreground);
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-mark {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border: 1px solid rgba(5, 150, 105, 0.2);
  font-weight: 800;
}
.nav-links {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}
.nav-links a {
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  border-radius: var(--radius-control);
  color: var(--color-muted);
  font-weight: 650;
  transition: background-color 160ms var(--ease-out), color 160ms var(--ease-out);
}
.nav-links a.router-link-active {
  color: var(--color-foreground);
  background: rgba(15, 23, 42, 0.05);
  font-weight: 600;
}
.nav-user {
  color: #6b7280;
  font-size: 13px;
}
.nav-user-link {
  color: var(--color-muted);
  font-size: 13px;
  transition: color 160ms var(--ease-out), background-color 160ms var(--ease-out);
  display: flex;
  align-items: center;
  gap: 6px;
}
.nav-user-link:hover {
  color: var(--color-foreground);
  background: rgba(15, 23, 42, 0.05);
}
.nav-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
}
.nav-avatar-placeholder {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 800;
}
.nav-logout {
  padding: 6px 14px;
  font-size: 13px;
}
</style>
