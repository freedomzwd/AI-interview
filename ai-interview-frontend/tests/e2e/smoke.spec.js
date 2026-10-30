import { expect, test } from '@playwright/test'

test('login page renders the user entry form', async ({ page }) => {
  await page.goto('/login')
  await expect(page.getByRole('button', { name: /登录|login/i })).toBeVisible()
  await expect(page.locator('input[type="email"], input[name="email"]').first()).toBeVisible()
})

test('protected dashboard redirects anonymous users to login', async ({ page }) => {
  await page.goto('/dashboard')
  await expect(page).toHaveURL(/\/login/)
})
