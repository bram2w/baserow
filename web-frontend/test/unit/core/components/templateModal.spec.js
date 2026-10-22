import { defineComponent } from 'vue'
import { flushPromises, shallowMount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { TestApp } from '@baserow/test/helpers/testApp'
import TemplateModal from '@baserow/modules/core/components/template/TemplateModal'

const projectTracker = {
  id: 1,
  slug: 'project-tracker',
  name: 'Project Tracker',
}
const recipeBook = { id: 2, slug: 'recipe-book', name: 'Recipe Book' }

const categories = [
  { id: 1, name: 'Business', templates: [projectTracker] },
  { id: 2, name: 'Personal', templates: [recipeBook] },
]
// The id of an official template, to show that it doesn't pick its categories.
const sprintTracker = {
  id: 2,
  type: 'user',
  slug: 'sprint-tracker-a1b2c3',
  name: 'Sprint Tracker',
  categories: [{ id: 7, name: 'Agile' }],
}

const ModalStub = defineComponent({
  name: 'Modal',
  props: ['keepContent', 'fullScreen', 'closeButton'],
  emits: ['show', 'hidden'],
  methods: {
    show() {
      this.$emit('show')
    },
    hide() {
      this.$emit('hidden')
    },
  },
  template: '<div><slot /></div>',
})

describe('TemplateModal', () => {
  const mountComponent = () => {
    return shallowMount(TemplateModal, {
      propsData: {
        workspace: {
          id: 1,
        },
      },
      global: {
        stubs: {
          Modal: ModalStub,
          TemplateList: true,
          TemplateDetails: true,
        },
        mocks: { $featureFlagIsEnabled: () => false },
      },
    })
  }

  it('keeps the root modal content mounted while closed', () => {
    const wrapper = mountComponent()

    expect(wrapper.findComponent({ name: 'Modal' }).props('keepContent')).toBe(
      ''
    )
  })
})

describe('TemplateModal navigation', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
    testApp.mock.onGet('/templates/').reply(200, categories)
  })

  afterEach(async () => {
    mocks = {}
    refreshList = vi.fn()
    showCreateModal = vi.fn()
    await testApp.afterEach()
  })

  let mocks = {}

  const stubs = {
    Modal: ModalStub,
    TemplateDetails: defineComponent({
      name: 'TemplateDetails',
      props: ['template', 'categories', 'workspace', 'showBack'],
      emits: ['back', 'installed'],
      template: `<div class="details">
        {{ template.name }}: {{ categories.map((c) => c.name).join(',') }}
        <a class="details__back" @click="$emit('back')" />
      </div>`,
    }),
    TemplateList: defineComponent({
      name: 'TemplateList',
      props: ['categories', 'active'],
      emits: ['selected'],
      template: `<div class="list">
        <slot name="head" />
        <a class="list__recipe-book" @click="$emit('selected', categories[1].templates[0])" />
      </div>`,
    }),
    UserTemplateList: defineComponent({
      name: 'UserTemplateList',
      props: ['active'],
      emits: ['selected', 'create'],
      template: `<div class="own-list">
        <slot name="head" />
        <a class="own-list__sprint-tracker" @click="$emit('selected', sprintTracker)" />
        <a class="own-list__create" @click="$emit('create')" />
      </div>`,
      setup: () => ({ sprintTracker }),
      methods: {
        refresh() {
          refreshList()
        },
      },
    }),
    CreateUserTemplateModal: defineComponent({
      name: 'CreateUserTemplateModal',
      props: ['categories'],
      emits: ['created', 'hidden'],
      methods: {
        show() {
          showCreateModal()
        },
      },
      template: '<div class="create-modal" />',
    }),
  }

  let refreshList = vi.fn()
  let showCreateModal = vi.fn()

  const mountAndShow = async (...args) => {
    const wrapper = await testApp.mount(TemplateModal, {
      props: { workspace: { id: 1 } },
      global: { stubs, mocks },
    })
    await wrapper.vm.show(...args)
    await flushPromises()
    return wrapper
  }

  it('opens the list, a template from it and goes back', async () => {
    const wrapper = await mountAndShow()

    expect(wrapper.find('.details').exists()).toBe(false)
    expect(wrapper.find('.list').isVisible()).toBe(true)

    await wrapper.find('.list__recipe-book').trigger('click')

    expect(wrapper.find('.details').text()).toBe('Recipe Book: Personal')
    expect(wrapper.find('.list').isVisible()).toBe(false)

    await wrapper.find('.details__back').trigger('click')

    expect(wrapper.find('.details').exists()).toBe(false)
    expect(wrapper.find('.list').isVisible()).toBe(true)
  })

  it('opens the template with the given id or slug right away', async () => {
    let wrapper = await mountAndShow(2)
    expect(wrapper.find('.details').text()).toBe('Recipe Book: Personal')

    wrapper = await mountAndShow('project-tracker')
    expect(wrapper.find('.details').text()).toBe('Project Tracker: Business')
  })

  it('opens the default template right away', async () => {
    testApp.mock.resetHandlers()
    testApp.mock.onGet('/templates/').reply(200, [
      { ...categories[0], templates: [projectTracker] },
      { ...categories[1], templates: [{ ...recipeBook, is_default: true }] },
    ])
    const wrapper = await mountAndShow()

    expect(wrapper.find('.details').text()).toBe('Recipe Book: Personal')

    await wrapper.find('.details__back').trigger('click')

    expect(wrapper.find('.list').isVisible()).toBe(true)
  })

  it('opens the list again when shown after a template was opened', async () => {
    const wrapper = await mountAndShow('project-tracker')

    await wrapper.vm.show()
    await flushPromises()

    expect(wrapper.find('.details').exists()).toBe(false)
    expect(wrapper.find('.list').isVisible()).toBe(true)
  })

  it('lets the list claim the search shortcut only while it is shown', async () => {
    const wrapper = await mountAndShow()
    const list = () => wrapper.findComponent({ name: 'TemplateList' })

    expect(list().props('active')).toBe(true)

    await wrapper.find('.list__recipe-book').trigger('click')
    expect(list().props('active')).toBe(false)

    await wrapper.find('.details__back').trigger('click')
    expect(list().props('active')).toBe(true)

    // The list stays mounted while the modal is closed.
    await wrapper.vm.hide()
    expect(list().exists()).toBe(true)
    expect(list().props('active')).toBe(false)
  })

  it('closes the template however the modal is hidden', async () => {
    const wrapper = await mountAndShow('project-tracker')

    // Like escape or a click outside, which the modal handles itself.
    wrapper.findComponent({ name: 'Modal' }).vm.$emit('hidden')
    await flushPromises()

    expect(wrapper.find('.details').exists()).toBe(false)
  })

  it('keeps the search shortcut from the page behind it while open', async () => {
    const wrapper = await mountAndShow()
    const { $priorityBus } = wrapper.vm
    const pageSearch = vi.fn()
    $priorityBus.$on('start-search', $priorityBus.level.LOW, pageSearch)
    const startSearch = () => {
      const event = { preventDefault: vi.fn() }
      $priorityBus.$emit('start-search', { event })
      return event
    }

    try {
      await wrapper.find('.list__recipe-book').trigger('click')
      expect(startSearch().preventDefault).toHaveBeenCalled()
      expect(pageSearch).not.toHaveBeenCalled()

      await wrapper.vm.hide()
      startSearch()
      expect(pageSearch).toHaveBeenCalledTimes(1)
    } finally {
      $priorityBus.$off('start-search', pageSearch)
    }
  })

  describe('tabs', () => {
    const tabs = (wrapper) => wrapper.findAll('.segment-control__button')
    const ownList = (wrapper) => wrapper.find('.own-list')

    const openOwnTab = async (wrapper) => {
      await tabs(wrapper)[1].trigger('click')
      await flushPromises()
    }

    it('are hidden for anonymous users', async () => {
      const wrapper = await mountAndShow()

      expect(tabs(wrapper)).toHaveLength(0)
      expect(ownList(wrapper).exists()).toBe(false)
    })

    it('are hidden while the feature flag is off', async () => {
      testApp.authenticate({ id: 1 })
      mocks = { $featureFlagIsEnabled: () => false }
      const wrapper = await mountAndShow()

      expect(tabs(wrapper)).toHaveLength(0)
    })

    it('switch between the official and the own templates', async () => {
      testApp.authenticate({ id: 1 })
      const wrapper = await mountAndShow()

      expect(tabs(wrapper).map((tab) => tab.text())).toStrictEqual([
        'templateModal.officialTemplates',
        'templateModal.yourTemplates',
      ])
      // The own templates are only loaded when their tab is opened.
      expect(ownList(wrapper).exists()).toBe(false)

      await openOwnTab(wrapper)

      expect(ownList(wrapper).isVisible()).toBe(true)
      expect(wrapper.find('.list').isVisible()).toBe(false)
      expect(
        wrapper.findComponent({ name: 'UserTemplateList' }).props('active')
      ).toBe(true)
      expect(
        wrapper.findComponent({ name: 'TemplateList' }).props('active')
      ).toBe(false)

      await tabs(wrapper)[0].trigger('click')

      expect(wrapper.find('.list').isVisible()).toBe(true)
      // Kept mounted, so that it doesn't load again.
      expect(ownList(wrapper).isVisible()).toBe(false)
    })

    it('open an own template with its categories and go back', async () => {
      testApp.authenticate({ id: 1 })
      const wrapper = await mountAndShow()
      await openOwnTab(wrapper)

      await wrapper.find('.own-list__sprint-tracker').trigger('click')

      expect(wrapper.find('.details').text()).toBe('Sprint Tracker: Agile')
      expect(ownList(wrapper).isVisible()).toBe(false)

      await wrapper.find('.details__back').trigger('click')

      expect(ownList(wrapper).isVisible()).toBe(true)
      expect(wrapper.find('.list').isVisible()).toBe(false)
    })

    it('create a template and list it', async () => {
      testApp.authenticate({ id: 1 })
      const wrapper = await mountAndShow()
      await openOwnTab(wrapper)
      const ownListComponent = () =>
        wrapper.findComponent({ name: 'UserTemplateList' })
      const createModal = wrapper.findComponent({
        name: 'CreateUserTemplateModal',
      })

      expect(createModal.props('categories')).toStrictEqual(categories)

      await wrapper.find('.own-list__create').trigger('click')

      expect(showCreateModal).toHaveBeenCalledTimes(1)
      // The create modal takes the search shortcut.
      expect(ownListComponent().props('active')).toBe(false)

      createModal.vm.$emit('created', { id: 9, template: 3 })
      createModal.vm.$emit('hidden')
      await flushPromises()

      expect(refreshList).toHaveBeenCalledTimes(1)
      expect(ownListComponent().props('active')).toBe(true)
    })

    it('start at the official templates when shown again', async () => {
      testApp.authenticate({ id: 1 })
      const wrapper = await mountAndShow()
      await openOwnTab(wrapper)

      await wrapper.vm.show()
      await flushPromises()

      expect(wrapper.find('.list').isVisible()).toBe(true)
      expect(ownList(wrapper).exists()).toBe(false)
    })
  })
})
