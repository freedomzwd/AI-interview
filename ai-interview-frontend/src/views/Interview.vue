<template>
  <div class="interview-page">
    <!-- 面试准备动画 -->
    <div v-if="preparing" class="prepare-overlay">
      <div class="prepare-card">
        <div class="ai-face-large brand-orb">智</div>
        <h2 style="margin-top:20px;font-size:20px">面试即将开始</h2>
        <p style="color:#6b7280;margin-top:8px;font-size:14px">{{ prepareTip }}</p>
        <div class="prepare-progress">
          <div class="prepare-bar" :style="{ width: preparePercent + '%' }"></div>
        </div>
        <p style="color:#9ca3af;font-size:12px;margin-top:8px">AI 正在为你准备面试题目...</p>
      </div>
    </div>

    <!-- 顶部状态栏 -->
    <div class="interview-header" v-if="!preparing">
      <div style="display:flex;align-items:center;gap:8px">
        <span class="header-mark">智</span>
        <span>AI 面试官</span>
      </div>
      <span class="progress">第 {{ currentIndex + 1 }} / {{ totalQuestions }} 题</span>
      <router-link to="/dashboard" class="btn-secondary" style="padding:4px 12px;font-size:12px;border-radius:6px;display:inline-block">退出</router-link>
    </div>

    <!-- 聊天区域 -->
    <div class="chat-area" ref="chatArea" v-if="!preparing">
      <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
        <!-- AI 头像 -->
        <div v-if="msg.role === 'interviewer'" class="avatar-col">
          <div class="ai-avatar">智</div>
        </div>
        <div class="bubble">
          <div class="bubble-content" v-html="renderContent(msg.content)"></div>
          <div v-if="msg.score" class="bubble-score">评分 {{ msg.score }}/10</div>
        </div>
        <!-- 用户头像 -->
        <div v-if="msg.role === 'candidate'" class="avatar-col">
          <img v-if="userAvatar && !avatarError" :src="userAvatar" class="user-avatar" alt="me" @error="avatarError = true" />
          <div v-else class="user-avatar-placeholder">{{ userInitial }}</div>
        </div>
      </div>

      <!-- 流式输出 -->
      <div v-if="streamingText" class="message interviewer">
        <div class="avatar-col">
          <div class="ai-avatar thinking">智</div>
        </div>
        <div class="bubble">
          <div class="bubble-content streaming-content" v-html="renderContent(streamingText)"></div>
          <span class="cursor-blink">▊</span>
        </div>
      </div>

      <!-- AI 思考中 -->
      <div v-if="thinking && !streamingText" class="message interviewer">
        <div class="avatar-col">
          <div class="ai-avatar thinking">智</div>
        </div>
        <div class="bubble thinking-bubble">
          <span class="dot-animation">AI 思考中<span class="dots"></span></span>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area" v-if="!preparing && !finished">
      <textarea v-model="answer" placeholder="输入你的回答..." @keydown.enter.exact.prevent="handleSubmit" @keydown.shift.enter.exact="null" :disabled="thinking" rows="3"></textarea>
      <button class="btn-primary" @click="handleSubmit" :disabled="!answer.trim() || thinking">
        {{ thinking ? '评估中...' : '发送 (Enter)' }}
      </button>
    </div>

    <!-- 面试结束 -->
    <div class="input-area finished" v-if="!preparing && finished">
      <p>面试已完成</p>
      <router-link :to="`/interview/${interviewId}/report`" class="btn-primary" style="display:inline-block;padding:10px 24px;color:white;border-radius:8px">
        查看评估报告
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { submitAnswerStream, getMessages } from '../api/interview'

const route = useRoute()
const authStore = useAuthStore()
const interviewId = route.params.id

const messages = ref([])
const answer = ref('')
const thinking = ref(false)
const finished = ref(false)
const currentIndex = ref(0)
const totalQuestions = ref(5)
const chatArea = ref(null)
const streamingText = ref('')

// 准备动画
const preparing = ref(true)
const preparePercent = ref(0)
const prepareTips = [
  '请做好准备，保持冷静自信',
  '回答时尽量结合项目经验',
  '注意条理清晰，分点作答',
  '面试官会根据你的简历提问'
]
const prepareTip = ref(prepareTips[0])

// 用户头像
const userAvatar = computed(() => authStore.userAvatar || '')
const avatarError = ref(false)
const userInitial = computed(() => {
  const name = authStore.userName || ''
  return name.charAt(0).toUpperCase() || '我'
})

function renderContent(text) {
  if (!text) return ''
  // 实时过滤AI返回的JSON评分数据，避免流式输出时闪现
  let cleaned = text
    .replace(/```json\s*\{[\s\S]*?\}\s*```/g, '')
    .replace(/\{[^{}]*"score"\s*:\s*[\d.]+[^{}]*\}/g, '')
    .trim()
  return cleaned.replace(/\n/g, '<br>')
}

function scrollToBottom() {
  nextTick(() => {
    if (chatArea.value) chatArea.value.scrollTop = chatArea.value.scrollHeight
  })
}

onMounted(async () => {
  // 准备动画
  let tipIdx = 0
  const tipTimer = setInterval(() => {
    tipIdx = (tipIdx + 1) % prepareTips.length
    prepareTip.value = prepareTips[tipIdx]
  }, 1500)

  const barTimer = setInterval(() => {
    if (preparePercent.value < 90) preparePercent.value += 2
  }, 100)

  try {
    const data = await getMessages(interviewId)
    const msgList = Array.isArray(data) ? data : (data.items || data)
    messages.value = msgList.map(m => ({
      role: m.role, content: m.content, score: m.score, feedback: m.feedback
    }))
    const indices = msgList.map(m => m.question_index).filter(i => i != null)
    if (indices.length) currentIndex.value = Math.max(...indices)
  } catch (e) {
    console.error('加载消息失败:', e)
  }

  // 完成准备动画
  preparePercent.value = 100
  clearInterval(barTimer)
  clearInterval(tipTimer)
  setTimeout(() => { preparing.value = false }, 600)
  nextTick(scrollToBottom)
})

async function handleSubmit() {
  if (!answer.value.trim() || thinking.value) return
  const myAnswer = answer.value.trim()
  answer.value = ''
  messages.value.push({ role: 'candidate', content: myAnswer })
  scrollToBottom()
  thinking.value = true
  streamingText.value = ''
  let rawStreamText = ''  // 保存原始完整文本用于最终提取

  try {
    await submitAnswerStream(interviewId, myAnswer,
      (chunk) => {
        rawStreamText += chunk
        // 实时过滤：去掉已完成的JSON块和正在构建中的JSON片段（以```json或裸{开头的尾部）
        let display = rawStreamText
          .replace(/```json\s*\{[\s\S]*?\}\s*```/g, '')
          .replace(/\{[^{}]*"score"\s*:\s*[\d.]+[^{}]*\}/g, '')
        // 过滤尾部不完整的JSON片段（```json...未闭合 或 {"sco...未闭合）
        display = display.replace(/```json[\s\S]*$/g, '')
        display = display.replace(/\{[^}]*$/g, function(match) {
          // 只过滤看起来像JSON评分的不完整片段
          return /["']?score/.test(match) || /^\{\s*$/.test(match) ? '' : match
        })
        streamingText.value = display.trim()
        scrollToBottom()
      },
      (data) => {
        if (rawStreamText.trim()) {
          let displayText = rawStreamText
            .replace(/```json\s*\{[\s\S]*?\}\s*```/g, '')
            .replace(/\{[^{}]*"score"\s*:\s*[\d.]+[^{}]*\}/g, '')
            .trim()
          if (displayText) {
            messages.value.push({ role: 'interviewer', content: displayText, score: data.score })
          }
        }
        streamingText.value = ''
        rawStreamText = ''
        const lastCandidate = [...messages.value].reverse().find(m => m.role === 'candidate')
        if (lastCandidate) lastCandidate.score = data.score

        if (data.is_finished) {
          finished.value = true
        } else if (data.next_question) {
          currentIndex.value = data.question_index + 1
          messages.value.push({ role: 'interviewer', content: data.next_question })
        }
        scrollToBottom()
      }
    )
  } catch (e) {
    streamingText.value = ''
    messages.value.push({ role: 'interviewer', content: '出错了：' + e.message })
    scrollToBottom()
  } finally {
    thinking.value = false
  }
}
</script>

<style scoped>
.interview-page { display: flex; flex-direction: column; height: 100vh; max-width: 860px; margin: 0 auto; background: rgba(255,255,255,0.28); }

/* 准备动画 */
.prepare-overlay {
  position: fixed; inset: 0; background: var(--color-background);
  display: flex; align-items: center; justify-content: center; z-index: 200;
}
.prepare-card { text-align: center; padding: 40px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-card); box-shadow: var(--shadow-card); }
.ai-face-large { animation: faceFloat 2s ease-in-out infinite; }
.brand-orb {
  width: 80px; height: 80px; margin: 0 auto;
  border-radius: 24px; display: flex; align-items: center; justify-content: center;
  background: var(--color-primary-soft); border: 1px solid var(--color-border-strong);
  color: var(--color-primary); font-size: 32px; font-weight: 800;
}
@keyframes faceFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
.prepare-progress {
  width: 280px; height: 6px; background: #e5e7eb; border-radius: 3px;
  margin: 16px auto 0; overflow: hidden;
}
.prepare-bar {
  height: 100%; background: var(--color-primary);
  border-radius: 3px; transition: width 0.3s ease;
}

/* 顶部 */
.interview-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 20px; background: var(--color-surface); border-bottom: 1px solid var(--color-border);
  font-size: 14px; font-weight: 600;
}
.header-mark {
  width: 24px; height: 24px; display: inline-flex; align-items: center; justify-content: center;
  border-radius: 7px; background: var(--color-primary-soft); color: var(--color-primary);
  border: 1px solid rgba(5, 150, 105, 0.18); font-size: 13px; font-weight: 800;
}
.progress { color: var(--color-muted); font-weight: 400; }

/* 聊天 */
.chat-area { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.message { display: flex; align-items: flex-start; gap: 10px; }
.message.interviewer { justify-content: flex-start; }
.message.candidate { justify-content: flex-end; }

/* 头像 */
.avatar-col { flex-shrink: 0; margin-top: 2px; }
.ai-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: var(--color-primary-soft); border: 1px solid rgba(5, 150, 105, 0.18);
  color: var(--color-primary); font-size: 14px; font-weight: 800;
  box-shadow: var(--shadow-soft);
}
.ai-avatar.thinking { animation: avatarPulse 1.5s ease-in-out infinite; }
@keyframes avatarPulse {
  0%, 100% { box-shadow: 0 0 0 rgba(5,150,105,0); }
  50% { box-shadow: 0 0 0 4px rgba(5,150,105,0.10); }
}
.user-avatar { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; }
.user-avatar-placeholder {
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--color-primary-soft);
  border: 1px solid rgba(5, 150, 105, 0.18);
  color: var(--color-primary);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 600;
}

/* 气泡 */
.bubble { max-width: 70%; padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.6; box-shadow: var(--shadow-soft); }
.interviewer .bubble { background: var(--color-surface-solid); border: 1px solid var(--color-border); border-bottom-left-radius: 4px; }
.candidate .bubble { background: var(--color-primary); color: white; border-bottom-right-radius: 4px; }
.thinking-bubble { color: var(--color-muted); font-style: italic; }
.dot-animation .dots::after { content: ''; animation: dots 1.5s steps(4, end) infinite; }
@keyframes dots {
  0% { content: ''; } 25% { content: '.'; } 50% { content: '..'; } 75% { content: '...'; } 100% { content: ''; }
}
.streaming-content { display: inline; }
.cursor-blink { display: inline; animation: blink 0.8s step-end infinite; color: var(--color-primary); font-size: 14px; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.bubble-score { margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2); font-size: 13px; }
.interviewer .bubble-score { border-top-color: var(--color-border); color: var(--color-primary); }

/* 输入 */
.input-area { padding: 16px 20px; background: var(--color-surface); border-top: 1px solid var(--color-border); display: flex; gap: 12px; align-items: flex-end; }
.input-area textarea { flex: 1; resize: none; font-family: inherit; }
.input-area.finished { justify-content: center; align-items: center; padding: 24px; gap: 16px; }
.input-area.finished p { font-size: 18px; font-weight: 600; }
</style>
