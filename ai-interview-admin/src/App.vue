<template>
  <div class="admin-layout" v-if="authStore.isLoggedIn">
    <aside class="sidebar">
      <div class="sidebar-logo"><span class="brand-mark">智</span><span class="logo-text">智面</span></div>
      <div class="sidebar-subtitle">后台管理</div>
      <nav class="sidebar-nav">
        <router-link to="/" exact-active-class="active">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 13.5h5v6H4zM9.5 4.5h5v15h-5zM15 9h5v10.5h-5z" />
          </svg>
          数据概览
        </router-link>
        <router-link to="/users" active-class="active">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M8.5 11.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7ZM3.5 19.5c.6-3.3 2.4-5 5-5s4.4 1.7 5 5M16 11.5a3 3 0 1 0 0-6M15.5 14.5c2.6.2 4.2 1.9 4.7 5" />
          </svg>
          用户管理
        </router-link>
        <router-link to="/interviews" active-class="active">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 14.5a4 4 0 0 0 4-4v-3a4 4 0 1 0-8 0v3a4 4 0 0 0 4 4ZM5.5 10.5a6.5 6.5 0 0 0 13 0M12 17v3.5M8.5 20.5h7" />
          </svg>
          面试记录
        </router-link>
        <div class="nav-section">知识库 RAG</div>
        <router-link to="/question-bank" active-class="active">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M5 5.5c1.8-.8 3.5-.8 5.2.1.6.3 1.2.8 1.8 1.4.6-.6 1.2-1 1.8-1.4 1.7-.9 3.4-.9 5.2-.1v13c-1.8-.8-3.5-.8-5.2.1-.6.3-1.2.8-1.8 1.4-.6-.6-1.2-1-1.8-1.4-1.7-.9-3.4-.9-5.2-.1v-13Z" />
          </svg>
          题库管理
        </router-link>
        <router-link to="/knowledge" active-class="active">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M7 3.5h6.5L18 8v12.5H7zM13.5 3.5V8H18M9.5 12h5M9.5 15h5M9.5 18h3" />
          </svg>
          文档管理
        </router-link>
        <div class="nav-section">岗位匹配</div>
        <router-link to="/position-templates" active-class="active">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7M5 7.5h14v12H5zM5 11.5h14M10 14h4" />
          </svg>
          岗位模板
        </router-link>
        <router-link to="/external-data" active-class="active">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v18M3 12h18M5.6 5.6a9 9 0 1 0 12.8 12.8A9 9 0 0 0 5.6 5.6Z" /></svg>
          外部数据源
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <span>{{ authStore.email }}</span>
        <button class="logout-btn" @click="logout">退出登录</button>
      </div>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
  <router-view v-else />
</template>

<script setup>
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'
const authStore = useAuthStore()
const router = useRouter()
function logout() { authStore.logout(); router.push('/login') }
</script>

<style scoped>
.admin-layout { display: flex; min-height: 100vh; }

.sidebar {
  width: 230px;
  background: rgba(255,255,255,.82);
  color: var(--color-foreground);
  border-right: 1px solid var(--color-border);
  padding: 22px 16px;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0; left: 0; bottom: 0;
  overflow: hidden;
}

.sidebar-logo {
  font-size: 22px;
  font-weight: 700;
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
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

.logo-text {
  color: var(--color-foreground);
}

.sidebar-subtitle {
  font-size: 12px;
  color: var(--color-muted);
  margin-bottom: 32px;
  position: relative;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  position: relative;
}

.sidebar-nav a {
  padding: 10px 12px;
  border-radius: 10px;
  color: var(--color-muted);
  font-size: 14px;
  transition: background-color 160ms var(--ease-out), color 160ms var(--ease-out);
  display: flex;
  align-items: center;
  gap: 10px;
}

.sidebar-nav a:hover {
  background: rgba(15, 23, 42, 0.05);
  color: var(--color-foreground);
}

.sidebar-nav a.active {
  background: var(--color-primary-soft);
  color: var(--color-foreground);
  box-shadow: none;
}

.nav-icon {
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  padding: 6px;
  border-radius: 9px;
  color: var(--color-muted);
  background: transparent;
  transition: background-color 160ms var(--ease-out), color 160ms var(--ease-out);
}

.nav-icon path {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.sidebar-nav a:hover .nav-icon {
  background: rgba(15, 23, 42, 0.05);
  color: var(--color-foreground);
}

.sidebar-nav a.active .nav-icon {
  background: var(--color-primary);
  color: white;
}

.nav-section {
  font-size: 11px;
  color: var(--color-subtle);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 16px 14px 4px;
  font-weight: 600;
}

.sidebar-footer {
  font-size: 12px;
  color: var(--color-muted);
  border-top: 1px solid var(--color-border);
  padding-top: 16px;
  position: relative;
}

.logout-btn {
  display: block;
  width: 100%;
  margin-top: 10px;
  padding: 8px;
  border-radius: 8px;
  font-size: 13px;
  background: rgba(15, 23, 42, 0.04);
  color: var(--color-foreground);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: background-color 160ms var(--ease-out), border-color 160ms var(--ease-out), color 160ms var(--ease-out);
}

.logout-btn:hover {
  background: var(--color-danger-soft);
  color: var(--color-danger);
  border-color: rgba(185, 28, 28, 0.16);
}

.main-content {
  margin-left: 230px;
  flex: 1;
  min-width: 0;
  overflow-x: hidden;
  padding: 28px;
  background: transparent;
}
</style>
