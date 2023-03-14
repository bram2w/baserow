import {expect, test} from '@playwright/test'
import {DashboardPage} from '../../pages/dashboardPage'
import {createUser} from '../../fixtures/user'
import {createLicense, deleteLicense, ENTERPRISE_LICENSE} from "../../fixtures/licence";


test.describe('Enterprise regression tests', () => {

    let license = null

    test.beforeEach(async ({page}) => {
        // Create a new Enterprise license.
        license = await createLicense(ENTERPRISE_LICENSE)
    })

    test('#1606: a non-staff user with an enterprise licence can login and view templates @enterprise', async ({page}) => {
        // Create a new user which we'll navigate with.
        const user = await createUser()

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
    })

    test.afterEach(async () => {
        await deleteLicense(license)
    })
})
