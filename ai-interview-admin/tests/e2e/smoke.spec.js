import { expect, test } from '@playwright/test'

test('admin login page renders', async ({ page }) => {
  await page.goto('/login')
  await expect(page.getByRole('button', { name: /登录|login/i })).toBeVisible()
  await expect(page.locator('input[type="email"], input[name="email"]').first()).toBeVisible()
})

test('admin root redirects anonymous users to login', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveURL(/\/login/)
})

test('dashboard completion metric navigates to completed interviews', async ({ page }) => {
  await page.route('**/api/v1/backoffice/**', async route => {
    const path = new URL(route.request().url()).pathname
    const data = path.endsWith('/users/stats')
      ? { user_count: 1, resume_count: 1, interview_count: 1, completed_interview_count: 1 }
      : { items: [], total: 0 }
    await route.fulfill({ json: { code: 200, data } })
  })

  await page.addInitScript(() => {
    localStorage.setItem('admin_token', 'test-token')
    localStorage.setItem('admin_email', 'admin@example.com')
  })

  await page.goto('/')
  await page.getByRole('link', { name: '查看已完成面试' }).click()
  await expect(page).toHaveURL(/\/interviews\?status=completed/)
  await expect(page.getByRole('heading', { name: '面试记录' })).toBeVisible()
})
