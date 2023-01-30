import { test } from '@playwright/test'
import { LoginPage } from '../../pages/loginPage'
import { DashboardPage } from '../../pages/dashboardPage'
import { createUser, deleteUser } from '../../fixtures/user'

let user = null

test.beforeEach(async () => {
  user = await createUser()
})

test.afterEach(async () => {
  await deleteUser(user)
})

test('User can log in with email/password', async ({ page }) => {
  const loginPage = new LoginPage(page)
  await loginPage.goto()
  await loginPage.loginWithPassword(user.email, user.password)
  const dashboardPage = new DashboardPage(page)
  await dashboardPage.checkOnPage()
})