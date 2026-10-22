import { mountSuspended } from '@nuxt/test-utils/runtime'
import { nextTick, reactive, ref } from 'vue'
import PageHeader from '@baserow/modules/builder/components/page/header/PageHeader'
import AutomationHeader from '@baserow/modules/automation/components/AutomationHeader'

describe.each([
  ['builder', PageHeader],
  ['automation', AutomationHeader],
])('%s untrusted content header alert', (type, header) => {
  test('stays visible until content is trusted and returns when blocked again', async () => {
    const application = reactive({
      id: 1,
      type,
      workspace: { id: 1 },
      untrusted_content: true,
    })
    const wrapper = await mountSuspended(header, {
      props: type === 'automation' ? { automation: application } : {},
      global: {
        provide: {
          builder: application,
          workflow: ref({ id: 1, nodes: [] }),
          workspace: ref(application.workspace),
          isDev: false,
        },
        mocks: {
          $hasPermission: () => false,
          $store: { getters: { 'page/getDeviceTypeSelected': 'desktop' } },
        },
        stubs: {
          PageHeaderMenuItems: true,
          DeviceSelector: true,
          PageActions: true,
          WorkflowSettingsModal: true,
        },
      },
    })

    expect(wrapper.find('[role="alert"]').html()).toMatchSnapshot()
    expect(wrapper.find('.alert__close').exists()).toBe(false)

    application.untrusted_content = false
    await nextTick()
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)

    application.untrusted_content = true
    await nextTick()
    expect(wrapper.find('[role="alert"]').exists()).toBe(true)
    wrapper.unmount()
  })
})
