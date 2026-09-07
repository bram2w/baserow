import { mountSuspended } from '@nuxt/test-utils/runtime'
import InputTextElement from '@baserow/modules/builder/components/elements/components/InputTextElement.vue'

describe('InputTextElement', () => {
  let store = null

  beforeEach(() => {
    store = useNuxtApp().$store
  })

  const mountComponent = ({ props = {}, provide = {} }) => {
    return mountSuspended(InputTextElement, {
      props,
      global: { provide },
    })
  }

  const mountNumericInput = async (defaultValue) => {
    const page = { id: 1, elements: [] }
    const builder = { id: 1, theme: { primary_color: '#ccc' }, pages: [page] }
    const workspace = {}
    const mode = 'public'
    const element = {
      id: 42,
      type: 'input_text',
      validation_type: 'integer',
      default_value: { formula: defaultValue },
      label: { formula: '' },
      placeholder: { formula: '' },
      required: false,
      is_multiline: false,
      rows: 1,
      input_type: 'number',
      page_id: page.id,
      styles: {},
    }

    store.dispatch('element/forceCreate', { page, element })

    return mountComponent({
      props: { element },
      provide: {
        builder,
        currentPage: page,
        elementPage: page,
        mode,
        applicationContext: { builder, page, mode },
        element,
        workspace,
      },
    })
  }

  test.each([
    ['0', '0'],
    ['', ''],
  ])(
    'renders numeric default value %p as %p',
    async (defaultValue, expected) => {
      const wrapper = await mountNumericInput(defaultValue)

      expect(wrapper.find('input').element.value).toBe(expected)
    }
  )
})

describe('InputTextElement label', () => {
  let store = null

  beforeEach(() => {
    store = useNuxtApp().$store
  })

  const mountWithLabel = async (label, pageParameters = {}) => {
    const page = { id: 1, elements: [] }
    const builder = { id: 1, theme: { primary_color: '#ccc' }, pages: [page] }
    const workspace = {}
    const mode = 'public'
    const element = {
      id: 43,
      type: 'input_text',
      validation_type: 'any',
      default_value: { formula: '' },
      label,
      placeholder: { formula: '' },
      required: false,
      is_multiline: false,
      rows: 1,
      input_type: 'text',
      page_id: page.id,
      styles: {},
    }

    store.dispatch('element/forceCreate', { page, element })
    for (const [name, value] of Object.entries(pageParameters)) {
      await store.dispatch('pageParameter/setParameter', { page, name, value })
    }

    return mountSuspended(InputTextElement, {
      props: { element },
      global: {
        provide: {
          builder,
          currentPage: page,
          elementPage: page,
          mode,
          applicationContext: { builder, page, mode },
          element,
          workspace,
        },
      },
    })
  }

  test('renders the raw label by default', async () => {
    const wrapper = await mountWithLabel({
      mode: 'raw',
      formula: 'Your **name** ([why?](/why))',
    })

    const label = wrapper.find('.ab-form-group__label')
    expect(label.find('strong').exists()).toBe(false)
    expect(label.text()).toBe('Your **name** ([why?](/why))')
  })

  test('renders a marked literal label as Markdown with links', async () => {
    const wrapper = await mountWithLabel({
      mode: 'raw',
      formula: '__markdown__Your **name** ([why?](/why))',
    })

    const label = wrapper.find('.ab-form-group__label')
    expect(label.find('strong').text()).toBe('name')
    expect(label.find('a.ab-link').attributes('href')).toBe('/why')
    expect(label.text()).not.toContain('__markdown__')
  })

  test('renders a marked data-fed label as Markdown', async () => {
    const wrapper = await mountWithLabel(
      {
        mode: 'simple',
        formula: "concat('__markdown__', get('page_parameter.label'))",
      },
      { label: 'Your **name**' }
    )

    const label = wrapper.find('.ab-form-group__label')
    expect(label.find('strong').text()).toBe('name')
    expect(label.text()).toBe('Your name')
  })

  // Pinned on purpose: the marker is detected on the resolved text, so a data
  // value decides the rendering of a surface whose formula has no marker.
  test('a data value starting with the marker renders as Markdown', async () => {
    const wrapper = await mountWithLabel(
      { mode: 'simple', formula: "get('page_parameter.label')" },
      { label: '__markdown__Your **name**' }
    )

    const label = wrapper.find('.ab-form-group__label')
    expect(label.find('strong').text()).toBe('name')
    expect(label.text()).toBe('Your name')
  })

  test('a data value with the marker mid-string stays plain', async () => {
    const wrapper = await mountWithLabel(
      { mode: 'simple', formula: "get('page_parameter.label')" },
      { label: 'Your __markdown__**name**' }
    )

    const label = wrapper.find('.ab-form-group__label')
    expect(label.find('strong').exists()).toBe(false)
    expect(label.text()).toBe('Your __markdown__**name**')
  })
})
