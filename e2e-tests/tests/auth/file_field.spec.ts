import {expect, test} from '@playwright/test'
import { LoginPage } from '../../pages/loginPage'
import { TablePage } from '../../pages/tablePage'
import { DashboardPage } from '../../pages/dashboardPage'
import { createUser, deleteUser } from '../../fixtures/user'
import {Sidebar} from "../../components/sidebar";

let user = null

test.beforeEach(async () => {
  user = await createUser()
})

test.afterEach(async () => {
  // We only want to bother cleaning up in a devs local env or when pointed at a real
  // server. If in CI then the first user will be the first admin and this will fail.
  // Secondly in CI we are going to delete the database anyway so no need to clean-up.
  if(!process.env.CI){
    await deleteUser(user)
  }
})

test('User can upload an image and download it again @upload', async ({ page }) => {
  const loginPage = new LoginPage(page)
  await loginPage.goto()
  await loginPage.loginWithPassword(user.email, user.password)
  // Pass our user's token to the dashboard page's middleware, visit it.
  const dashboardPage = new DashboardPage(page)
  await dashboardPage.authWithMiddleware(user)
  await dashboardPage.goto()
  await dashboardPage.checkOnPage()

  // Click "Create new" > "From template".
  const templateModal = await dashboardPage.sidebar.openCreateAppFromTemplateModal()
  await templateModal.waitUntilLoaded()

  const templatesLoadingSpinner = templateModal.loadingSpinner()
  await expect(templatesLoadingSpinner, 'Checking that the templates modal spinner is hidden.').toBeHidden()

  await templateModal.clickUseThisTemplateButton();

  const sideBar = new Sidebar(page)
  await sideBar.selectDatabaseAndTableByName('Project Tracker', 'Projects')

  const tablePage = new TablePage(page)
  await tablePage.addNewFieldOfType('File');
  const imageWidth = await tablePage.uploadImageToFirstFileFieldCellAndGetWidth()

  expect(imageWidth).toBeGreaterThan(0);
})