import { Page } from '@playwright/test'
import { BaserowPage } from "./baserowPage"
import { Sidebar } from "../components/sidebar";

export class DashboardPage extends BaserowPage {
  readonly pageUrl = `dashboard`
  readonly sidebar: Sidebar

  constructor(page: Page) {
    super(page)
    this.sidebar = new Sidebar(page)
  }


}