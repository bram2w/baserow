import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

import { TestApp } from '@baserow/test/helpers/testApp'
import UserTemplateList from '@baserow/modules/core/components/template/UserTemplateList'
import InfiniteScroll from '@baserow/modules/core/components/helpers/InfiniteScroll'

// The permission plugin allows everything in tests and can't be replaced.
const permission = vi.hoisted(() => ({ allowed: true }))

vi.mock('#app', async (importOriginal) => {
  const original = await importOriginal()
  return {
    ...original,
    useNuxtApp: () =>
      new Proxy(original.useNuxtApp(), {
        get(target, property) {
          return property === '$hasPermission'
            ? () => permission.allowed
            : Reflect.get(target, property)
        },
      }),
  }
})

const userTemplate = (id, name, state = 'private', extra = {}) => ({
  id,
  type: 'user',
  name,
  slug: `${name.toLowerCase().replace(/ /g, '-')}-a1b2c3`,
  description: `${name} description`,
  icon: 'iconoir-table',
  workspace_id: 100 + id,
  open_application: null,
  categories: [],
  state,
  reason: null,
  created_on: '2026-10-01T10:00:00Z',
  updated_on: '2026-10-01T10:00:00Z',
  ...extra,
})

const page = (templates, count = templates.length) => ({
  count,
  next: null,
  previous: null,
  results: templates,
})

describe('UserTemplateList', () => {
  let testApp = null
  let requests = []

  // Replies with the given pages in order and records the query of each request.
  const mockPages = (...pages) => {
    pages.forEach((data) => {
      testApp.mock.onGet('/templates/own/').replyOnce((config) => {
        requests.push(config.params)
        return [200, data]
      })
    })
  }

  beforeEach(async () => {
    testApp = new TestApp()
    requests = []
    const { store } = testApp
    await store.dispatch('workspace/forceCreate', { id: 1, name: 'Acme' })
    // Loaded, so that they aren't fetched.
    store.commit('workspace/SET_PERMISSIONS', {
      workspaceId: 1,
      permissions: [],
    })
  })

  afterEach(async () => {
    vi.useRealTimers()
    permission.allowed = true
    await testApp.afterEach()
  })

  const mountComponent = async (props = {}) => {
    const wrapper = await testApp.mount(UserTemplateList, { props })
    await flushPromises()
    return wrapper
  }

  const rowNames = (wrapper) =>
    wrapper.findAll('.user-template-list__name-title').map((el) => el.text())

  test('lists the templates with their state and description', async () => {
    mockPages(
      page([
        userTemplate(1, 'Sprint Tracker', 'public'),
        userTemplate(2, 'Content Calendar', 'rejected', {
          reason: 'Contains personal data.',
          description: '',
        }),
        userTemplate(3, 'Client Onboarding', 'private'),
        userTemplate(4, 'Growth Playbook', 'blocked'),
        userTemplate(5, 'Launch Plan', 'in_review'),
      ])
    )
    const wrapper = await mountComponent()

    expect(requests).toStrictEqual([{ offset: 0, limit: 20 }])
    expect(wrapper.find('.user-template-list__title').text()).toBe(
      'userTemplateList.count - 5'
    )
    expect(rowNames(wrapper)).toStrictEqual([
      'Sprint Tracker',
      'Content Calendar',
      'Client Onboarding',
      'Growth Playbook',
      'Launch Plan',
    ])
    expect(
      wrapper.findAll('.user-template-list__description').map((el) => el.text())
    ).toStrictEqual([
      'Sprint Tracker description',
      'Client Onboarding description',
      'Growth Playbook description',
      'Launch Plan description',
    ])

    const badges = wrapper.findAll('.badge')
    expect(badges.map((badge) => badge.text())).toStrictEqual([
      'userTemplateList.statePublic',
      'userTemplateList.stateRejected',
      'userTemplateList.statePrivate',
      'userTemplateList.stateBlocked',
      'userTemplateList.stateInReview',
    ])
    expect(badges.map((badge) => badge.classes())).toStrictEqual([
      expect.arrayContaining(['badge--green']),
      expect.arrayContaining(['badge--red']),
      expect.arrayContaining(['badge--neutral']),
      expect.arrayContaining(['badge--red']),
      expect.arrayContaining(['badge--yellow']),
    ])
    expect(wrapper.find('.template-empty-state').exists()).toBe(false)
  })

  test('shows the empty state when the user has no templates', async () => {
    mockPages(page([]))
    const wrapper = await mountComponent()

    expect(wrapper.find('.template-empty-state__title').text()).toBe(
      'userTemplateList.emptyTitle'
    )
    expect(wrapper.find('.template-empty-state__icon i').classes()).toContain(
      'iconoir-box'
    )
    expect(wrapper.find('.user-template-list__table').exists()).toBe(false)
    // Nothing to search in.
    expect(wrapper.find('.user-template-list__search').exists()).toBe(false)

    await wrapper.find('.template-empty-state .button').trigger('click')
    expect(wrapper.emitted('create')).toHaveLength(1)
  })

  test('shows only the loading state until the list is loaded', async () => {
    let reply = null
    testApp.mock.onGet('/templates/own/').replyOnce(
      () =>
        new Promise((resolve) => {
          reply = resolve
        })
    )
    const wrapper = await testApp.mount(UserTemplateList, { props: {} })
    await flushPromises()

    expect(wrapper.find('.user-template-list__loading').exists()).toBe(true)
    expect(wrapper.find('.user-template-list__toolbar').exists()).toBe(false)
    expect(wrapper.find('.template-empty-state').exists()).toBe(false)

    reply([200, page([])])
    await flushPromises()

    expect(wrapper.find('.user-template-list__loading').exists()).toBe(false)
    expect(wrapper.find('.template-empty-state').exists()).toBe(true)
  })

  test('shows a state that it does not know as it is', async () => {
    mockPages(page([userTemplate(1, 'Sprint Tracker', 'archived')]))
    const wrapper = await mountComponent()

    expect(rowNames(wrapper)).toStrictEqual(['Sprint Tracker'])
    expect(wrapper.find('.badge').text()).toBe('archived')
    expect(wrapper.find('.badge').classes()).toContain('badge--neutral')
  })

  test('shows an error when the list could not be loaded', async () => {
    testApp.mock.onGet('/templates/own/').replyOnce(500)
    mockPages(page([userTemplate(1, 'Sprint Tracker')]))
    const wrapper = await mountComponent()

    expect(wrapper.find('.template-empty-state__title').text()).toBe(
      'userTemplateList.errorTitle'
    )
    expect(wrapper.text()).not.toContain('userTemplateList.emptyTitle')

    await wrapper.find('.template-empty-state .button').trigger('click')
    await flushPromises()

    expect(wrapper.find('.template-empty-state').exists()).toBe(false)
    expect(rowNames(wrapper)).toStrictEqual(['Sprint Tracker'])
  })

  describe('without a workspace to create a template from', () => {
    const toolbarButton = (wrapper) =>
      wrapper.find('.user-template-list__toolbar .button')

    // The reason is shown as the tooltip of the disabled button.
    const tooltip = async (wrapper) => {
      await toolbarButton(wrapper).element.parentElement.dispatchEvent(
        new MouseEvent('mouseenter')
      )
      return document.body.querySelector('.tooltip__content')?.textContent
    }

    const scenarios = [
      ['no workspaces', 'userTemplateList.noWorkspace'],
      ['no exportable workspace', 'userTemplateList.noPermission'],
    ]

    const setUp = (scenario) => {
      if (scenario === 'no workspaces') {
        testApp.store.commit('workspace/DELETE_ITEM', 1)
      } else {
        permission.allowed = false
      }
    }

    test.each(scenarios)(
      'explains the empty state with %s',
      async (scenario, reason) => {
        setUp(scenario)
        mockPages(page([]))
        const wrapper = await mountComponent()

        expect(wrapper.find('.template-empty-state__description').text()).toBe(
          reason
        )
        expect(wrapper.find('.template-empty-state .button').exists()).toBe(
          false
        )
      }
    )

    test.each(scenarios)(
      'disables the button of the list with %s',
      async (scenario, reason) => {
        setUp(scenario)
        mockPages(page([userTemplate(1, 'Sprint Tracker')]))
        const wrapper = await mountComponent()

        expect(toolbarButton(wrapper).attributes('disabled')).toBeDefined()
        expect(await tooltip(wrapper)).toBe(reason)

        await toolbarButton(wrapper).trigger('click')
        expect(wrapper.emitted('create')).toBeUndefined()
      }
    )

    test('enables the button of the list with an exportable workspace', async () => {
      mockPages(page([userTemplate(1, 'Sprint Tracker')]))
      const wrapper = await mountComponent()

      expect(toolbarButton(wrapper).attributes('disabled')).toBeUndefined()
      expect(await tooltip(wrapper)).toBeUndefined()

      await toolbarButton(wrapper).trigger('click')
      expect(wrapper.emitted('create')).toHaveLength(1)
    })
  })

  test('searches on the server after typing stops', async () => {
    mockPages(
      page([userTemplate(1, 'Sprint Tracker'), userTemplate(2, 'Calendar')]),
      page([userTemplate(1, 'Sprint Tracker')]),
      page([])
    )
    const wrapper = await mountComponent()
    vi.useFakeTimers()

    const input = wrapper.find('.user-template-list__search input')
    await input.setValue('spr')
    await input.setValue('sprint')
    expect(requests).toHaveLength(1)

    await vi.runAllTimersAsync()
    await flushPromises()

    expect(requests).toStrictEqual([
      { offset: 0, limit: 20 },
      { offset: 0, limit: 20, search: 'sprint' },
    ])
    expect(rowNames(wrapper)).toStrictEqual(['Sprint Tracker'])

    // No matches is not the same as no templates at all.
    await input.setValue('nothing')
    await vi.runAllTimersAsync()
    await flushPromises()

    expect(requests[2]).toStrictEqual({
      offset: 0,
      limit: 20,
      search: 'nothing',
    })
    expect(wrapper.find('.template-empty-state__title').text()).toBe(
      'templateEmptyState.noResultsTitle'
    )
    expect(wrapper.find('.template-empty-state__icon i').classes()).toContain(
      'iconoir-search'
    )
    // The search stays available and the table is replaced.
    expect(wrapper.find('.user-template-list__search').exists()).toBe(true)
    expect(wrapper.find('.user-template-list__table').exists()).toBe(false)
  })

  test('loads the next page when scrolled to the end', async () => {
    const firstPage = Array.from({ length: 20 }, (_, i) =>
      userTemplate(i + 1, `Template ${i + 1}`)
    )
    mockPages(page(firstPage, 21), page([userTemplate(21, 'Template 21')], 21))
    const wrapper = await mountComponent()

    expect(rowNames(wrapper)).toHaveLength(20)

    wrapper.findComponent(InfiniteScroll).vm.$emit('load-next-page', 2)
    await flushPromises()

    expect(requests).toStrictEqual([
      { offset: 0, limit: 20 },
      { offset: 20, limit: 20 },
    ])
    expect(rowNames(wrapper)).toHaveLength(21)
    expect(rowNames(wrapper)[20]).toBe('Template 21')
  })

  test('emits the template of a clicked row', async () => {
    const template = userTemplate(1, 'Sprint Tracker')
    mockPages(page([template]))
    const wrapper = await mountComponent()

    await wrapper
      .find('.user-template-list__row:not(.user-template-list__row--head)')
      .trigger('click')

    expect(wrapper.emitted('selected')).toStrictEqual([[template]])
  })

  test('reloads the first page on refresh', async () => {
    mockPages(
      page([userTemplate(1, 'Sprint Tracker')]),
      page([userTemplate(2, 'New One'), userTemplate(1, 'Sprint Tracker')])
    )
    const wrapper = await mountComponent()

    await wrapper.vm.refresh()
    await flushPromises()

    expect(requests).toStrictEqual([
      { offset: 0, limit: 20 },
      { offset: 0, limit: 20 },
    ])
    expect(rowNames(wrapper)).toStrictEqual(['New One', 'Sprint Tracker'])
  })
})
