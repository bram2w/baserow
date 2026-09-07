import TextFieldForm from '@baserow/modules/builder/components/elements/components/collectionField/form/TextFieldForm'

import { mountSuspended } from '@nuxt/test-utils/runtime'
import { h } from 'vue'

describe('TextFieldForm', () => {
  let wrapper

  const mountComponent = () =>
    mountSuspended(TextFieldForm, {
      props: {
        element: { id: 1, type: 'table', fields: [] },
        baseTheme: {},
        defaultValues: {
          value: { formula: 'test text' },
          styles: {},
          // Add some non-allowed properties
          someOtherProp: 'should not be included',
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
          openCustomStyleForm: vi.fn(),
        },
        stubs: { InjectedFormulaInput: true, CustomStyleButton: true },
      },
    })

  beforeEach(async () => {
    wrapper = await mountComponent()
  })

  afterEach(() => {
    wrapper.unmount()
  })

  test('hints at the Markdown marker under the value and stores no format', async () => {
    const hints = wrapper.findAll('.control__helper-text')
    expect(hints).toHaveLength(1)
    expect(hints[0].text()).toBe(useNuxtApp().$i18n.t('markdownMarker.hint'))
    expect(wrapper.vm.allowedValues).toEqual(['value', 'styles'])

    await wrapper.setData({ values: { styles: { color: 'red' } } })

    const emittedValues = wrapper.emitted('values-changed')
    expect(emittedValues).toBeTruthy()
    expect(emittedValues[emittedValues.length - 1][0]).toEqual({
      value: { formula: 'test text' },
      styles: { color: 'red' },
    })
  })
})
