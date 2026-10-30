<template>
  <div class="container">
    <div class="page-header">
      <h1>面试记录</h1>
      <router-link to="/resume/upload" class="btn-primary action-link">
        开始新面试
      </router-link>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="interviews.length === 0" class="empty card">
      <p class="empty-mark">智</p>
      <p>还没有面试记录</p>
      <p style="color:#6b7280;font-size:14px;margin-top:8px">上传简历开始你的第一次 AI 模拟面试</p>
    </div>

    <div v-else class="interview-list">
      <div v-for="item in interviews" :key="item.interview_id" class="card interview-item">
        <div class="item-header">
          <span class="position">{{ item.target_position }}</span>
          <span :class="['status', item.status]">{{ item.status === 'completed' ? '已完成' : '进行中' }}</span>
        </div>
        <div class="item-meta">
          <span>难度：{{ difficultyMap[item.difficulty] || item.difficulty }}</span>
          <span>题数：{{ item.total_questions }}</span>
          <span v-if="item.overall_score">得分：{{ item.overall_score }}</span>
          <span>{{ formatDate(item.created_at) }}</span>
        </div>
        <div class="item-actions">
          <router-link v-if="item.status === 'in_progress'" :to="`/interview/${item.interview_id}`" class="btn-primary small-action">
            继续面试
          </router-link>
          <router-link v-else :to="`/interview/${item.interview_id}/report`" class="btn-secondary small-action">
            查看报告
          </router-link>
          <button class="btn-danger small-action" @click="handleDelete(item.interview_id)">
            删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getInterviews, deleteInterview } from '../api/interview'

const interviews = ref([])
const loading = ref(true)
const difficultyMap = { easy: '简单', medium: '中等', hard: '困难' }

function formatDate(str) {
  if (!str) return ''
  return new Date(str).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  try {
    const data = await getInterviews()
    interviews.value = data.items || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

async function handleDelete(interviewId) {
  if (!confirm('确定要删除这条面试记录吗？删除后无法恢复。')) return
  try {
    await deleteInterview(interviewId)
    interviews.value = interviews.value.filter(i => i.interview_id !== interviewId)
  } catch (e) {
    alert('删除失败: ' + e.message)
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 20px 0;
}
.page-header h1 {
  font-size: 26px;
  color: var(--color-foreground);
}
.action-link, .small-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.btn-primary.action-link,
.btn-primary.small-action {
  color: #fff;
}
.action-link {
  padding: 10px 24px;
}
.small-action {
  padding: 6px 16px;
  font-size: 13px;
  border-radius: 8px;
}
.loading, .empty {
  text-align: center;
  padding: 60px 20px;
}
.empty-mark {
  width: 54px;
  height: 54px;
  display: grid;
  place-items: center;
  margin: 0 auto 12px;
  border-radius: 16px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border: 1px solid rgba(5, 150, 105, .2);
  font-size: 24px;
  font-weight: 800;
}
.interview-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.interview-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: border-color 160ms var(--ease-out), transform 130ms var(--ease-out);
}
.interview-item:hover {
  border-color: var(--color-border-strong);
}
.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.position {
  font-weight: 600;
  font-size: 16px;
}
.status {
  font-size: 12px;
  padding: 5px 9px;
  border-radius: 999px;
  font-weight: 700;
  border: 1px solid transparent;
}
.status.completed {
  background: var(--color-success-soft);
  color: var(--color-success);
  border-color: rgba(4, 120, 87, .18);
}
.status.in_progress {
  background: var(--color-warning-soft);
  color: var(--color-warning);
  border-color: rgba(180, 83, 9, .18);
}
.item-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--color-muted);
}
.item-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
