import { mountSuspended } from '@nuxt/test-utils/runtime'
import TableElement from '@baserow/modules/builder/components/elements/components/TableElement.vue'
import { MARKDOWN_PREFIX } from '@baserow/modules/core/formula/textFormat'

describe('TableElement', () => {
  let store = null

  beforeEach(() => {
    store = useNuxtApp().$store
  })

  const mountTable = async (fields) => {
    const page = { id: 1, elements: [], dataSources: [] }
    const sharedPage = { id: 2, shared: true, elements: [], dataSources: [] }
    const builder = {
      id: 1,
      theme: { primary_color: '#ccc' },
      pages: [page, sharedPage],
      integrations: [],
    }
    const mode = 'public'
    const element = {
      id: 45,
      type: 'table',
      data_source_id: null,
      schema_property: null,
      items_per_page: 5,
      button_load_more_label: { formula: '' },
      orientation: {
        desktop: 'horizontal',
        tablet: 'horizontal',
        smartphone: 'horizontal',
      },
      fields: fields.map((field, index) => ({
        id: index + 1,
        uid: `uid-${index + 1}`,
        type: 'text',
        value: { formula: '' },
        styles: {},
        ...field,
      })),
      page_id: page.id,
      styles: {},
    }

    store.dispatch('element/forceCreate', { page, element })

    return mountSuspended(TableElement, {
      // Like `ElementPreview`/`PageElement`, the page reaches the collection
      // element through the application context additions.
      props: {
        element,
        applicationContextAdditions: { recordIndexPath: [], page },
      },
      global: {
        provide: {
          builder,
          currentPage: page,
          elementPage: page,
          mode,
          applicationContext: { builder, page, mode, element },
          element,
          workspace: {},
        },
      },
    })
  }

  test('renders column headers as inline Markdown only when the name is marked', async () => {
    const wrapper = await mountTable([
      { name: `${MARKDOWN_PREFIX}**Bold** ([docs](https://example.com))` },
      { name: '**Plain**' },
    ])

    const [markdown, plain] = wrapper.findAll('th')
    expect(markdown.find('strong').text()).toBe('Bold')
    expect(markdown.find('a').exists()).toBe(false)
    expect(markdown.text()).toBe('Bold ([docs](https://example.com))')
    expect(plain.find('strong').exists()).toBe(false)
    expect(plain.text()).toBe('**Plain**')
  })
})
