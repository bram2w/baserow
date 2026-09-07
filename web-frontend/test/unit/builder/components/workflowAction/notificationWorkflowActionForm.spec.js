import NotificationWorkflowActionForm from '@baserow/modules/builder/components/workflowAction/NotificationWorkflowActionForm'

import { mountSuspended } from '@nuxt/test-utils/runtime'
import { h } from 'vue'

describe('NotificationWorkflowActionForm', () => {
  let wrapper

  const mountComponent = () =>
    mountSuspended(NotificationWorkflowActionForm, {
      props: {
        defaultValues: {
          title: { formula: 'Saved' },
          description: { formula: 'Done' },
        },
      },
      global: {
        provide: {
          workspace: {},
          builder: { theme: {} },
          currentPage: {},
          elementPage: {},
          mode: 'edit',
          formulaComponent: () => h('div', `fake formula component`),
          dataProvidersAllowed: [],
        },
        stubs: { InjectedFormulaInput: true },
      },
    })

  beforeEach(async () => {
    wrapper = await mountComponent()
  })

  afterEach(() => {
    wrapper.unmount()
  })

  test('hints at the Markdown marker under the title and the description and stores no format', () => {
    const hints = wrapper.findAll('.control__helper-text')
    expect(hints).toHaveLength(2)
    hints.forEach((hint) =>
      expect(hint.text()).toBe(useNuxtApp().$i18n.t('markdownMarker.hint'))
    )
    expect(Object.keys(wrapper.vm.values)).toEqual(['title', 'description'])
    expect(wrapper.findComponent({ name: 'RadioGroup' }).exists()).toBe(false)
  })
})
