import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './style.css'

// Ctrl + 滚轮缩放字体：滚轮向上放大、向下缩小，缩放范围 50% ~ 200%
const MIN_ZOOM = 0.5
const MAX_ZOOM = 2

window.addEventListener('wheel', (event) => {
  if (!event.ctrlKey) return
  event.preventDefault()
  const current = parseFloat(document.documentElement.style.zoom) || 1
  const next = current + (event.deltaY < 0 ? 0.1 : -0.1)
  document.documentElement.style.zoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, next))
}, { passive: false })

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
