<template>
  <div>
    <div class="page-header">
      <div><h1>外部数据源</h1><p>只同步公开 API 或已授权企业职位 Board，不使用招聘网站抓取。</p></div>
      <button class="btn-secondary" @click="loadRuns">刷新记录</button>
    </div>
    <div class="source-grid">
      <section class="card source-card">
        <div><span class="source-type">职位来源</span><h2>Remotive 公开职位</h2><p>同步软件开发类远程职位，并保留原始投递链接和来源信息。</p></div>
        <button class="btn-primary" :disabled="syncing === 'jobs'" @click="syncJobs">{{ syncing === 'jobs' ? '同步中...' : '同步职位' }}</button>
      </section>
      <section class="card source-card">
        <div><span class="source-type">算法题来源</span><h2>Codeforces 官方 API</h2><p>按标签增量导入题目、难度和原题链接，不伪造参考答案。</p></div>
        <div class="codeforces-actions"><input v-model="tag" aria-label="Codeforces 标签" placeholder="标签，如 dp" /><button class="btn-primary" :disabled="syncing === 'codeforces'" @click="syncCodeforces">{{ syncing === 'codeforces' ? '同步中...' : '同步算法题' }}</button></div>
      </section>
    </div>
    <section class="card runs-card"><div class="runs-heading"><h2>同步记录</h2><span>{{ runs.length }} 条</span></div>
      <div class="runs-scroll"><table><thead><tr><th>来源</th><th>数据类型</th><th>状态</th><th>接收</th><th>新增</th><th>更新</th><th>开始时间</th><th>失败原因</th></tr></thead><tbody>
        <tr v-for="run in runs" :key="run.id"><td>{{ run.provider }}</td><td>{{ resourceLabel(run.resource) }}</td><td><span :class="['badge', run.status === 'completed' ? 'badge-green' : 'badge-red']">{{ run.status === 'completed' ? '完成' : '失败' }}</span></td><td>{{ run.received_count }}</td><td>{{ run.created_count }}</td><td>{{ run.updated_count }}</td><td>{{ formatDate(run.started_at) }}</td><td class="error">{{ run.error_message || '-' }}</td></tr>
        <tr v-if="!runs.length"><td colspan="8" class="empty">暂无同步记录</td></tr>
      </tbody></table></div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { externalDataApi } from '../api'
const runs = ref([]); const tag = ref('dp'); const syncing = ref('')
function resourceLabel(value) { return { jobs: '职位', problems: '算法题' }[value] || value }
function formatDate(value) { return value ? new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : '-' }
async function loadRuns() { try { runs.value = (await externalDataApi.runs({ limit: 30 })).items || [] } catch (e) { alert(e.message) } }
async function syncJobs() { syncing.value = 'jobs'; try { await externalDataApi.syncJobs(); await loadRuns(); alert('职位同步任务已提交，可稍后刷新同步记录') } catch (e) { alert(e.message) } finally { syncing.value = '' } }
async function syncCodeforces() { if (!tag.value.trim()) return; syncing.value = 'codeforces'; try { await externalDataApi.syncCodeforces(tag.value.trim(), 30); await loadRuns(); alert('算法题同步任务已提交，可稍后刷新同步记录') } catch (e) { alert(e.message) } finally { syncing.value = '' } }
onMounted(loadRuns)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; margin-bottom: 20px; }.page-header h1 { font-size: 20px; margin-bottom: 7px; }.page-header p { color: var(--color-muted); font-size: 14px; }.source-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-bottom: 16px; }.source-card { min-height: 198px; display: flex; flex-direction: column; justify-content: space-between; align-items: flex-start; }.source-type { color: var(--color-primary); font-size: 12px; font-weight: 700; }.source-card h2 { font-size: 17px; margin: 8px 0; }.source-card p { color: var(--color-muted); font-size: 14px; line-height: 1.6; }.codeforces-actions { display: flex; width: 100%; gap: 8px; }.codeforces-actions input { min-width: 0; flex: 1; }.runs-card { padding: 0; overflow: hidden; }.runs-heading { display: flex; justify-content: space-between; align-items: center; padding: 18px 20px; }.runs-heading h2 { font-size: 16px; }.runs-heading span { color: var(--color-muted); font-size: 13px; }.runs-scroll { overflow-x: auto; }.runs-scroll table { min-width: 860px; }.error { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.empty { padding: 28px; color: var(--color-muted); text-align: center; } @media (max-width: 860px) { .source-grid { grid-template-columns: 1fr; } }
</style>
