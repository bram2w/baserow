import { Page, expect } from '@playwright/test'
import { baserowConfig } from '../playwright.config'

export class BaserowPage {
  readonly page: Page
  readonly baseUrl = baserowConfig.PUBLIC_WEB_FRONTEND_URL
  readonly pageUrl: string

  constructor(page: Page) {
    this.page = page
  }

  async goto() {
    await this.page.goto(this.getFullUrl())
  }

  async checkOnPage() {
    await expect(this.page.url()).toBe(this.getFullUrl())
  }

  getFullUrl() {
    return `${this.baseUrl}/${this.pageUrl}`
  }
}