import { mountSuspended } from '@nuxt/test-utils/runtime'
import TextElement from '@baserow/modules/builder/components/elements/components/TextElement.vue'

describe('TextElement', () => {
  const mountText = (element) => {
    const page = {}
    const builder = { id: 1, theme: {} }
    const mode = 'public'

    return mountSuspended(TextElement, {
      props: { element: { id: 1, type: 'text', styles: {}, ...element } },
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
  }

  test('renders Markdown with the Application Builder rules', async () => {
    const wrapper = await mountText({
      value: { mode: 'raw', formula: '# Heading\n\n`inline code`' },
      format: 'markdown',
    })

    expect(wrapper.find('.ab-heading').text()).toBe('Heading')
    expect(wrapper.find('.ab-code--inline').text()).toBe('inline code')
  })

  test('renders plain text as paragraphs', async () => {
    const wrapper = await mountText({
      value: { mode: 'raw', formula: '# Heading\n\n`inline code`' },
      format: 'plain',
    })

    expect(wrapper.find('.ab-heading').exists()).toBe(false)
    expect(wrapper.findAll('p')).toHaveLength(2)
    expect(wrapper.text()).toContain('# Heading')
  })

  // The Text element keeps its own format setting, and follows the marker
  // rule of every other text surface on top of it. Pinned on purpose.
  test('renders a plain-format element as Markdown when its value starts with the marker', async () => {
    const wrapper = await mountText({
      value: { mode: 'raw', formula: '__markdown__# Heading\n\n`inline code`' },
      format: 'plain',
    })

    expect(wrapper.find('.ab-heading').text()).toBe('Heading')
    expect(wrapper.find('.ab-code--inline').text()).toBe('inline code')
    expect(wrapper.text()).not.toContain('__markdown__')
  })

  test('strips the marker from a markdown-format element too', async () => {
    const wrapper = await mountText({
      value: { mode: 'raw', formula: '__markdown__# Heading' },
      format: 'markdown',
    })

    expect(wrapper.find('.ab-heading').text()).toBe('Heading')
    expect(wrapper.text()).not.toContain('__markdown__')
  })

  test('keeps a marker elsewhere in a plain-format element as text', async () => {
    const wrapper = await mountText({
      value: { mode: 'raw', formula: 'See __markdown__# Heading' },
      format: 'plain',
    })

    expect(wrapper.find('.ab-heading').exists()).toBe(false)
    expect(wrapper.text()).toContain('See __markdown__# Heading')
  })
})
