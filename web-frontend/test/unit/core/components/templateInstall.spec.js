import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { ref } from 'vue'

import { useRuntimeConfig } from '#app'
import { TestApp } from '@baserow/test/helpers/testApp'
import TemplateInstall from '@baserow/modules/core/components/template/TemplateInstall'
import { triggerDownload } from '@baserow/modules/core/utils/download'
import CreateWorkspaceModal from '@baserow/modules/core/components/workspace/CreateWorkspaceModal'
import { workspaceSidebarVisibleKey } from '@baserow/modules/core/composables/useWorkspaceSidebar'

// The permission plugin allows everything in tests and can't be replaced.
const permission = vi.hoisted(() => ({ check: () => true }))

vi.mock('#app', async (importOriginal) => {
  const original = await importOriginal()
  return {
    ...original,
    useNuxtApp: () =>
      new Proxy(original.useNuxtApp(), {
        get(target, property) {
          return property === '$hasPermission'
            ? (...args) => permission.check(...args)
            : Reflect.get(target, property)
        },
      }),
  }
})

// Saving the file is replaced, so that nothing navigates. A test can still use
// the real helper.
vi.mock('@baserow/modules/core/utils/download', async (importOriginal) => {
  const original = await importOriginal()
  return { ...original, triggerDownload: vi.fn() }
})

const template = { id: 5, slug: 'project-tracker', name: 'Project Tracker' }

// What the `app` layout provides: whether its sidebar lists the selected workspace.
const withWorkspaceSidebar = (visible) => ({
  provide: { [workspaceSidebarVisibleKey]: ref(visible) },
})

describe('TemplateInstall', () => {
  let testApp = null
  let push = null

  beforeEach(() => {
    testApp = new TestApp()
    push = vi.spyOn(testApp.nuxtApp.$router, 'push').mockResolvedValue()
  })

  afterEach(async () => {
    permission.check = () => true
    push.mockRestore()
    vi.mocked(triggerDownload).mockReset()
    await testApp.afterEach()
  })

  const signIn = () => {
    testApp.authenticate({ id: 1, preferences: {}, completed_onboarding: true })
    testApp.store.dispatch('workspace/forceCreate', { id: 1, name: 'First' })
    testApp.store.dispatch('workspace/forceCreate', { id: 2, name: 'Second' })
  }

  const mockInstall = (workspaceId) =>
    testApp.mock
      .onPost(`/templates/install/${workspaceId}/${template.id}/async/`)
      .reply(202, { id: 10, type: 'install_template', state: 'finished' })

  const clickUse = async (wrapper) => {
    await wrapper.find('.template-install__use').trigger('click')
    await flushPromises()
  }

  test('sends an anonymous visitor to the login page and back', async () => {
    const wrapper = await testApp.mount(TemplateInstall, {
      props: { template },
    })

    expect(wrapper.find('.template-install__workspace').exists()).toBe(false)

    await clickUse(wrapper)

    expect(push).toHaveBeenCalledWith({
      name: 'login',
      query: { original: '/template/project-tracker' },
    })
    expect(testApp.mock.history.post).toHaveLength(0)
    expect(wrapper.emitted('installed')).toBeUndefined()
  })

  test('installs into the provided workspace without redirecting', async () => {
    signIn()
    mockInstall(2)

    const wrapper = await testApp.mount(TemplateInstall, {
      props: { template, workspace: { id: 2 } },
    })
    await clickUse(wrapper)

    expect(testApp.mock.history.post.map((r) => r.url)).toStrictEqual([
      '/templates/install/2/5/async/',
    ])
    // The public revision, or the owner's latest one while it isn't public.
    expect(testApp.mock.history.post[0].params).toStrictEqual({})
    expect(wrapper.emitted('installed')).toHaveLength(1)
    expect(push).not.toHaveBeenCalled()
  })

  test('installs the latest revision when asked to', async () => {
    signIn()
    mockInstall(2)

    const wrapper = await testApp.mount(TemplateInstall, {
      props: { template, workspace: { id: 2 }, latest: true },
    })
    await clickUse(wrapper)

    expect(testApp.mock.history.post.map((r) => r.params)).toStrictEqual([
      { latest: true },
    ])
  })

  test('installs into the first workspace without leaving the page', async () => {
    signIn()
    mockInstall(1)

    const wrapper = await testApp.mount(TemplateInstall, {
      props: { template },
    })
    await clickUse(wrapper)

    expect(testApp.mock.history.post.map((r) => r.url)).toStrictEqual([
      '/templates/install/1/5/async/',
    ])
    expect(wrapper.emitted('installed')).toHaveLength(1)
    expect(push).not.toHaveBeenCalled()
    expect(
      wrapper.find('.template-install__use').attributes('disabled')
    ).toBeUndefined()
  })

  test('disables the workspaces the user cannot add applications to', async () => {
    signIn()
    permission.check = (operation, context, workspaceId) =>
      operation !== 'workspace.create_application' || workspaceId !== 1
    mockInstall(2)

    const wrapper = await testApp.mount(TemplateInstall, {
      props: { template },
    })
    await flushPromises()

    const items = wrapper.findAllComponents({ name: 'DropdownItem' })
    expect(items.map((item) => item.props('disabled'))).toStrictEqual([
      true,
      false,
    ])
    expect(items[0].props('description')).toBe(
      'templateInstall.workspaceNoPermission'
    )

    // The first workspace the template can be installed into is preselected.
    await clickUse(wrapper)

    expect(testApp.mock.history.post.map((r) => r.url)).toStrictEqual([
      '/templates/install/2/5/async/',
    ])
  })

  test('fetches the permissions of every listed workspace', async () => {
    signIn()
    testApp.mock.onGet(/\/workspaces\/\d+\/permissions\//).reply(200, [])

    await testApp.mount(TemplateInstall, { props: { template } })
    await flushPromises()

    expect(
      testApp.store.getters['workspace/getAll'].map(
        (workspace) => workspace._.permissionsLoaded
      )
    ).toStrictEqual([true, true])
  })

  test('cannot install without a workspace to add applications to', async () => {
    signIn()
    permission.check = (operation) =>
      operation !== 'workspace.create_application'

    const wrapper = await testApp.mount(TemplateInstall, {
      props: { template, workspace: { id: 1 } },
    })
    await flushPromises()

    expect(
      wrapper.find('.template-install__use').attributes('disabled')
    ).toBeDefined()
  })

  const installToasts = () =>
    testApp.store.state.toast.items.filter(
      (toast) => toast.type === 'installTemplate'
    )

  const selectWorkspace = (id) =>
    testApp.store.commit(
      'workspace/SET_SELECTED',
      testApp.store.getters['workspace/get'](id)
    )

  test('shows the progress in a toast when no sidebar shows it', async () => {
    signIn()
    selectWorkspace(1)
    mockInstall(1)

    const wrapper = await testApp.mount(TemplateInstall, {
      props: { template, workspace: { id: 1 } },
    })
    await clickUse(wrapper)

    expect(installToasts().map((toast) => toast.data)).toStrictEqual([
      { jobId: 10, template_name: 'Project Tracker' },
    ])
  })

  test('shows the progress in a toast when installing into another workspace', async () => {
    signIn()
    selectWorkspace(1)
    mockInstall(2)

    const wrapper = await testApp.mount(TemplateInstall, {
      props: { template, workspace: { id: 2 } },
      global: withWorkspaceSidebar(true),
    })
    await clickUse(wrapper)

    expect(installToasts()).toHaveLength(1)
  })

  test('leaves the progress to the sidebar of the target workspace', async () => {
    signIn()
    selectWorkspace(1)
    mockInstall(1)

    const wrapper = await testApp.mount(TemplateInstall, {
      props: { template, workspace: { id: 1 } },
      global: withWorkspaceSidebar(true),
    })
    await clickUse(wrapper)

    expect(wrapper.emitted('installed')).toHaveLength(1)
    expect(installToasts()).toHaveLength(0)
  })

  test('shows the progress in a toast when the sidebar is collapsed', async () => {
    signIn()
    selectWorkspace(1)
    mockInstall(1)

    const wrapper = await testApp.mount(TemplateInstall, {
      props: { template, workspace: { id: 1 } },
      global: withWorkspaceSidebar(false),
    })
    await clickUse(wrapper)

    expect(installToasts()).toHaveLength(1)
  })

  test('shows the copy link only when asked', async () => {
    let wrapper = await testApp.mount(TemplateInstall, {
      props: { template },
    })
    await wrapper
      .find('.template-install__actions .button-icon')
      .trigger('click')
    expect(wrapper.findAll('.context__menu-item-link')).toHaveLength(1)

    wrapper = await testApp.mount(TemplateInstall, {
      props: { template, showCopyLink: false },
    })
    await wrapper
      .find('.template-install__actions .button-icon')
      .trigger('click')
    expect(wrapper.findAll('.context__menu-item-link')).toHaveLength(0)
  })

  test('does not report a failed install as installed', async () => {
    signIn()
    testApp.dontFailOnErrorResponses()
    testApp.mock
      .onPost(`/templates/install/1/${template.id}/async/`)
      .reply(400, { error: 'ERROR_USER_NOT_IN_GROUP' })

    const wrapper = await testApp.mount(TemplateInstall, {
      props: { template, workspace: { id: 1 } },
    })
    await clickUse(wrapper)

    expect(wrapper.emitted('installed')).toBeUndefined()
    expect(push).not.toHaveBeenCalled()
    expect(installToasts()).toHaveLength(0)
    expect(
      wrapper.find('.template-install__use').attributes('disabled')
    ).toBeUndefined()
  })
  describe('download', () => {
    const userTemplate = {
      id: 5,
      type: 'user',
      slug: 'crm-a1b2c3',
      name: 'CRM',
    }
    const downloadUrl = '/templates/crm-a1b2c3/download/'
    const file = {
      url: 'http://localhost:8000/media/template-revisions/abc.zip',
      file_name: 'crm.zip',
    }

    // The copied label is left out of the texts of the menu.
    const mountWithMenu = async (props, { mocks = {}, slots = {} } = {}) => {
      const wrapper = await testApp.mount(TemplateInstall, {
        props,
        slots,
        global: { mocks, stubs: { Copied: true } },
      })
      await flushPromises()
      await wrapper
        .find('.template-install__actions .button-icon')
        .trigger('click')
      await flushPromises()
      return wrapper
    }

    const menuTexts = (wrapper) =>
      wrapper.findAll('.context__menu-item-link').map((link) => link.text())

    const downloadLink = (wrapper) =>
      wrapper
        .findAll('.context__menu-item-link')
        .find((link) => link.text() === 'templateInstall.download')

    // The click doesn't bubble, so that only the item handles it. In the tests the
    // menu is rendered again with a new element, which its check of the clicks
    // outside of it would take as one.
    const clickDownload = async (wrapper) => {
      downloadLink(wrapper).element.dispatchEvent(
        new MouseEvent('click', { bubbles: false, cancelable: true })
      )
      await flushPromises()
    }

    const menuIsOpen = (wrapper) =>
      wrapper.findComponent({ name: 'Context' }).vm.isOpen()

    const downloadRequests = () =>
      testApp.mock.history.get.filter((request) =>
        request.url.endsWith('/download/')
      )

    const errorToasts = () =>
      testApp.store.state.toast.items.filter((toast) => toast.type === 'error')

    test('shows Download after the copy link of a user template', async () => {
      signIn()
      const wrapper = await mountWithMenu({ template: userTemplate })

      expect(menuTexts(wrapper)).toStrictEqual([
        'templateInstall.copyLink',
        'templateInstall.download',
      ])
      const icon = downloadLink(wrapper).find('i')
      expect(icon.classes()).toContain('iconoir-download')
      // The URL is only fetched at the click.
      expect(downloadRequests()).toHaveLength(0)
    })

    test('does not show Download for an official template', async () => {
      signIn()
      const wrapper = await mountWithMenu({ template })

      expect(menuTexts(wrapper)).toStrictEqual(['templateInstall.copyLink'])
    })

    test('does not show Download when user templates are off', async () => {
      signIn()
      const wrapper = await mountWithMenu(
        { template: userTemplate },
        { mocks: { $featureFlagIsEnabled: () => false } }
      )

      expect(menuTexts(wrapper)).toStrictEqual(['templateInstall.copyLink'])
    })

    test('separates the copy link and Download from the items of the slot', async () => {
      signIn()
      const wrapper = await mountWithMenu(
        { template: userTemplate },
        {
          slots: {
            'menu-items': '<li class="context__menu-item">Own</li>',
            'menu-items-end': '<li class="context__menu-item">End</li>',
          },
        }
      )

      const items = wrapper.findAll('.context__menu-item')
      expect(items.map((item) => item.text())).toStrictEqual([
        'Own',
        'templateInstall.copyLink',
        'templateInstall.download',
        'End',
      ])
      expect(
        items.map((item) =>
          item.classes().includes('context__menu-item--with-separator')
        )
      ).toStrictEqual([false, true, false, false])
    })

    test('separates Download from the slot without a copy link', async () => {
      signIn()
      const wrapper = await mountWithMenu(
        { template: userTemplate, showCopyLink: false },
        { slots: { 'menu-items': '<li class="context__menu-item">Own</li>' } }
      )

      const items = wrapper.findAll('.context__menu-item')
      expect(items.map((item) => item.text())).toStrictEqual([
        'Own',
        'templateInstall.download',
      ])
      expect(items[1].classes()).toContain('context__menu-item--with-separator')
    })

    test('downloads the file of the fetched URL, then closes the menu', async () => {
      signIn()
      let reply = null
      testApp.mock.onGet(downloadUrl).reply(
        () =>
          new Promise((resolve) => {
            reply = resolve
          })
      )
      const wrapper = await mountWithMenu({ template: userTemplate })

      await clickDownload(wrapper)

      // While the URL is fetched the item shows it, and the menu stays open.
      expect(downloadLink(wrapper).classes()).toContain(
        'context__menu-item-link--loading'
      )
      expect(menuIsOpen(wrapper)).toBe(true)

      // A second click doesn't fetch it again, nor closes the menu.
      await clickDownload(wrapper)
      expect(downloadRequests()).toHaveLength(1)
      expect(downloadLink(wrapper).classes()).toContain(
        'context__menu-item-link--loading'
      )
      expect(menuIsOpen(wrapper)).toBe(true)
      // The public revision, or the owner's latest one while it isn't public.
      expect(downloadRequests()[0].params).toStrictEqual({})

      reply([200, file])
      await flushPromises()

      expect(triggerDownload).toHaveBeenCalledTimes(1)
      expect(triggerDownload).toHaveBeenCalledWith(file.url, file.file_name, {
        viaXhr: false,
      })
      expect(downloadLink(wrapper).classes()).not.toContain(
        'context__menu-item-link--loading'
      )
      expect(menuIsOpen(wrapper)).toBe(false)
      expect(push).not.toHaveBeenCalled()
    })

    test('downloads the latest revision when asked to', async () => {
      signIn()
      testApp.mock.onGet(downloadUrl).reply(200, file)
      const wrapper = await mountWithMenu({
        template: userTemplate,
        latest: true,
      })

      await clickDownload(wrapper)

      expect(downloadRequests().map((request) => request.params)).toStrictEqual(
        [{ latest: true }]
      )
      expect(triggerDownload).toHaveBeenCalledTimes(1)
    })

    test('shows why a template without a file is not downloaded', async () => {
      signIn()
      testApp.dontFailOnErrorResponses()
      testApp.mock.onGet(downloadUrl).reply(400, {
        error: 'ERROR_TEMPLATE_FILE_DOES_NOT_EXIST',
        detail: 'The file of the template does not exist.',
      })
      const wrapper = await mountWithMenu({ template: userTemplate })

      await clickDownload(wrapper)

      expect(triggerDownload).not.toHaveBeenCalled()
      expect(errorToasts().map((toast) => toast.title)).toStrictEqual([
        'clientHandler.templateFileDoesNotExistTitle',
      ])
      expect(downloadLink(wrapper).classes()).not.toContain(
        'context__menu-item-link--loading'
      )
    })

    test('shows an error when the file cannot be saved', async () => {
      signIn()
      testApp.mock.onGet(downloadUrl).reply(200, file)
      vi.mocked(triggerDownload).mockRejectedValueOnce(new Error('403'))
      const wrapper = await mountWithMenu({ template: userTemplate })

      await clickDownload(wrapper)

      expect(errorToasts().map((toast) => toast.title)).toStrictEqual([
        'clientHandler.notCompletedTitle',
      ])
      expect(menuIsOpen(wrapper)).toBe(false)
    })

    test.each([403, 404])(
      'saves nothing when the storage answers %i through XHR',
      async (status) => {
        signIn()
        const config = useRuntimeConfig()
        const viaXhr = config.public.downloadFileViaXhr
        config.public.downloadFileViaXhr = '1'
        const original = await vi.importActual(
          '@baserow/modules/core/utils/download'
        )
        vi.mocked(triggerDownload).mockImplementationOnce(
          original.triggerDownload
        )
        const fetch = vi.fn(() => Promise.resolve({ ok: false, status }))
        vi.stubGlobal('fetch', fetch)
        const click = vi
          .spyOn(HTMLAnchorElement.prototype, 'click')
          .mockImplementation(() => {})
        testApp.mock.onGet(downloadUrl).reply(200, file)

        try {
          const wrapper = await mountWithMenu({ template: userTemplate })
          await clickDownload(wrapper)

          expect(fetch).toHaveBeenCalledWith(file.url, { cache: 'no-store' })
          expect(click).not.toHaveBeenCalled()
          expect(errorToasts().map((toast) => toast.title)).toStrictEqual([
            'clientHandler.notCompletedTitle',
          ])
        } finally {
          config.public.downloadFileViaXhr = viaXhr
          click.mockRestore()
          vi.unstubAllGlobals()
        }
      }
    )

    test('sends an anonymous visitor to the login page and back', async () => {
      const wrapper = await mountWithMenu({ template: userTemplate })

      await clickDownload(wrapper)

      expect(push).toHaveBeenCalledWith({
        name: 'login',
        query: { original: '/template/crm-a1b2c3' },
      })
      expect(downloadRequests()).toHaveLength(0)
      expect(triggerDownload).not.toHaveBeenCalled()
    })
  })

  describe('without a workspace', () => {
    const userTemplate = {
      id: 5,
      type: 'user',
      slug: 'crm-a1b2c3',
      name: 'CRM',
    }

    const signInWithoutWorkspace = () =>
      testApp.authenticate({
        id: 1,
        preferences: {},
        completed_onboarding: true,
      })

    const mountWithoutWorkspace = (props, canCreateWorkspace = true) =>
      testApp.mount(TemplateInstall, {
        props,
        global: {
          mocks: { $hasPermission: () => canCreateWorkspace },
        },
      })

    describe.each([
      ['an official template', template],
      ['a user template', userTemplate],
    ])('of %s', (_name, shownTemplate) => {
      test('creates a workspace and installs into it without leaving', async () => {
        signInWithoutWorkspace()
        const wrapper = await mountWithoutWorkspace({ template: shownTemplate })

        expect(wrapper.find('.template-install__no-workspace').text()).toBe(
          'templateInstall.noWorkspace'
        )
        expect(wrapper.find('.template-install__workspace').exists()).toBe(
          false
        )
        expect(wrapper.find('.template-install__use').exists()).toBe(false)

        await wrapper
          .find('.template-install__create-workspace')
          .trigger('click')
        const modal = wrapper.findComponent(CreateWorkspaceModal)
        expect(modal.vm.$refs.modal.isOpen()).toBe(true)

        // Done by the modal before it reports the new workspace.
        await testApp.store.dispatch('workspace/forceCreate', {
          id: 3,
          name: 'New',
        })
        modal.vm.$emit('created', testApp.store.getters['workspace/get'](3))
        await flushPromises()

        expect(wrapper.find('.template-install__no-workspace').exists()).toBe(
          false
        )
        expect(
          wrapper.find('.template-install__create-workspace').exists()
        ).toBe(false)
        expect(
          wrapper.findComponent({ name: 'Dropdown' }).props('modelValue')
        ).toBe(3)
        expect(
          wrapper.find('.template-install__use').attributes('disabled')
        ).toBeUndefined()

        testApp.mock
          .onPost(`/templates/install/3/${shownTemplate.id}/async/`)
          .reply(202, { id: 10, type: 'install_template', state: 'finished' })
        await clickUse(wrapper)

        expect(testApp.mock.history.post.map((r) => r.url)).toStrictEqual([
          `/templates/install/3/${shownTemplate.id}/async/`,
        ])
        expect(wrapper.emitted('installed')).toHaveLength(1)
        expect(push).not.toHaveBeenCalled()
      })

      test('asks to be invited when the user may not create a workspace', async () => {
        signInWithoutWorkspace()
        const wrapper = await mountWithoutWorkspace(
          { template: shownTemplate },
          false
        )

        expect(wrapper.find('.template-install__no-workspace').text()).toBe(
          'templateInstall.noWorkspaceAskInvite'
        )
        expect(
          wrapper.find('.template-install__create-workspace').exists()
        ).toBe(false)
        expect(wrapper.find('.template-install__workspace').exists()).toBe(
          false
        )
        expect(
          wrapper.find('.template-install__use').attributes('disabled')
        ).toBeDefined()
      })
    })

    test('shows the picker, not the create button, to a user with a workspace', async () => {
      signIn()
      const wrapper = await mountWithoutWorkspace({ template })

      expect(wrapper.find('.template-install__no-workspace').exists()).toBe(
        false
      )
      expect(wrapper.find('.template-install__create-workspace').exists()).toBe(
        false
      )
      expect(wrapper.find('.template-install__workspace').exists()).toBe(true)
    })

    test('shows neither to an anonymous visitor', async () => {
      const wrapper = await mountWithoutWorkspace({ template })

      expect(wrapper.find('.template-install__no-workspace').exists()).toBe(
        false
      )
      expect(wrapper.find('.template-install__create-workspace').exists()).toBe(
        false
      )
      expect(wrapper.findComponent(CreateWorkspaceModal).exists()).toBe(false)
    })
  })
})
