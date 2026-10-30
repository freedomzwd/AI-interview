<template>
  <div>
    <div class="page-header">
      <h1>文档检索测试</h1>
      <router-link to="/knowledge"><button class="btn-secondary">← 返回文档列表</button></router-link>
    </div>

    <div class="card">
      <div class="hint">
        测试输入查询文本，看从知识文档库里能召回什么 chunks。这个检索用于答案评分增强、用户答疑场景。
      </div>

      <div class="form-grid">
        <div class="form-item span-2">
          <label>查询文本 *</label>
          <input v-model="query" placeholder="例：Python GIL 影响" @keyup.enter="search" />
        </div>
        <div class="form-item">
          <label>返回数量 K</label>
          <input type="number" v-model.number="k" min="1" max="20" />
        </div>
        <div class="form-item">
          <label>语义最低相似度</label>
          <input type="number" v-model.number="minScore" min="0" max="1" step="0.05" />
        </div>
        <div class="form-item">
          <label>分类筛选（可选）</label>
          <input v-model="category" placeholder="python" />
        </div>
      </div>

      <div class="actions">
        <button class="btn-primary" @click="search" :disabled="loading">{{ loading ? '检索中...' : '开始检索' }}</button>
      </div>
    </div>

    <div v-if="result" class="card result-card">
      <div class="result-header">
        <span>查询：<b>{{ result.query }}</b></span>
        <span class="badge badge-blue">召回 {{ result.count }} 个 chunk</span>
      </div>

      <div v-if="!result.items.length" class="empty">没有匹配的内容，建议降低 min_score 或先上传更多文档</div>

      <div v-for="(item, idx) in result.items" :key="item.id" class="result-item">
        <div class="ri-header">
          <span class="ri-rank">#{{ idx + 1 }}</span>
          <span class="ri-id">Chunk ID: {{ item.id }}</span>
          <span class="ri-doc">来自文档: {{ item.document_id }}</span>
          <span :class="['retrieval-badge', retrievalClass(item)]">{{ retrievalLabel(item) }}</span>
        </div>
        <div class="ri-content">{{ item.content }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { knowledgeApi } from '../api'

const query = ref('Python 协程 异步原理')
const k = ref(4)
const minScore = ref(0.3)
const category = ref('')
const loading = ref(false)
const result = ref(null)

function retrievalLabel(item) {
  const score = Number.isFinite(item.similarity) ? `${(item.similarity * 100).toFixed(1)}%` : '--'
  if (item.retrieval_mode === 'semantic') return `语义相似度 ${score}`
  if (item.retrieval_mode === 'hybrid') return `混合相关度 ${score}`
  if (item.retrieval_mode === 'advanced') return `增强相关度 ${score}`
  return `关键词相关度 ${score}`
}

function retrievalClass(item) {
  return item.retrieval_mode === 'semantic' ? 'is-semantic' : 'is-keyword'
}

async function search() {
  if (!query.value.trim()) { alert('请输入查询文本'); return }
  loading.value = true
  try {
    const payload = { query: query.value.trim(), k: k.value, min_score: minScore.value }
    if (category.value.trim()) payload.category = category.value.trim()
    result.value = await knowledgeApi.testRetrieve(payload)
  } catch (e) { alert(e.message) }
  finally { loading.value = false }
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h1 { font-size: 20px; }
.btn-secondary { background: #e5e7eb; color: #374151; padding: 8px 14px; }

.hint { background: var(--color-primary-soft); color: var(--color-primary); padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; font-size: 13px; border: 1px solid rgba(5, 150, 105, 0.14); }
.form-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 16px; }
.form-item.span-2 { grid-column: span 2; }
.form-item label { display: block; font-size: 13px; color: #374151; margin-bottom: 6px; font-weight: 500; }
.form-item input { width: 100%; }
.actions { display: flex; gap: 8px; }

.result-card { margin-top: 20px; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid #f3f4f6; }
.empty { text-align: center; color: #9ca3af; padding: 30px 0; }

.result-item { padding: 14px 0; border-bottom: 1px solid #f3f4f6; }
.result-item:last-child { border-bottom: none; }
.ri-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; flex-wrap: wrap; font-size: 13px; color: #6b7280; }
.ri-rank { font-weight: 700; color: var(--color-primary); }
.retrieval-badge { margin-left: auto; padding: 5px 8px; border: 1px solid transparent; border-radius: 4px; font-weight: 600; white-space: nowrap; }
.retrieval-badge.is-semantic { color: #047857; background: #ecfdf5; border-color: #a7f3d0; }
.retrieval-badge.is-keyword { color: #9a5d00; background: #fffbeb; border-color: #fde68a; }
.ri-content { padding: 12px 14px; background: #f9fafb; border-radius: 6px; font-size: 13px; color: #374151; line-height: 1.7; white-space: pre-wrap; }
@media (max-width: 720px) { .form-grid { grid-template-columns: 1fr; } .form-item.span-2 { grid-column: span 1; } .retrieval-badge { margin-left: 0; } }
</style>
