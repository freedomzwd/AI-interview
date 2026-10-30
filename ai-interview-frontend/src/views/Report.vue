<template>
  <div class="container">
    <div v-if="loading" class="loading">加载报告中...</div>

    <div v-else-if="report" class="report-page">
      <!-- 总分 -->
      <div class="card score-card">
        <div
          class="score-circle"
          :style="{ '--score-percent': scorePercent(data.overall_score), '--score-color': reportScoreColor(data.overall_score) }"
        >
          <span class="score-num">{{ data.overall_score }}</span>
          <span class="score-label">/10</span>
        </div>
        <div class="score-info">
          <h2>面试评估报告</h2>
          <p class="hire-rec" v-if="report.hire_recommendation">
            {{ report.hire_recommendation }}
          </p>
        </div>
      </div>

      <!-- 总结 -->
      <div class="card" style="margin-top:16px" v-if="report.summary">
        <h3 style="margin-bottom:10px">总体评价</h3>
        <p style="font-size:14px;line-height:1.8;color:#374151">{{ report.summary }}</p>
      </div>

      <!-- 优势 & 不足 -->
      <div class="two-col" style="margin-top:16px">
        <div class="card" v-if="report.strengths?.length">
          <h3 style="margin-bottom:10px;color:var(--color-success)">优势</h3>
          <ul>
            <li v-for="(s, i) in report.strengths" :key="i">{{ s }}</li>
          </ul>
        </div>
        <div class="card" v-if="report.weaknesses?.length">
          <h3 style="margin-bottom:10px;color:var(--color-danger)">不足</h3>
          <ul>
            <li v-for="(w, i) in report.weaknesses" :key="i">{{ w }}</li>
          </ul>
        </div>
      </div>

      <!-- 建议 -->
      <div class="card" style="margin-top:16px" v-if="report.suggestions?.length">
        <h3 style="margin-bottom:10px">改进建议</h3>
        <ul>
          <li v-for="(s, i) in report.suggestions" :key="i">{{ s }}</li>
        </ul>
      </div>

      <!-- 各题得分 -->
      <div class="card" style="margin-top:16px" v-if="report.question_scores?.length">
        <h3 style="margin-bottom:12px">各题得分</h3>
        <div v-for="(q, i) in report.question_scores" :key="i" class="q-score-item">
          <div class="q-score-header">
            <span class="q-index">Q{{ i + 1 }}</span>
            <span class="q-text">{{ q.question }}</span>
            <span class="q-score" :style="{ color: q.score >= 7 ? '#047857' : q.score >= 5 ? '#b45309' : '#b91c1c' }">
              {{ q.score }}
            </span>
          </div>
          <div class="q-bar">
            <div class="q-bar-fill" :style="{ width: (q.score * 10) + '%', background: q.score >= 7 ? '#059669' : q.score >= 5 ? '#b45309' : '#b91c1c' }"></div>
          </div>
        </div>
      </div>

      <!-- 对话复盘 -->
      <div class="card dialogue-card" v-if="dialogueItems.length">
        <div class="section-heading">
          <div>
            <h3>对话记录</h3>
            <p>已按得分、回答完整度和技术关键词标出复盘优先级</p>
          </div>
          <div class="legend">
            <span><i class="legend-dot priority-high"></i>优先处理</span>
            <span><i class="legend-dot priority-medium"></i>需要加强</span>
            <span><i class="legend-dot priority-low"></i>表现稳定</span>
          </div>
        </div>

        <div
          v-for="item in dialogueItems"
          :key="item.key"
          :class="['dialogue-item', priorityClass(item.priority)]"
        >
          <div class="dialogue-topline">
            <span class="q-index">Q{{ item.index + 1 }}</span>
            <span :class="['priority-pill', priorityClass(item.priority)]">{{ priorityLabel(item.priority) }}</span>
            <span v-if="item.score" :class="['score-chip', scoreTone(item.score)]">评分 {{ item.score }}/10</span>
            <div class="focus-tags" v-if="item.tags.length">
              <span v-for="tag in item.tags" :key="tag">{{ tag }}</span>
            </div>
          </div>

          <div class="speaker-block interviewer-block" v-if="item.question">
            <div class="speaker-label">面试官</div>
            <p>{{ item.question }}</p>
          </div>

          <div class="speaker-block candidate-block" v-if="item.answer">
            <div class="speaker-label">候选人</div>
            <p>{{ item.answer }}</p>
          </div>

          <div class="feedback-block" v-if="item.feedback">
            <div class="speaker-label">重点点评</div>
            <p>{{ item.feedback }}</p>
          </div>
        </div>
      </div>

      <!-- 操作 -->
      <div style="text-align:center;margin-top:24px;margin-bottom:40px">
        <router-link to="/resume/upload" class="btn-primary" style="display:inline-block;padding:10px 24px;color:white;border-radius:8px;margin-right:12px">
          再来一次
        </router-link>
        <router-link to="/dashboard" class="btn-secondary" style="display:inline-block;padding:10px 24px;border-radius:8px">
          返回首页
        </router-link>
      </div>
    </div>

    <div v-else class="card" style="text-align:center;padding:60px;max-width:500px;margin:60px auto">
      <p>报告加载失败</p>
      <router-link to="/dashboard" style="margin-top:12px;display:inline-block">返回首页</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getMessages, getReport } from '../api/interview'

const route = useRoute()
const interviewId = route.params.id
const data = ref(null)
const report = ref(null)
const messages = ref([])
const loading = ref(true)

const dialogueItems = computed(() => {
  const byQuestion = new Map()

  messages.value.forEach((m, fallbackIndex) => {
    const index = Number.isInteger(m.question_index) ? m.question_index : fallbackIndex
    if (!byQuestion.has(index)) {
      byQuestion.set(index, { index, question: '', answer: '', score: null, feedback: '', tags: [] })
    }
    const item = byQuestion.get(index)
    if (m.role === 'interviewer' && !item.question) item.question = m.content || ''
    if (m.role === 'candidate') {
      item.answer = m.content || ''
      item.score = m.score
      item.feedback = m.feedback || ''
    }
  })

  return Array.from(byQuestion.values())
    .filter(item => item.question || item.answer || item.feedback)
    .map((item, fallbackIndex) => {
      const score = Number(item.score)
      const priority = getPriority(score, item.answer, item.feedback)
      return {
        ...item,
        key: `${item.index}-${fallbackIndex}`,
        priority,
        tags: extractFocusTags(item.question, item.answer, item.feedback, score)
      }
    })
    .sort((a, b) => a.index - b.index)
})

function getPriority(score, answer = '', feedback = '') {
  const text = `${answer} ${feedback}`
  if (Number.isFinite(score) && score <= 3) return 'high'
  if (/未提供|没有提供|完全未回应|仅以|无法展示|严重|缺乏|未回答/.test(text)) return 'high'
  if (Number.isFinite(score) && score <= 6) return 'medium'
  if (/建议|补充|加强|不足|不够|欠缺|需要/.test(text)) return 'medium'
  return 'low'
}

function extractFocusTags(question = '', answer = '', feedback = '', score = null) {
  const text = `${question} ${answer} ${feedback}`
  const tags = []

  if (Number.isFinite(score) && score <= 3) tags.push('优先复盘')
  if (/未提供|没有提供|仅以|未回答|不知道|不会|开始/.test(text)) tags.push('回答完整度')
  if (/架构|流程|设计|模块|链路|工作流|编排/.test(text)) tags.push('架构说明')
  if (/数据|指标|准确率|评估|量化|样本|标注/.test(text)) tags.push('数据与指标')
  if (/项目|经验|场景|落地|业务|实现/.test(text)) tags.push('项目细节')
  if (/RAG|Agent|LoRA|LangChain|LangGraph|FAISS|Qwen|模型|微调/i.test(text)) tags.push('技术深度')
  if (/建议|补充|加强|改进|不足|缺乏/.test(text)) tags.push('改进建议')

  return [...new Set(tags)].slice(0, 5)
}

function priorityClass(priority) {
  return `priority-${priority}`
}

function priorityLabel(priority) {
  return { high: '高优先级', medium: '中优先级', low: '低优先级' }[priority] || '待复盘'
}

function scoreTone(score) {
  if (score >= 7) return 'score-good'
  if (score >= 5) return 'score-mid'
  return 'score-low'
}

function scorePercent(score) {
  const value = Number(score) || 0
  return `${Math.max(0, Math.min(100, value * 10))}%`
}

function reportScoreColor(score) {
  if (score >= 7) return '#059669'
  if (score >= 5) return '#b45309'
  return '#b91c1c'
}

onMounted(async () => {
  try {
    const [res, msgRes] = await Promise.all([
      getReport(interviewId),
      getMessages(interviewId).catch(() => [])
    ])
    data.value = res
    report.value = res.report || {}
    messages.value = Array.isArray(msgRes) ? msgRes : (msgRes.items || [])
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.loading {
  text-align: center;
  padding: 80px;
  color: var(--color-muted);
}
.report-page {
  max-width: 1120px;
  margin: 30px auto;
}
.score-card {
  display: flex;
  align-items: center;
  gap: 24px;
}
.score-circle {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  background: conic-gradient(var(--score-color) 0 var(--score-percent), #e2e8f0 var(--score-percent) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
}
.score-circle::after {
  content: '';
  position: absolute;
  inset: 7px;
  border-radius: 50%;
  background: white;
}
.score-num {
  font-size: 32px;
  font-weight: 700;
  color: var(--color-foreground);
  position: relative;
  z-index: 1;
}
.score-label {
  font-size: 14px;
  color: var(--color-muted);
  position: relative;
  z-index: 1;
}
.score-info h2 {
  font-size: 20px;
  margin-bottom: 4px;
}
.hire-rec {
  font-size: 14px;
  color: var(--color-muted);
  margin-top: 4px;
}
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
ul {
  list-style: none;
  padding: 0;
}
ul li {
  font-size: 14px;
  line-height: 1.8;
  padding-left: 16px;
  position: relative;
}
ul li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #6b7280;
}
.q-score-item {
  margin-bottom: 14px;
}
.q-score-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
  font-size: 14px;
}
.q-index {
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
  color: #6b7280;
}
.q-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.q-score {
  font-weight: 700;
  font-size: 16px;
}
.q-bar {
  height: 6px;
  background: #f3f4f6;
  border-radius: 3px;
  overflow: hidden;
}
.q-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}
.dialogue-card {
  margin-top: 16px;
}
.section-heading {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 18px;
}
.section-heading h3 {
  margin-bottom: 6px;
}
.section-heading p {
  color: var(--color-muted);
  font-size: 13px;
}
.legend {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  color: var(--color-muted);
  font-size: 12px;
}
.legend span,
.legend-dot {
  display: inline-flex;
  align-items: center;
}
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  margin-right: 5px;
}
.dialogue-item {
  border: 1px solid var(--color-border);
  border-left-width: 4px;
  border-radius: var(--radius-inner);
  padding: 14px;
  margin-bottom: 14px;
  background: rgba(255, 255, 255, 0.72);
}
.dialogue-item.priority-high { border-left-color: var(--color-danger); }
.dialogue-item.priority-medium { border-left-color: var(--color-warning); }
.dialogue-item.priority-low { border-left-color: var(--color-primary); }
.dialogue-topline {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.priority-pill,
.score-chip,
.focus-tags span {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}
.priority-pill {
  padding: 4px 9px;
}
.priority-pill.priority-high {
  color: var(--color-danger);
  background: var(--color-danger-soft);
  border: 1px solid rgba(185, 28, 28, 0.16);
}
.priority-pill.priority-medium {
  color: var(--color-warning);
  background: var(--color-warning-soft);
  border: 1px solid rgba(180, 83, 9, 0.18);
}
.priority-pill.priority-low {
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border: 1px solid rgba(5, 150, 105, 0.18);
}
.score-chip {
  padding: 4px 9px;
  background: #f8fafc;
  border: 1px solid var(--color-border);
}
.score-good { color: var(--color-success); }
.score-mid { color: var(--color-warning); }
.score-low { color: var(--color-danger); }
.focus-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.focus-tags span {
  padding: 4px 8px;
  color: #334155;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
}
.speaker-block,
.feedback-block {
  border-radius: 10px;
  padding: 12px 14px;
  margin-top: 10px;
}
.interviewer-block {
  background: #f8fafc;
}
.candidate-block {
  background: var(--color-primary-soft);
}
.feedback-block {
  background: #fff7ed;
  border: 1px solid rgba(180, 83, 9, 0.18);
}
.speaker-label {
  color: var(--color-muted);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 6px;
}
.speaker-block p,
.feedback-block p {
  color: var(--color-foreground);
  font-size: 14px;
  line-height: 1.8;
  margin: 0;
}

@media (max-width: 760px) {
  .report-page {
    max-width: calc(100vw - 32px);
    margin: 20px auto;
  }
  .score-card,
  .section-heading {
    flex-direction: column;
  }
  .two-col {
    grid-template-columns: 1fr;
  }
}
</style>
