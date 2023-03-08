import { Locator, Page } from '@playwright/test'
import { BaserowPage } from './baserowPage'

export class LoginPage extends BaserowPage {
  readonly pageUrl = `login`
  readonly emailInput: Locator
  readonly passwordInput: Locator
  readonly loginButton: Locator

  constructor(page: Page) {
    super(page)
    this.emailInput = page.locator('input[type="email"]').first()
    this.passwordInput = page.locator('input[type="password"]').first()
    this.loginButton = page.locator('button:text("Sign in")').first()
  }

  async loginWithPassword(email: string, password: string) {
    await this.emailInput.fill(email)
    await this.passwordInput.fill(password)
    const navigationPromise = this.page.waitForNavigation({timeout:5000})
    await this.loginButton.click()
    await this.page.screenshot()
    await navigationPromise
  }
}