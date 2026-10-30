<template>
  <main class="container">
    <header class="page-header">
      <div>
        <h1>职位机会</h1>
        <p>来自公开企业职位 API 的实时岗位，点击后前往来源页面投递。</p>
      </div>
      <span class="result-count">{{ total }} 个岗位</span>
    </header>

    <section class="filters" aria-label="职位筛选">
      <input v-model="search" placeholder="搜索公司、职位或地点" @input="debouncedReload" />
      <select v-model="provider" @change="reload">
        <option value="">全部来源</option>
        <option value="remotive">Remotive</option>
        <option value="greenhouse">Greenhouse</option>
      </select>
    </section>

    <section v-if="loading" class="empty-state">正在加载真实职位数据...</section>
    <section v-else-if="!items.length" class="empty-state">暂时没有符合条件的职位，请稍后刷新。</section>
    <section v-else class="jobs-list">
      <article v-for="job in items" :key="job.id" class="job-item">
        <div class="job-main">
          <div class="job-heading">
            <div>
              <p class="company">{{ job.company }}</p>
              <h2>{{ job.title }}</h2>
            </div>
            <span class="source">{{ providerLabel(job.provider) }}</span>
          </div>
          <div class="job-meta">
            <span v-if="job.location">{{ job.location }}</span>
            <span v-if="job.work_type">{{ job.work_type === 'remote' ? '远程' : job.work_type }}</span>
            <span v-if="job.employment_type">{{ job.employment_type }}</span>
            <span v-if="job.published_at">发布于 {{ formatDate(job.published_at) }}</span>
          </div>
          <p v-if="job.description" class="description">{{ job.description }}</p>
          <div v-if="job.tags?.length" class="tags">
            <span v-for="tag in job.tags.slice(0, 6)" :key="tag">{{ tag }}</span>
          </div>
        </div>
        <a class="apply-link" :href="job.apply_url" target="_blank" rel="noopener noreferrer">查看并投递</a>
      </article>
    </section>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getJobs } from '../api/jobs'

const items = ref([])
const total = ref(0)
const loading = ref(true)
const route = useRoute()
const search = ref(typeof route.query.search === 'string' ? route.query.search : '')
const provider = ref('')
let timer

function providerLabel(value) { return { remotive: 'Remotive', greenhouse: 'Greenhouse' }[value] || value }
function formatDate(value) { return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium' }).format(new Date(value)) }
function debouncedReload() { clearTimeout(timer); timer = setTimeout(reload, 300) }
async function reload() {
  loading.value = true
  try {
    const data = await getJobs({ page: 1, per_page: 30, search: search.value || undefined, provider: provider.value || undefined })
    items.value = data.items || []
    total.value = data.total || 0
  } finally { loading.value = false }
}
onMounted(reload)
</script>

<style scoped>
.container { max-width: 1040px; margin: 0 auto; padding: 28px 24px 48px; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; margin-bottom: 20px; }
h1 { font-size: 24px; margin-bottom: 7px; } .page-header p { color: #64748b; font-size: 14px; }
.result-count, .source { border: 1px solid rgba(5, 150, 105, .2); background: var(--color-primary-soft); color: var(--color-primary); border-radius: 999px; padding: 5px 9px; font-size: 12px; font-weight: 700; white-space: nowrap; }
.filters { display: flex; gap: 10px; margin-bottom: 16px; } .filters input { width: min(400px, 100%); } .filters select { min-width: 130px; }
.jobs-list { display: grid; gap: 10px; }.job-item { background: rgba(255,255,255,.9); border: 1px solid var(--color-border); border-radius: var(--radius-inner); padding: 18px; display: flex; gap: 20px; justify-content: space-between; box-shadow: var(--shadow-soft); }
.job-main { min-width: 0; }.job-heading { display: flex; gap: 12px; align-items: flex-start; justify-content: space-between; }.company { color: var(--color-primary); font-size: 13px; font-weight: 700; margin-bottom: 3px; }.job-heading h2 { font-size: 17px; color: #0f172a; }.job-meta { display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 10px 0; color: #64748b; font-size: 13px; }.job-meta span + span { border-left: 1px solid #cbd5e1; padding-left: 14px; }.description { color: #475569; font-size: 14px; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }.tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 12px; }.tags span { background: #f1f5f9; border-radius: 5px; color: #475569; font-size: 12px; padding: 4px 7px; }.apply-link { flex: 0 0 auto; align-self: center; border: 1px solid var(--color-primary); border-radius: var(--radius-control); color: white; background: var(--color-primary); padding: 9px 12px; font-size: 13px; font-weight: 700; }.apply-link:hover { background: var(--color-primary-hover); }.empty-state { padding: 56px 20px; border: 1px dashed #cbd5e1; border-radius: var(--radius-inner); color: #64748b; text-align: center; }
@media (max-width: 640px) { .container { padding: 20px 16px 36px; }.page-header { display: block; }.result-count { display: inline-block; margin-top: 12px; }.filters, .job-item { flex-direction: column; }.filters input { width: 100%; }.apply-link { align-self: stretch; text-align: center; }.job-meta span + span { border: 0; padding-left: 0; } }
</style>
