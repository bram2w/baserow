import { mountSuspended } from '@nuxt/test-utils/runtime'
import TextField from '@baserow/modules/builder/components/elements/components/collectionField/TextField.vue'

describe('TextField', () => {
  const page = {}
  const builder = { id: 1, theme: {} }
  const mode = 'public'
  const element = { id: 1, type: 'table', fields: [], styles: {} }
  const field = { id: 1, uid: 'abc', name: 'Field', type: 'text', styles: {} }
  const value = '# Heading\n\n`inline code`'

  const mountComponent = (props = {}) =>
    mountSuspended(TextField, {
      props: { element, field, value, ...props },
      global: {
        provide: {
          workspace: {},
          builder,
          currentPage: page,
          elementPage: page,
          mode,
          applicationContext: { builder, page, mode },
        },
      },
    })

  test('renders a marked value as Markdown with the Application Builder rules', async () => {
    const wrapper = await mountComponent({ value: `__markdown__${value}` })

    expect(wrapper.find('.ab-heading').text()).toBe('Heading')
    expect(wrapper.find('.ab-code--inline').text()).toBe('inline code')
    expect(wrapper.find('span.ab-text').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('__markdown__')
  })

  test('renders the raw text in the text span without the marker', async () => {
    const wrapper = await mountComponent()

    const spans = wrapper.findAll('span.ab-text')
    expect(spans).toHaveLength(1)
    expect(spans[0].text()).toBe(value)
    expect(wrapper.find('.ab-heading').exists()).toBe(false)
    expect(wrapper.find('.markdown').exists()).toBe(false)
  })

  test('keeps a marker elsewhere in the value as text', async () => {
    const wrapper = await mountComponent({ value: 'See __markdown__**x**' })

    expect(wrapper.find('span.ab-text').text()).toBe('See __markdown__**x**')
    expect(wrapper.find('strong').exists()).toBe(false)
  })
})
