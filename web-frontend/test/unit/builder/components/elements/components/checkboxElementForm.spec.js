import CheckboxElementForm from '@baserow/modules/builder/components/elements/components/forms/general/CheckboxElementForm'

import { mountSuspended } from '@nuxt/test-utils/runtime'
import { h } from 'vue'

describe('CheckboxElementForm', () => {
  let wrapper

  const mountComponent = () =>
    mountSuspended(CheckboxElementForm, {
      props: {
        element: { id: 1, type: 'checkbox' },
        baseTheme: {},
        defaultValues: {
          label: { formula: 'Agree' },
          default_value: { formula: '' },
          required: false,
          styles: {},
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

  test('hints at the Markdown marker under the label and stores no format', () => {
    const hints = wrapper.findAll('.control__helper-text')
    expect(hints).toHaveLength(1)
    expect(hints[0].text()).toBe(useNuxtApp().$i18n.t('markdownMarker.hint'))
    expect(
      wrapper.find('.control__helper-text').element.closest('.control')
    ).toBe(wrapper.findAll('.control')[0].element)

    expect(wrapper.vm.allowedValues).toEqual([
      'label',
      'default_value',
      'required',
      'styles',
    ])
    expect(wrapper.findComponent({ name: 'RadioGroup' }).exists()).toBe(false)
  })
})
