import { flushPromises } from '@vue/test-utils'
import { vi } from 'vitest'

import { TestApp } from '@baserow/test/helpers/testApp'
import ShareDashboardLink from '@baserow/modules/dashboard/components/sharing/ShareDashboardLink'
import DashboardRotateSlugModal from '@baserow/modules/dashboard/components/sharing/DashboardRotateSlugModal'
import Context from '@baserow/modules/core/components/Context'
import { copyToClipboard } from '@baserow/modules/database/utils/clipboard'

vi.mock(
  '@baserow/modules/database/utils/clipboard',
  async (importOriginal) => ({
    ...(await importOriginal()),
    copyToClipboard: vi.fn(),
  })
)

const DASHBOARD_ID = 10

describe('ShareDashboardLink', () => {
  let testApp = null
  let store = null

  beforeEach(() => {
    testApp = new TestApp()
    store = testApp.getStore()
  })

  afterEach(() => testApp.afterEach())

  async function createDashboard(values = {}) {
    const workspace = { id: 1, name: 'Workspace' }
    await store.dispatch('workspace/forceCreate', workspace)
    await store.dispatch('application/forceCreate', {
      id: DASHBOARD_ID,
      type: 'dashboard',
      name: 'Conversion compass',
      workspace,
      public: false,
      slug: 'dashboard-slug',
      public_has_password: false,
      show_logo: true,
      ...values,
    })
    return store.getters['application/get'](DASHBOARD_ID)
  }

  async function openContext(dashboard) {
    const wrapper = await testApp.mount(ShareDashboardLink, {
      props: { dashboard },
    })
    await wrapper.find('.header__filter-link').trigger('click')
    const context = wrapper.findComponent(Context)
    expect(context.isVisible()).toBe(true)
    return { wrapper, context }
  }

  function findButtonByText(wrapper, text) {
    return wrapper
      .findAll('button')
      .filter((button) => button.text().includes(text))
      .at(0)
  }

  function expectedShareUrl(slug) {
    const { baserowEmbeddedShareUrl } = testApp.getApp().$config.public
    return `${baserowEmbeddedShareUrl}/public/dashboard/${slug}`
  }

  test('creates a private link for a dashboard that is not shared yet', async () => {
    const dashboard = await createDashboard()
    testApp.mock
      .onPatch(`/applications/${DASHBOARD_ID}/`, { public: true })
      .reply(200, { id: DASHBOARD_ID, type: 'dashboard', public: true })

    const { context } = await openContext(dashboard)

    expect(context.text()).toContain('shareDashboardLink.notSharedTitle')
    expect(context.find('.dashboard-sharing__shared-link-box').exists()).toBe(
      false
    )

    await findButtonByText(
      context,
      'shareDashboardLink.createPrivateLink'
    ).trigger('click')
    await flushPromises()

    expect(store.getters['application/get'](DASHBOARD_ID).public).toBe(true)
    expect(context.text()).toContain('shareDashboardLink.sharedTitle')
    expect(context.find('.dashboard-sharing__shared-link-box').text()).toBe(
      expectedShareUrl('dashboard-slug')
    )
  })

  test('shows the public URL and copies it to the clipboard', async () => {
    const dashboard = await createDashboard({ public: true })

    const { context } = await openContext(dashboard)

    expect(context.find('.dashboard-sharing__shared-link-box').text()).toBe(
      expectedShareUrl('dashboard-slug')
    )

    await context
      .findAll('.dashboard-sharing__shared-link-action')
      .at(0)
      .trigger('click')

    expect(copyToClipboard).toHaveBeenCalledWith(
      expectedShareUrl('dashboard-slug')
    )
    expect(context.find('.copied--show').exists()).toBe(true)
  })

  test('disables the shared link', async () => {
    const dashboard = await createDashboard({ public: true })
    testApp.mock
      .onPatch(`/applications/${DASHBOARD_ID}/`, { public: false })
      .reply(200, { id: DASHBOARD_ID, type: 'dashboard', public: false })

    const { context } = await openContext(dashboard)

    await findButtonByText(context, 'shareDashboardLink.disableLink').trigger(
      'click'
    )
    await flushPromises()

    expect(store.getters['application/get'](DASHBOARD_ID).public).toBe(false)
    expect(context.text()).toContain('shareDashboardLink.notSharedTitle')
    expect(context.find('.dashboard-sharing__shared-link-box').exists()).toBe(
      false
    )
  })

  test('rotates the slug after confirmation and shows a success toast', async () => {
    const dashboard = await createDashboard({ public: true })
    testApp.mock.onPost(`/dashboard/${DASHBOARD_ID}/rotate-slug/`).reply(200, {
      id: DASHBOARD_ID,
      type: 'dashboard',
      public: true,
      slug: 'rotated-slug',
    })

    const { wrapper, context } = await openContext(dashboard)

    await context
      .findAll('.dashboard-sharing__shared-link-action')
      .at(1)
      .trigger('click')

    const modal = wrapper.findComponent(DashboardRotateSlugModal)
    expect(modal.text()).toContain('dashboardRotateSlugModal.title')
    expect(store.getters['application/get'](DASHBOARD_ID).slug).toBe(
      'dashboard-slug'
    )

    await findButtonByText(
      modal,
      'dashboardRotateSlugModal.generateNewUrl'
    ).trigger('click')
    await flushPromises()

    expect(store.getters['application/get'](DASHBOARD_ID).slug).toBe(
      'rotated-slug'
    )
    expect(context.find('.dashboard-sharing__shared-link-box').text()).toBe(
      expectedShareUrl('rotated-slug')
    )
    expect(store.state.toast.items).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          type: 'success',
          title: 'dashboardRotateSlugModal.success',
        }),
      ])
    )
  })

  test('keeps the slug when the rotation is cancelled', async () => {
    const dashboard = await createDashboard({ public: true })

    const { wrapper, context } = await openContext(dashboard)

    await context
      .findAll('.dashboard-sharing__shared-link-action')
      .at(1)
      .trigger('click')

    const modal = wrapper.findComponent(DashboardRotateSlugModal)
    await findButtonByText(modal, 'action.cancel').trigger('click')
    await flushPromises()

    expect(store.getters['application/get'](DASHBOARD_ID).slug).toBe(
      'dashboard-slug'
    )
    expect(store.state.toast.items).toHaveLength(0)
  })
})
