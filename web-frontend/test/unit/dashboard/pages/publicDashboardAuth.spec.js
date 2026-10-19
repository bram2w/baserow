import { flushPromises } from '@vue/test-utils'
import { vi } from 'vitest'

import { TestApp } from '@baserow/test/helpers/testApp'
import { getToken, unsetToken } from '@baserow/modules/core/utils/auth'
import PublicDashboardAuth from '@baserow/modules/dashboard/pages/publicDashboardAuth'

const SLUG = 'protected-slug'

describe('PublicDashboardAuth page', () => {
  let testApp = null
  let nuxtApp = null
  let store = null

  beforeEach(() => {
    testApp = new TestApp()
    nuxtApp = testApp.getApp()
    store = testApp.getStore()
  })

  afterEach(async () => {
    await unsetToken(nuxtApp, SLUG)
    await testApp.afterEach()
  })

  async function mountPage(query = '') {
    const page = await testApp.mount(PublicDashboardAuth, {
      route: `/public/dashboard/${SLUG}/auth${query}`,
    })
    // The page navigates through the router of the app, nothing has to be
    // rendered for that.
    const push = vi.spyOn(nuxtApp.$router, 'push').mockResolvedValue()
    return { page, push }
  }

  async function submitPassword(page, password) {
    await page.find('input[type="password"]').setValue(password)
    await page.find('form').trigger('submit')
    await flushPromises()
  }

  test('stores the token for the right password and sends the visitor back', async () => {
    testApp.mock
      .onPost(`/dashboard/public/${SLUG}/auth/`, {
        password: 'secret-password',
      })
      .reply(200, { access_token: 'access-token' })

    const { page, push } = await mountPage(
      `?original=/public/dashboard/${SLUG}`
    )
    await submitPassword(page, 'secret-password')

    expect(store.getters['dashboardApplication/getPublicAuthToken']).toBe(
      'access-token'
    )
    expect(await getToken(nuxtApp, SLUG)).toBe('access-token')
    expect(push).toHaveBeenCalledWith(`/public/dashboard/${SLUG}`)
  })

  test('sends the visitor to the dashboard instead of an external URL', async () => {
    testApp.mock
      .onPost(`/dashboard/public/${SLUG}/auth/`, {
        password: 'secret-password',
      })
      .reply(200, { access_token: 'access-token' })

    const { page, push } = await mountPage(
      '?original=https://attacker.example.com/'
    )
    await submitPassword(page, 'secret-password')

    expect(push).toHaveBeenCalledWith({
      name: 'dashboard-public',
      params: { slug: SLUG },
    })
  })

  test('shows an error for a wrong password', async () => {
    testApp.dontFailOnErrorResponses()
    testApp.mock.onPost(`/dashboard/public/${SLUG}/auth/`).reply(401, {
      error: 'ERROR_NO_AUTHORIZATION_TO_PUBLIC_DASHBOARD',
      detail: 'A valid password is required.',
    })

    const { page, push } = await mountPage()
    await submitPassword(page, 'wrong-password')

    expect(page.text()).toContain('publicDashboardAuth.incorrectPasswordTitle')
    expect(push).not.toHaveBeenCalled()
    expect(store.getters['dashboardApplication/getPublicAuthToken']).toBe(null)
    expect(await getToken(nuxtApp, SLUG)).toBeFalsy()
  })

  test('asks for a password before sending anything', async () => {
    const { page, push } = await mountPage()
    await page.find('form').trigger('submit')
    await flushPromises()

    expect(testApp.mock.history.post).toHaveLength(0)
    expect(page.text()).toContain('error.requiredField')
    expect(push).not.toHaveBeenCalled()
  })
})
