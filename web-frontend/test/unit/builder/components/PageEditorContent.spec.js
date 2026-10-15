import { mountSuspended } from '@nuxt/test-utils/runtime'
import { nextTick, reactive } from 'vue'

import PageEditorContent from '@baserow/modules/builder/components/PageEditorContent'

describe('PageEditorContent', () => {
  test('waits for data sources before rendering the page preview', async () => {
    const page = reactive({
      id: 1,
      _: { dataSourceLoading: true },
      dataSources: [],
    })
    const sharedPage = {
      id: 2,
      shared: true,
      _: { dataSourceLoading: false },
      dataSources: [],
    }
    const builder = {
      id: 1,
      pages: [sharedPage, page],
      theme: {},
    }

    const wrapper = await mountSuspended(PageEditorContent, {
      props: {
        workspace: { id: 1 },
        builder,
        page,
        loading: false,
      },
      global: {
        stubs: {
          PageHeader: true,
          PagePreview: {
            inject: ['applicationContext'],
            template:
              '<div data-test-id="page-preview">{{ applicationContext.dataScope.includeTargetElement }}</div>',
          },
          PageSidePanels: true,
          SkeletonBlock: true,
        },
      },
    })

    expect(wrapper.find('[data-test-id="page-preview"]').exists()).toBe(false)

    page._.dataSourceLoading = false
    await nextTick()

    expect(wrapper.find('[data-test-id="page-preview"]').exists()).toBe(true)
    expect(wrapper.find('[data-test-id="page-preview"]').text()).toBe('false')
    wrapper.unmount()
  })
})
