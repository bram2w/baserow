import { Page } from '@playwright/test'
import { BaserowPage } from "./baserowPage"

export class DashboardPage extends BaserowPage {
  readonly pageUrl = `dashboard`

  constructor(page: Page) {
    super(page)
  }
}