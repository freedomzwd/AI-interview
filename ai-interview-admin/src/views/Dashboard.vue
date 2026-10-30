<template>
  <div>
    <h1 class="page-title">数据概览</h1>
    <div class="stats-grid">
      <router-link
        v-for="s in statCards"
        :key="s.key"
        class="stat-card"
        :to="s.to"
        :style="{ '--accent': s.color }"
        :aria-label="`查看${s.label}`"
      >
        <div class="stat-icon">{{ s.short }}</div>
        <div class="stat-num">{{ stats[s.key] }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { userApi } from '../api'

const stats = ref({ user_count: 0, resume_count: 0, interview_count: 0, completed_interview_count: 0 })

const statCards = [
  { key: 'user_count', label: '注册用户', short: '用', color: 'var(--color-primary)', to: '/users' },
  { key: 'resume_count', label: '上传简历', short: '历', color: '#0f766e', to: '/users' },
  { key: 'interview_count', label: '面试总数', short: '面', color: '#65a30d', to: '/interviews' },
  { key: 'completed_interview_count', label: '已完成面试', short: '完', color: 'var(--color-success)', to: '/interviews?status=completed' }
]

onMounted(async () => {
  try { stats.value = await userApi.stats() } catch (e) { console.error(e) }
})
</script>

<style scoped>
.page-title { font-size: 22px; margin-bottom: 24px; color: var(--color-foreground); }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }

.stat-card {
  background: var(--color-surface);
  border-radius: var(--radius-card);
  padding: 24px;
  position: relative;
  overflow: hidden;
  color: inherit;
  text-decoration: none;
  cursor: pointer;
  transition:
    transform 180ms var(--ease-out),
    border-color 180ms var(--ease-out),
    box-shadow 180ms var(--ease-out);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: var(--accent);
}

.stat-card:hover {
  transform: translateY(-2px);
  border-color: rgba(5, 150, 105, 0.28);
}

.stat-card:focus-visible {
  outline: 3px solid var(--color-focus);
  outline-offset: 3px;
}

.stat-icon {
  width: 34px; height: 34px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  background: var(--color-primary-soft); color: var(--accent);
  border: 1px solid rgba(5, 150, 105, 0.16);
  font-size: 14px; font-weight: 800; margin-bottom: 18px;
}
.stat-num { font-size: 40px; font-weight: 700; color: var(--accent); }
.stat-label { font-size: 14px; color: var(--color-muted); margin-top: 4px; }
@media (max-width: 960px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 560px) { .stats-grid { grid-template-columns: 1fr; } }
</style>
