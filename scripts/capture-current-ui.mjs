import { chromium } from '../ai-interview-admin/node_modules/playwright/index.mjs'
import { mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const output = path.join(root, 'project-screenshots', 'current')
await mkdir(output, { recursive: true })

const browser = await chromium.launch({ headless: true })
const context = await browser.newContext({
  viewport: { width: 1440, height: 960 },
  deviceScaleFactor: 1,
  colorScheme: 'light',
})
const page = await context.newPage()
page.setDefaultTimeout(20_000)

async function capture(url, filename) {
  await page.goto(url, { waitUntil: 'networkidle' })
  await page.screenshot({ path: path.join(output, filename), fullPage: true })
}

await capture('http://localhost:3000/login', '01-user-login.png')
await capture('http://localhost:3001/login', '02-admin-login.png')

await page.locator('input[type="email"]').fill('admin@ai-interview.com')
await page.locator('input[type="password"]').fill('ai-interview&admin')
await page.getByRole('button', { name: '登录' }).click()
await page.waitForURL(url => url.origin === 'http://localhost:3001' && url.pathname === '/')
await page.waitForLoadState('networkidle')
await page.screenshot({ path: path.join(output, '03-admin-dashboard.png'), fullPage: true })

await capture('http://localhost:3001/question-bank', '04-question-bank.png')
await capture('http://localhost:3001/knowledge', '05-knowledge-base.png')
await page.goto('http://localhost:3001/question-bank/test', { waitUntil: 'networkidle' })
await page.locator('input[placeholder^="例："]').fill('AI Agent 工具调用 RAG 记忆 安全评估')
await page.locator('input[type="number"]').nth(1).fill('0.3')
await page.getByRole('button', { name: '开始检索' }).click()
await page.locator('.result-card').waitFor()
await page.screenshot({ path: path.join(output, '06-rag-retrieval-test.png'), fullPage: true })

await browser.close()
console.log(`Captured current UI to ${output}`)
