import { MARKDOWN_PREFIX } from '@baserow/modules/core/formula/textFormat'
import CheckboxElementForm from '@baserow/modules/builder/components/elements/components/forms/general/CheckboxElementForm'

import { mountSuspended } from '@nuxt/test-utils/runtime'
import { h } from 'vue'

describe('CheckboxElementForm', () => {
  let wrapper

  const defaultProps = {
    element: { id: 1, type: 'table', fields: [] },
    baseTheme: {},
    defaultValues: {
      label: { formula: 'Agree' },
      default_value: { formula: '' },
      required: false,
      styles: {},
      // Add some non-allowed properties
      someOtherProp: 'should not be included',
      anotherProp: 123,
    },
  }

  const mountComponent = (props = {}) => {
    return mountSuspended(CheckboxElementForm, {
      props: {
        ...defaultProps,
        ...props,
      },
      mocks: {
        $t: (key) => key,
        $registry: {
          getOrderedList: () => [],
        },
      },
      global: {
        provide: {
          workspace: {},
          builder: {
            theme: {},
          },
          currentPage: {},
          elementPage: {},
          mode: 'edit',
          formulaComponent: () => h('div', `fake formula component`),
          dataProvidersAllowed: [],
          openCustomStyleForm: vi.fn(),
        },
      },
      stubs: {
        FormGroup: true,
        RadioGroup: true,
        InjectedFormulaInput: true,
        CustomStyle: true,
      },
    })
  }

  beforeEach(async () => {
    wrapper = await mountComponent()
  })

  afterEach(() => {
    wrapper.unmount()
  })

  test('writes the label format into the label formula', async () => {
    expect(wrapper.vm.allowedValues).toEqual([
      'label',
      'default_value',
      'required',
      'styles',
    ])
    const formatSelector = wrapper.findComponent({ name: 'TextFormatSelector' })
    expect(formatSelector.props('modelValue')).toBe('plain')

    await formatSelector.vm.$emit('update:modelValue', 'markdown')

    const emittedValues = wrapper.emitted('values-changed')
    expect(emittedValues).toBeTruthy()
    const lastEmittedValues = emittedValues[emittedValues.length - 1][0]

    expect(lastEmittedValues).toEqual({
      label: { formula: `${MARKDOWN_PREFIX}Agree` },
      default_value: { formula: '' },
      required: false,
      styles: {},
    })
    expect(formatSelector.props('modelValue')).toBe('markdown')

    await formatSelector.vm.$emit('update:modelValue', 'plain')

    expect(wrapper.vm.values.label).toEqual({ formula: 'Agree' })
    expect(lastEmittedValues.someOtherProp).toBeUndefined()
    expect(lastEmittedValues.anotherProp).toBeUndefined()
  })
})
